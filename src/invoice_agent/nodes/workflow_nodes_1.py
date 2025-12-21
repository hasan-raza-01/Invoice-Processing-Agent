"""LangGraph workflow nodes for invoice processing"""
import sys
from datetime import datetime, timezone
from typing import Dict, Any
import uuid

from invoice_agent.models.state_models import WorkflowState
from invoice_agent.utils.logger import logger
from invoice_agent.utils.exceptions import InvoiceAgentException
from invoice_agent.bigtool.bigtool_picker import BigtoolPicker
from invoice_agent.mcp.common_client import CommonClient
from invoice_agent.mcp.atlas_client import AtlasClient
from invoice_agent.database.checkpoint_store import CheckpointStore
from invoice_agent.models.invoice_models import InvoicePayload

# Initialize clients
bigtool = BigtoolPicker()
common_client = CommonClient()
atlas_client = AtlasClient()


def intake_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 1: INTAKE - Accept and validate invoice payload
    """
    logger.info("=" * 60)
    logger.info("Stage 1: INTAKE - Validating and persisting invoice")
    logger.info("=" * 60)
    
    try:
        # Validate payload
        invoice_data = state["invoice_payload"]
        invoice = InvoicePayload(**invoice_data)
        
        # Select storage tool
        storage_tool = bigtool.select("storage")
        
        # Persist raw invoice
        raw_id = storage_tool.execute(data=invoice_data) if storage_tool else str(uuid.uuid4())
        ingest_ts = datetime.now(timezone.utc).isoformat()
        
        # Update state
        state["raw_id"] = raw_id
        state["ingest_ts"] = ingest_ts
        state["validated"] = True
        state["current_stage"] = "INTAKE"
        state["logs"].append(f"[INTAKE] Invoice validated and stored: {raw_id}")
        
        logger.info(f"[OK] Invoice ingested successfully - ID: {raw_id}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] INTAKE failed: {e}")
        raise InvoiceAgentException(f"INTAKE stage failed: {e}", sys)


def understand_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 2: UNDERSTAND - OCR extraction and line item parsing
    """
    logger.info("=" * 60)
    logger.info("Stage 2: UNDERSTAND - OCR and parsing")
    logger.info("=" * 60)
    
    try:
        # Select OCR tool
        ocr_tool = bigtool.select("ocr")
        
        # Extract text from attachments
        attachments = state["invoice_payload"].get("attachments", [])
        ocr_text = []
        
        for attachment in attachments[:1]:  # Process first attachment
            if ocr_tool:
                text = ocr_tool.execute(image_path=attachment)
                ocr_text.append(text)
        
        # Parse line items (using existing data + OCR enrichment)
        line_items = state["invoice_payload"].get("line_items", [])
        
        # Extract PO references from OCR text
        detected_pos = []
        for text in ocr_text:
            if "PO-" in text or "P.O." in text:
                # Simple PO extraction
                for word in text.split():
                    if word.startswith("PO-") or word.startswith("P.O."):
                        detected_pos.append(word.replace("P.O.", "PO-"))
        
        if not detected_pos:
            detected_pos = ["PO-001"]  # Default PO reference
        
        # Update state
        state["parsed_invoice"] = {
            "invoice_text": " ".join(ocr_text) if ocr_text else "No OCR text",
            "parsed_line_items": line_items,
            "detected_pos": detected_pos,
            "currency": state["invoice_payload"].get("currency", "USD"),
            "parsed_dates": {
                "invoice_date": state["invoice_payload"].get("invoice_date"),
                "due_date": state["invoice_payload"].get("due_date")
            }
        }
        state["current_stage"] = "UNDERSTAND"
        state["logs"].append(f"[UNDERSTAND] OCR completed, detected POs: {detected_pos}")
        
        logger.info(f"[OK] OCR and parsing completed - POs found: {detected_pos}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] UNDERSTAND failed: {e}")
        raise InvoiceAgentException(f"UNDERSTAND stage failed: {e}", sys)


def prepare_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 3: PREPARE - Normalize vendor, enrich, compute flags
    """
    logger.info("=" * 60)
    logger.info("Stage 3: PREPARE - Vendor normalization and enrichment")
    logger.info("=" * 60)
    
    try:
        vendor_name = state["invoice_payload"]["vendor_name"]
        vendor_tax_id = state["invoice_payload"]["vendor_tax_id"]
        
        # Normalize vendor name (COMMON)
        normalized_name = common_client.normalize_vendor(vendor_name)
        
        # Select enrichment tool and enrich (ATLAS)
        enrichment_tool = bigtool.select("enrichment")
        enrichment_meta = atlas_client.enrich_vendor(
            normalized_name,
            vendor_tax_id,
            enrichment_tool
        )
        
        # Compute flags (COMMON)
        vendor_profile = {
            "normalized_name": normalized_name,
            "tax_id": vendor_tax_id,
            "enrichment_meta": enrichment_meta
        }
        
        flags = common_client.compute_flags(vendor_profile, state["invoice_payload"])
        
        # Update state
        state["vendor_profile"] = vendor_profile
        state["normalized_invoice"] = {
            "amount": state["invoice_payload"]["amount"],
            "currency": state["invoice_payload"]["currency"],
            "line_items": state["invoice_payload"]["line_items"]
        }
        state["flags"] = flags
        state["current_stage"] = "PREPARE"
        state["logs"].append(f"[PREPARE] Vendor normalized: {normalized_name}, Risk Score: {flags['risk_score']}")
        
        logger.info(f"[OK] Vendor prepared - Risk Score: {flags['risk_score']}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] PREPARE failed: {e}")
        raise InvoiceAgentException(f"PREPARE stage failed: {e}", sys)


def retrieve_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 4: RETRIEVE - Fetch POs, GRNs, history from ERP
    """
    logger.info("=" * 60)
    logger.info("Stage 4: RETRIEVE - Fetching ERP data")
    logger.info("=" * 60)
    
    try:
        # Select ERP connector
        erp_tool = bigtool.select("erp_connector")
        
        # Fetch POs (ATLAS)
        po_references = state["parsed_invoice"]["detected_pos"]
        matched_pos = atlas_client.fetch_pos(po_references, erp_tool)
        
        # Fetch GRNs (ATLAS)
        po_ids = [po["po_id"] for po in matched_pos]
        matched_grns = atlas_client.fetch_grns(po_ids, erp_tool)
        
        # Fetch historical invoices (ATLAS)
        vendor_id = state["vendor_profile"]["tax_id"]
        history = atlas_client.fetch_invoice_history(vendor_id, erp_tool)
        
        # Update state
        state["matched_pos"] = matched_pos
        state["matched_grns"] = matched_grns
        state["history"] = history
        state["current_stage"] = "RETRIEVE"
        state["logs"].append(f"[RETRIEVE] Fetched {len(matched_pos)} POs, {len(matched_grns)} GRNs")
        
        logger.info(f"[OK] ERP data retrieved - POs: {len(matched_pos)}, GRNs: {len(matched_grns)}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] RETRIEVE failed: {e}")
        raise InvoiceAgentException(f"RETRIEVE stage failed: {e}", sys)


def match_two_way_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 5: MATCH_TWO_WAY - Compute 2-way match score
    """
    logger.info("=" * 60)
    logger.info("Stage 5: MATCH_TWO_WAY - Computing match score")
    logger.info("=" * 60)
    
    try:
        # Get config threshold
        match_threshold = 0.90
        tolerance_pct = 5.0
        
        # Compute match (COMMON)
        invoice_line_items = state["normalized_invoice"]["line_items"]
        po_line_items = state["matched_pos"][0]["line_items"] if state["matched_pos"] else []
        
        match_result_data = common_client.compute_two_way_match(
            invoice_line_items,
            po_line_items,
            tolerance_pct
        )
        
        # Determine match result
        match_score = match_result_data["score"]
        match_result = "MATCHED" if match_score >= match_threshold else "FAILED"
        
        # Update state
        state["match_score"] = match_score
        state["match_result"] = match_result
        state["tolerance_pct"] = match_result_data["tolerance_pct"]
        state["match_evidence"] = match_result_data["evidence"]
        state["current_stage"] = "MATCH_TWO_WAY"
        state["logs"].append(f"[MATCH_TWO_WAY] Score: {match_score:.2f}, Result: {match_result}")
        
        logger.info(f"[OK] 2-way match completed - Score: {match_score:.2f}, Result: {match_result}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] MATCH_TWO_WAY failed: {e}")
        raise InvoiceAgentException(f"MATCH_TWO_WAY stage failed: {e}", sys)
