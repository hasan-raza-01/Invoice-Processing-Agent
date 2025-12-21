"""ERP connector tools"""
from invoice_agent.bigtool.bigtool_picker import BaseTool
from typing import List, Dict, Any
import random


class MockERPConnector(BaseTool):
    """Mock ERP system connector"""
    name = "mock_erp"
    capability = "erp_connector"
    
    def fetch_pos(self, po_references: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Fetch Purchase Orders"""
        pos = []
        for po_ref in po_references:
            pos.append({
                "po_id": po_ref,
                "vendor": "ACME CORPORATION",
                "amount": 2000.00,
                "line_items": [
                    {"desc": "Product A", "qty": 10, "unit_price": 100.0, "total": 1000.0},
                    {"desc": "Product B", "qty": 5, "unit_price": 200.0, "total": 1000.0}
                ],
                "status": "OPEN"
            })
        return pos
    
    def fetch_grns(self, po_ids: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Fetch Goods Received Notes"""
        grns = []
        for po_id in po_ids:
            grns.append({
                "grn_id": f"GRN-{po_id[-3:]}",
                "po_id": po_id,
                "received_qty": 15,
                "status": "RECEIVED"
            })
        return grns
    
    def post_entries(self, entries: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Post accounting entries to ERP"""
        return {
            "posted": True,
            "erp_txn_id": f"TXN-{random.randint(10000, 99999)}",
            "status": "SUCCESS"
        }
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute ERP action"""
        if action == "fetch_pos":
            return self.fetch_pos(kwargs.get("po_references", []))
        elif action == "fetch_grns":
            return self.fetch_grns(kwargs.get("po_ids", []))
        elif action == "post":
            return self.post_entries(kwargs.get("entries", []))
        return {}
