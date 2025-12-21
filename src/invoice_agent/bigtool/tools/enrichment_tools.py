"""Vendor enrichment tools"""
from invoice_agent.bigtool.bigtool_picker import BaseTool
from typing import Dict, Any
import random


class VendorDBEnrichment(BaseTool):
    """Mock vendor database enrichment"""
    name = "vendor_db"
    capability = "enrichment"
    
    def execute(self, vendor_name: str, tax_id: str, **kwargs) -> Dict[str, Any]:
        """
        Enrich vendor data from database
        
        Args:
            vendor_name: Vendor name
            tax_id: Tax ID
            
        Returns:
            Enrichment data
        """
        return {
            "pan": tax_id,
            "gst": f"GST{tax_id[:10]}",
            "credit_score": random.randint(650, 850),
            "risk_rating": random.choice(["LOW", "MEDIUM"]),
            "address": f"{random.randint(1, 999)} Business Street, City",
            "contact": f"+1-555-{random.randint(1000, 9999)}",
            "industry": "Manufacturing",
            "years_in_business": random.randint(5, 25)
        }
