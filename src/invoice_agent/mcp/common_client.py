"""Mock COMMON MCP Client for abilities requiring no external data"""
from typing import Dict, Any, List
from invoice_agent.utils.logger import logger


class CommonClient:
    """Mock COMMON server client for deterministic operations"""
    
    def __init__(self, base_url: str = "http://localhost:8001", api_key: str = "mock-key"):
        self.base_url = base_url
        self.api_key = api_key
        logger.info(f"CommonClient initialized (Mock Mode): {base_url}")
    
    def normalize_vendor(self, vendor_name: str) -> str:
        """
        Normalize vendor name
        
        Args:
            vendor_name: Raw vendor name
            
        Returns:
            Normalized vendor name
        """
        normalized = vendor_name.strip().upper().replace("  ", " ")
        logger.info(f"COMMON: Normalized vendor '{vendor_name}' -> '{normalized}'")
        return normalized
    
    def compute_flags(self, vendor_profile: Dict[str, Any], invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute validation flags
        
        Args:
            vendor_profile: Vendor profile data
            invoice: Invoice data
            
        Returns:
            Flags dictionary
        """
        missing_info = []
        risk_score = 0.0
        
        # Check for missing information
        if not vendor_profile.get("tax_id"):
            missing_info.append("tax_id")
            risk_score += 0.2
        
        if not invoice.get("attachments"):
            missing_info.append("attachments")
            risk_score += 0.1
        
        # Check amount threshold
        if invoice.get("amount", 0) > 10000:
            risk_score += 0.3
        
        flags = {
            "missing_info": missing_info,
            "risk_score": min(risk_score, 1.0)
        }
        
        logger.info(f"COMMON: Computed flags - Risk Score: {flags['risk_score']}")
        return flags
    
    def compute_two_way_match(
        self,
        invoice_line_items: List[Dict[str, Any]],
        po_line_items: List[Dict[str, Any]],
        tolerance_pct: float
    ) -> Dict[str, Any]:
        """
        Compute 2-way match score between invoice and PO
        
        Args:
            invoice_line_items: Invoice line items
            po_line_items: PO line items
            tolerance_pct: Tolerance percentage
            
        Returns:
            Match result with score and evidence
        """
        # Simple matching logic: compare totals
        invoice_total = sum(item.get("total", 0) for item in invoice_line_items)
        po_total = sum(item.get("total", 0) for item in po_line_items)
        
        difference = abs(invoice_total - po_total)
        difference_pct = (difference / po_total * 100) if po_total > 0 else 100
        
        # Calculate match score
        if difference_pct <= tolerance_pct:
            match_score = 1.0 - (difference_pct / tolerance_pct) * 0.1
        else:
            match_score = max(0.0, 0.9 - (difference_pct / 100))
        
        result = {
            "score": round(match_score, 2),
            "tolerance_pct": difference_pct,
            "evidence": {
                "invoice_total": invoice_total,
                "po_total": po_total,
                "difference": difference,
                "difference_pct": difference_pct
            }
        }
        
        logger.info(f"COMMON: 2-way match score: {result['score']} (diff: {difference_pct:.2f}%)")
        return result
