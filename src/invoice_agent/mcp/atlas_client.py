"""Mock ATLAS MCP Client for external system interactions"""
from typing import Dict, Any, List
from invoice_agent.utils.logger import logger
import random


class AtlasClient:
    """Mock ATLAS server client for external integrations"""
    
    def __init__(self, base_url: str = "http://localhost:8002", api_key: str = "mock-key"):
        self.base_url = base_url
        self.api_key = api_key
        logger.info(f"AtlasClient initialized (Mock Mode): {base_url}")
    
    def enrich_vendor(
        self,
        vendor_name: str,
        tax_id: str,
        tool: Any = None
    ) -> Dict[str, Any]:
        """
        Enrich vendor data with external information
        
        Args:
            vendor_name: Vendor name
            tax_id: Tax ID
            tool: Enrichment tool (from Bigtool)
            
        Returns:
            Enrichment metadata
        """
        enrichment = {
            "pan": tax_id,
            "gst": f"GST{tax_id[:10]}",
            "credit_score": random.randint(600, 850),
            "risk_rating": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "business_type": "B2B",
            "years_in_business": random.randint(1, 20),
            "enrichment_source": tool.name if tool else "vendor_db"
        }
        
        logger.info(f"ATLAS: Enriched vendor '{vendor_name}' - Credit Score: {enrichment['credit_score']}")
        return enrichment
    
    def fetch_pos(
        self,
        po_references: List[str],
        erp_tool: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch Purchase Orders from ERP
        
        Args:
            po_references: PO reference numbers
            erp_tool: ERP connector tool
            
        Returns:
            List of PO data
        """
        pos = []
        for po_ref in po_references:
            # Match amounts based on PO number for testing
            if po_ref == "PO-12345":
                # This should match invoice_001_perfect_match.json (amount: 5000.0)
                po = {
                    "po_id": po_ref,
                    "vendor": "ACME CORPORATION",
                    "amount": 5000.0,  # Matches invoice_001
                    "status": "OPEN",
                    "line_items": [
                        {
                            "desc": "Industrial Widget Model X-2000",
                            "qty": 10,
                            "unit_price": 500.0,
                            "total": 5000.0
                        }
                    ]
                }
            else:
                # Default PO for other scenarios
                po = {
                    "po_id": po_ref,
                    "vendor": "ACME CORPORATION",
                    "amount": round(random.uniform(1000, 10000), 2),
                    "status": "OPEN",
                    "line_items": [
                        {
                            "desc": "Product A",
                            "qty": 10,
                            "unit_price": 100.0,
                            "total": 1000.0
                        },
                        {
                            "desc": "Product B",
                            "qty": 5,
                            "unit_price": 200.0,
                            "total": 1000.0
                        }
                    ]
                }
            pos.append(po)
        
        logger.info(f"ATLAS: Fetched {len(pos)} POs from ERP")
        return pos
    
    def fetch_grns(
        self,
        po_ids: List[str],
        erp_tool: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch Goods Received Notes
        
        Args:
            po_ids: PO identifiers
            erp_tool: ERP connector tool
            
        Returns:
            List of GRN data
        """
        grns = []
        for po_id in po_ids:
            grn = {
                "grn_id": f"GRN-{po_id[-3:]}",
                "po_id": po_id,
                "received_qty": random.randint(1, 100),
                "status": "RECEIVED",
                "received_date": "2024-01-15"
            }
            grns.append(grn)
        
        logger.info(f"ATLAS: Fetched {len(grns)} GRNs")
        return grns
    
    def fetch_invoice_history(
        self,
        vendor_id: str,
        erp_tool: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical invoices for vendor
        
        Args:
            vendor_id: Vendor identifier
            erp_tool: ERP connector tool
            
        Returns:
            List of historical invoices
        """
        history = [
            {
                "invoice_id": f"INV-{i:03d}",
                "amount": round(random.uniform(1000, 5000), 2),
                "status": random.choice(["PAID", "PENDING"]),
                "date": "2024-01-01"
            }
            for i in range(3)
        ]
        
        logger.info(f"ATLAS: Fetched {len(history)} historical invoices")
        return history
    
    def post_to_erp(
        self,
        entries: List[Dict[str, Any]],
        erp_tool: Any = None
    ) -> Dict[str, Any]:
        """
        Post accounting entries to ERP
        
        Args:
            entries: Accounting entries
            erp_tool: ERP connector tool
            
        Returns:
            Posting result
        """
        txn_id = f"TXN-{random.randint(10000, 99999)}"
        
        result = {
            "posted": True,
            "erp_txn_id": txn_id,
            "status": "SUCCESS"
        }
        
        logger.info(f"ATLAS: Posted to ERP - Transaction ID: {txn_id}")
        return result
    
    def schedule_payment(
        self,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Schedule payment
        
        Args:
            payment_data: Payment details
            
        Returns:
            Scheduled payment info
        """
        payment_id = f"PAY-{random.randint(10000, 99999)}"
        
        result = {
            "scheduled_payment_id": payment_id,
            "scheduled_date": "2024-02-01",
            "status": "SCHEDULED"
        }
        
        logger.info(f"ATLAS: Payment scheduled - ID: {payment_id}")
        return result
    
    def send_notification(
        self,
        recipient: str,
        message: str,
        email_tool: Any = None
    ) -> Dict[str, Any]:
        """
        Send notification
        
        Args:
            recipient: Recipient email/identifier
            message: Message content
            email_tool: Email tool from Bigtool
            
        Returns:
            Notification status
        """
        result = {
            "sent": True,
            "recipient": recipient,
            "message_id": f"MSG-{random.randint(1000, 9999)}",
            "tool_used": email_tool.name if email_tool else "mock_email"
        }
        
        logger.info(f"ATLAS: Notification sent to {recipient}")
        return result
