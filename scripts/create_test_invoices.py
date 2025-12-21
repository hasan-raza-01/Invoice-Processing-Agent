"""
Script to create all comprehensive test invoice HTML files and JSON payloads
"""
from pathlib import Path

# Define invoice data
INVOICES = {
    # Invoice 2: Amount Mismatch (HITL trigger)
    "002_amount_mismatch": {
        "json": {
            "invoice_id": "INV-2025-002",
            "vendor_name": "Beta Solutions LLC",
            "vendor_tax_id": "TAX-BETA-67890",
            "invoice_date": "2025-12-16",
            "due_date": "2026-01-16",
            "amount": 7500.00,
            "currency": "USD",
            "line_items": [
                {"desc": "Professional Services - Cloud Migration", "qty": 1, "unit_price": 5000.00, "total": 5000.00},
                {"desc": "Expedited Service Fee", "qty": 1, "unit_price": 1500.00, "total": 1500.00},
                {"desc": "Premium Support Package (3 months)", "qty": 1, "unit_price": 1000.00, "total": 1000.00}
            ],
            "attachments": ["invoice_002_amount_mismatch.html"]
        }
    },
    # Invoice 3: No PO Reference
    "003_no_po": {
        "json": {
            "invoice_id": "INV-2025-003",
            "vendor_name": "Gamma Enterprises",
            "vendor_tax_id": "TAX-GAMMA-11223",
            "invoice_date": "2025-12-17",
            "due_date": "2025-12-31",
            "amount": 5000.00,
            "currency": "USD",
            "line_items": [
                {"desc": "Emergency Equipment Repair Service", "qty": 8, "unit_price": 375.00, "total": 3000.00},
                {"desc": "Replacement Parts - Priority Delivery", "qty": 1, "unit_price": 1200.00, "total": 1200.00},
                {"desc": "Weekend Emergency Service Premium", "qty": 1, "unit_price": 800.00, "total": 800.00}
            ],
            "attachments": ["invoice_003_no_po.html"]
        }
    },
    # Invoice 4: Large Amount
    "004_large_amount": {
        "json": {
            "invoice_id": "INV-2025-004",
            "vendor_name": "Delta Technologies Inc",
            "vendor_tax_id": "TAX-DELTA-99887",
            "invoice_date": "2025-12-18",
            "due_date": "2026-01-18",
            "amount": 34200.00,
            "currency": "USD",
            "line_items": [
                {"desc": "Enterprise Software License - Premium Tier (500 users)", "qty": 500, "unit_price": 20.00, "total": 10000.00},
                {"desc": "Professional Implementation Services", "qty": 1, "unit_price": 15000.00, "total": 15000.00},
                {"desc": "Advanced Security Module Add-on", "qty": 1, "unit_price": 5000.00, "total": 5000.00},
                {"desc": "Managed Hosting & Infrastructure (12 months)", "qty": 12, "unit_price": 500.00, "total": 6000.00}
            ],
            "attachments": ["invoice_004_large_amount.html"]
        }
    },
    # Invoice 5: Duplicate
    "005_duplicate": {
        "json": {
            "invoice_id": "INV-2025-001",  # Same as invoice 1
            "vendor_name": "Acme Corporation",
            "vendor_tax_id": "TAX-ACME-12345",
            "invoice_date": "2025-12-15",
            "due_date": "2026-01-15",
            "amount": 5000.00,
            "currency": "USD",
            "line_items": [
                {"desc": "Industrial Widget Model X-2000", "qty": 10, "unit_price": 500.00, "total": 5000.00}
            ],
            "attachments": ["invoice_005_duplicate.html"]
        }
    }
}

def create_invoice_files():
    """Create all invoice JSON files"""
    import json
    
    base_dir = Path("data/sample_invoices")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    for invoice_key, data in INVOICES.items():
        json_file = base_dir / f"invoice_{invoice_key}.json"
        with open(json_file, 'w') as f:
            json.dump(data['json'], f, indent=2)
        print(f"Created: {json_file}")
    
    # Create test scenarios doc
    scenarios_content = """# Invoice Processing Agent - Test Scenarios

## Test Case Summary

| Invoice ID | Scenario | Expected Workflow Path | Expected Outcome |
|------------|----------|------------------------|------------------|
| INV-2025-001 | Perfect Match | INTAKE > UNDERSTAND > PREPARE > RETRIEVE > MATCH (OK) > RECONCILE > APPROVE > POSTING > NOTIFY > COMPLETE | Auto-complete, no HITL |
| INV-2025-002 | Amount Mismatch | INTAKE > ... > MATCH (FAIL) > CHECKPOINT_HITL > (pause) | Requires human review |
| INV-2025-003 | No PO Reference | INTAKE > ... > RETRIEVE (no PO) > MATCH (FAIL) > CHECKPOINT_HITL | Requires human review |
| INV-2025-004 | Large Amount | INTAKE > ... > APPROVE (escalate) > ... > COMPLETE | Auto-complete but escalated approval |
| INV-2025-005 | Duplicate | INTAKE > ... (duplicate detection) > FLAG | Should detect duplicate |

## Testing Instructions

1. **Start with Invoice 001** (Perfect Match)
   - Should complete end-to-end automatically
   - Verify all 12 stages execute
   - Check logs for successful completion

2. **Test Invoice 002** (Amount Mismatch)
   - Should pause at CHECKPOINT_HITL
   - Verify appears in human review dashboard
   - Test ACCEPT decision > should resume and complete
   - Test REJECT decision > should mark as manual handoff

3. **Test Invoice 003** (No PO)
   - Should pause at CHECKPOINT_HITL
   - Different reason: "No PO found"

4. **Test Invoice 004** (Large Amount)
   - Should complete but flag for manager approval
   - Check approval_status = "ESCALATED"

5. **Test Invoice 005** (Duplicate)
   - Should detect duplicate invoice_id
   - Verify duplicate handling logic

## Expected Processing Times

- Perfect match: ~2-5 seconds
- With HITL: Indefinite (waiting for human)
- After HITL decision: ~2-3 seconds to complete
"""
    
    scenarios_file = base_dir / "TEST_SCENARIOS.md"
    with open(scenarios_file, 'w') as f:
        f.write(scenarios_content)
    print(f"Created: {scenarios_file}")

if __name__ == '__main__':
    create_invoice_files()
    print("\n[OK] All invoice JSON files and test scenarios created!")
    print("Note: HTML files can be viewed in a browser to see formatted invoices")
