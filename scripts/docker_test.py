"""
Docker Container Testing Script
Comprehensive tests for Invoice Processing Agent in Docker
"""
import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, '/app/src')

from invoice_agent.agent.workflow_executor import start_workflow
from invoice_agent.database.checkpoint_store import CheckpointStore
from invoice_agent.database.models import init_db
from invoice_agent.utils.logger import logger

print("=" * 60)
print("DOCKER CONTAINER - COMPREHENSIVE TESTING")
print("=" * 60)
print()

# Test results
results = []

def test_result(name: str, passed: bool, details: str = ""):
    """Record test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    results.append((name, passed, details))
    print(f"{status}: {name}")
    if details:
        print(f"  Details: {details}")
    print()

# Test 1: Database Initialization
print("Test 1: Database Initialization")
print("-" * 60)
try:
    init_db()
    test_result("Database Initialization", True, "Tables created successfully")
except Exception as e:
    test_result("Database Initialization", False, str(e))

# Test 2: Checkpoint Store
print("Test 2: Checkpoint Store Operations")
print("-" * 60)
try:
    store = CheckpointStore()
    # Use timestamp for unique checkpoint ID
    import time
    test_checkpoint_id = f"TEST-CKPT-{int(time.time())}"
    test_state = {"test": "data", "workflow_id": "test-workflow"}
    
    # Save checkpoint
    store.save_checkpoint(
        checkpoint_id=test_checkpoint_id,
        state_blob=test_state,
        invoice_id="TEST-INV-001",
        paused_reason="Test checkpoint"
    )
    
    # Load checkpoint
    loaded = store.load_checkpoint(test_checkpoint_id)
    
    if loaded and loaded.get("test") == "data":
        test_result("Checkpoint Store", True, "Save and load working")
    else:
        test_result("Checkpoint Store", False, "Data mismatch")
except Exception as e:
    test_result("Checkpoint Store", False, str(e))

# Test 3: Workflow Execution (Perfect Match)
print("Test 3: Workflow Execution - Perfect Match")
print("-" * 60)
try:
    # Load sample invoice
    invoice_path = Path("/app/data/sample_invoices/invoice_001_perfect_match.json")
    if invoice_path.exists():
        with open(invoice_path, 'r') as f:
            data = json.load(f)
            invoice_payload = data.get("invoice_payload", data)
        
        # Run workflow
        result = asyncio.run(start_workflow(invoice_payload))
        
        # Perfect match should complete automatically (no HITL needed)
        if result.get("status") == "COMPLETED":
            test_result(
                "Perfect Match Workflow",
                True,
                f"Workflow ID: {result.get('workflow_id')}, Status: COMPLETED (auto-approved)"
            )
        elif result.get("status") == "PAUSED":
            # If it pauses, check if it's expected (match failed)
            match_score = result.get("match_score", 0)
            if match_score < 0.9:
                test_result(
                    "Perfect Match Workflow",
                    False,
                    f"Match failed (score: {match_score}) - check mock ERP data"
                )
            else:
                test_result("Perfect Match Workflow", False, "Unexpected PAUSED status with good match")
        else:
            test_result(
                "Perfect Match Workflow",
                False,
                f"Unexpected status: {result.get('status')}"
            )
    else:
        test_result("Perfect Match Workflow", False, "Sample invoice not found")
except Exception as e:
    test_result("Perfect Match Workflow", False, str(e))

# Test 4: Workflow Execution (Amount Mismatch - HITL)
print("Test 4: Workflow Execution - Amount Mismatch (HITL)")
print("-" * 60)
try:
    invoice_path = Path("/app/data/sample_invoices/invoice_002_amount_mismatch.json")
    if invoice_path.exists():
        with open(invoice_path, 'r') as f:
            data = json.load(f)
            invoice_payload = data.get("invoice_payload", data)
        
        result = asyncio.run(start_workflow(invoice_payload))
        
        if result.get("status") == "PAUSED" and result.get("review_checkpoint_id"):
            test_result(
                "HITL Checkpoint Creation",
                True,
                f"Checkpoint ID: {result.get('review_checkpoint_id')}"
            )
        else:
            test_result(
                "HITL Checkpoint Creation",
                False,
                f"Status: {result.get('status')}, no checkpoint created"
            )
    else:
        test_result("HITL Checkpoint Creation", False, "Sample invoice not found")
except Exception as e:
    test_result("HITL Checkpoint Creation", False, str(e))

# Test 5: Bigtool Selection
print("Test 5: Bigtool Dynamic Selection")
print("-" * 60)
try:
    from invoice_agent.bigtool.bigtool_picker import BigtoolPicker
    
    picker = BigtoolPicker()
    
    # Test OCR selection
    ocr_tool = picker.select("ocr")
    if ocr_tool:
        test_result("Bigtool OCR Selection", True, f"Tool: {ocr_tool.__class__.__name__}")
    else:
        test_result("Bigtool OCR Selection", False, "No tool selected")
        
except Exception as e:
    test_result("Bigtool Selection", False, str(e))

# Test 6: MCP Clients
print("Test 6: MCP Client Operations")
print("-" * 60)
try:
    from invoice_agent.mcp.common_client import CommonClient
    from invoice_agent.mcp.atlas_client import AtlasClient
    
    common = CommonClient()
    atlas = AtlasClient()
    
    # Test COMMON client
    normalized = common.normalize_vendor("ACME CORP INC.")
    if "ACME" in normalized.upper():
        test_result("MCP COMMON Client", True, f"Normalized: {normalized}")
    else:
        test_result("MCP COMMON Client", False, "Normalization failed")
    
    # Test ATLAS client
    enriched = atlas.enrich_vendor("ACME Corp", "12-3456789")
    if enriched:
        test_result("MCP ATLAS Client", True, "Enrichment working")
    else:
        test_result("MCP ATLAS Client", False, "Enrichment failed")
        
except Exception as e:
    test_result("MCP Clients", False, str(e))

# Summary
print()
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)

print(f"Total Tests: {len(results)}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print("=" * 60)

if failed == 0:
    print("🎉 All tests passed!")
    sys.exit(0)
else:
    print("⚠️ Some tests failed!")
    print("\nFailed tests:")
    for name, passed, details in results:
        if not passed:
            print(f"  - {name}: {details}")
    sys.exit(1)
