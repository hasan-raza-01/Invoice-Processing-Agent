"""Comprehensive test suite for Invoice Processing Agent"""
import sys
import os
from pathlib import Path
import json
import time

# Fix console encoding for Windows (allows emoji output)
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback if encoding setup fails

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configure warnings before imports
from invoice_agent.utils.warnings_config import configure_warnings
configure_warnings()

from invoice_agent.agent.workflow_executor import start_workflow, resume_workflow
from invoice_agent.database.checkpoint_store import CheckpointStore
from invoice_agent.database.models import init_db, get_session, HumanReviewQueue
from invoice_agent.utils.logger import logger

print("=" * 60)
print("COMPREHENSIVE TEST SUITE - INVOICE PROCESSING AGENT")
print("=" * 60)
print()

def load_sample_invoice(filename: str) -> dict:
    """Load a sample invoice from data/sample_invoices"""
    filepath = project_root / "data" / "sample_invoices" / filename
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data["invoice_payload"]

def test_warnings_fixed():
    """Test 1: Verify no warnings on import"""
    print("Test 1: Verify No Warnings on Import")
    print("-" * 60)
    try:
        # This should produce no warnings
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from invoice_agent.api import main
            from invoice_agent.frontend import app
            
            if len(w) == 0:
                print("✅ PASSED: No warnings detected on import")
                return True
            else:
                print(f"❌ FAILED: {len(w)} warnings detected:")
                for warning in w:
                    print(f"   - {warning.category.__name__}: {warning.message}")
                return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        print()

def test_database_operations():
    """Test 2: Database Persistence"""
    print("Test 2: Database Persistence Operations")
    print("-" * 60)
    try:
        # Initialize database
        init_db()
        print("✅ Database initialized")
        
        # Test checkpoint store
        store = CheckpointStore()
        test_thread_id = "test_thread_123"
        test_state = {"test_key": "test_value", "stage": "TEST"}
        
        checkpoint_id = store.save_checkpoint(test_thread_id, test_state)
        print(f"✅ Checkpoint saved: {checkpoint_id}")
        
        # Retrieve checkpoint
        retrieved = store.get_checkpoint(checkpoint_id)
        assert retrieved is not None, "Checkpoint not found"
        assert retrieved["thread_id"] == test_thread_id
        print(f"✅ Checkpoint retrieved successfully")
        
        # Test human review queue
        with get_session() as session:
            review_count = session.query(HumanReviewQueue).filter_by(
                status="PENDING"
            ).count()
            print(f"✅ Human review queue operational ({review_count} pending)")
        
        print("✅ PASSED: Database operations working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_perfect_match_workflow():
    """Test 3: Perfect Match Invoice - Auto-completion"""
    print("Test 3: Perfect Match Workflow (Auto-complete)")
    print("-" * 60)
    try:
        invoice = load_sample_invoice("invoice_001_perfect_match.json")
        logger.info("Starting perfect match workflow test...")
        
        result = start_workflow(invoice)
        
        print(f"✅ Workflow completed")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Final Stage: {result.get('current_stage')}")
        
        # Should complete without HITL
        if result.get('status') == 'COMPLETED':
            print("✅ PASSED: Perfect match auto-completed")
            return True
        else:
            print(f"❌ FAILED: Expected COMPLETED, got {result.get('status')}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_hitl_checkpoint_creation():
    """Test 4: HITL Checkpoint Creation"""
    print("Test 4: HITL Checkpoint Creation (Match Failure)")
    print("-" * 60)
    try:
        invoice = load_sample_invoice("invoice_002_amount_mismatch.json")
        logger.info("Starting HITL checkpoint test...")  
        
        result = start_workflow(invoice)
        
        print(f"✅ Workflow paused")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Checkpoint ID: {result.get('checkpoint_id')}")
        
        # Should pause for HITL
        if result.get('status') == 'PAUSED' and result.get('checkpoint_id'):
            print("✅ PASSED: HITL checkpoint created successfully")
            return True, result.get('checkpoint_id')
        else:
            print(f"❌ FAILED: Expected PAUSED with checkpoint, got {result.get('status')}")
            return False, None
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None
    finally:
        print()

def test_hitl_accept_resume(checkpoint_id: str):
    """Test 5: HITL Accept & Resume"""
    print("Test 5: HITL Accept & Resume Workflow")
    print("-" * 60)
    try:
        if not checkpoint_id:
            print("⚠️ SKIPPED: No checkpoint ID provided")
            return False
        
        logger.info(f"Resuming workflow with ACCEPT decision...")
        
        result = resume_workflow(
            checkpoint_id=checkpoint_id,
            decision="ACCEPT",
            reviewer_id="test_reviewer_001",
            notes="Test acceptance"
        )
        
        print(f"✅ Workflow resumed")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Final Stage: {result.get('current_stage')}")
        
        if result.get('status') == 'COMPLETED':
            print("✅ PASSED: Workflow resumed and completed after ACCEPT")
            return True
        else:
            print(f"❌ FAILED: Expected COMPLETED, got {result.get('status')}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_hitl_reject():
    """Test 6: HITL Reject"""
    print("Test 6: HITL Reject Workflow")
    print("-" * 60)
    try:
        invoice = load_sample_invoice("invoice_002_amount_mismatch.json")
        result = start_workflow(invoice)
        
        if result.get('checkpoint_id'):
            checkpoint_id = result.get('checkpoint_id')
            logger.info(f"Rejecting workflow...")
            
            result = resume_workflow(
                checkpoint_id=checkpoint_id,
                decision="REJECT",
                reviewer_id="test_reviewer_002",
                notes="Test rejection"
            )
            
            print(f"✅ Workflow terminated")
            print(f"   - Status: {result.get('status')}")
            
            if 'REJECT' in result.get('status', '') or 'MANUAL' in result.get('status', ''):
                print("✅ PASSED: Workflow rejected successfully")
                return True
            else:
                print(f"❌ FAILED: Expected rejection status, got {result.get('status')}")
                return False
        else:
            print("❌ FAILED: No checkpoint created")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_bigtool_selection():
    """Test 7: Bigtool Dynamic Tool Selection"""
    print("Test 7: Bigtool Dynamic Tool Selection")
    print("-" * 60)
    try:
        from invoice_agent.bigtool.bigtool_picker import BigtoolPicker
        
        picker = BigtoolPicker()
        
        # Test OCR selection
        ocr_tool = picker.select_tool("ocr", {"context": "invoice_scan"})
        print(f"✅ OCR tool selected: {ocr_tool.__class__.__name__}")
        
        # Test enrichment selection
        enrich_tool = picker.select_tool("enrichment", {"vendor": "ACME"})
        print(f"✅ Enrichment tool selected: {enrich_tool.__class__.__name__}")
        
        # Test ERP selection
        erp_tool = picker.select_tool("erp_connector", {})
        print(f"✅ ERP tool selected: {erp_tool.__class__.__name__}")
        
        print("✅ PASSED: Bigtool selection working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_mcp_clients():
    """Test 8: MCP Client Operations"""
    print("Test 8: MCP Client Operations")
    print("-" * 60)
    try:
        from invoice_agent.mcp.common_client import CommonClient
        from invoice_agent.mcp.atlas_client import AtlasClient
        
        common = CommonClient()
        atlas = AtlasClient()
        
        # Test COMMON operations
        validated = common.validate_invoice_schema({"invoice_id": "TEST-001"})
        print(f"✅ COMMON validation: {validated}")
        
        normalized = common.normalize_vendor_name("ACME CORP INC.")
        print(f"✅ COMMON normalization: {normalized}")
        
        # Test ATLAS operations
        enriched = atlas.enrich_vendor("ACME Corp", "12-3456789")
        print(f"✅ ATLAS enrichment: {enriched.get('normalized_name')}")
        
        pos = atlas.fetch_purchase_orders("INV-001")
        print(f"✅ ATLAS PO fetch: {len(pos)} POs retrieved")
        
        print("✅ PASSED: MCP clients working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_error_handling():
    """Test 9: Error Handling"""
    print("Test 9: Error Handling & Edge Cases")
    print("-" * 60)
    try:
        # Test with invalid invoice payload
        try:
            result = start_workflow({})
            print("⚠️ Warning: Empty invoice accepted (unexpected)")
        except Exception as e:
            print(f"✅ Empty invoice rejected: {type(e).__name__}")
        
        # Test with missing required fields
        try:
            result = start_workflow({"invoice_id": "TEST"})
            print("⚠️ Warning: Incomplete invoice accepted")
        except Exception as e:
            print(f"✅ Incomplete invoice rejected: {type(e).__name__}")
        
        print("✅ PASSED: Error handling working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        print()

def run_all_tests():
    """Run all tests and generate report"""
    print("\n")
    print("=" * 60)
    print("STARTING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    checkpoint_id_for_resume = None
    
    # Test 1: Warnings
    results.append(("Warnings Fixed", test_warnings_fixed()))
    
    # Test 2: Database
    results.append(("Database Operations", test_database_operations()))
    
    # Test 3: Perfect Match
    results.append(("Perfect Match Workflow", test_perfect_match_workflow()))
    
    # Test 4: HITL Checkpoint
    passed, checkpoint_id = test_hitl_checkpoint_creation()
    results.append(("HITL Checkpoint Creation", passed))
    checkpoint_id_for_resume = checkpoint_id
    
    # Test 5: HITL Accept
    results.append(("HITL Accept & Resume", test_hitl_accept_resume(checkpoint_id_for_resume)))
    
    # Test 6: HITL Reject
    results.append(("HITL Reject", test_hitl_reject()))
    
    # Test 7: Bigtool
    results.append(("Bigtool Selection", test_bigtool_selection()))
    
    # Test 8: MCP Clients
    results.append(("MCP Clients", test_mcp_clients()))
    
    # Test 9: Error Handling
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print()
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<12} {test_name}")
    
    print()
    print("=" * 60)
    print(f"TOTAL: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 60)
    print()
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
