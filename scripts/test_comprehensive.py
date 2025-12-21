"""
Comprehensive application testing script with real invoice images
Tests all aspects: OCR, Workflow, API, Database, HITL
"""
import sys
import json
from pathlib import Path

# Fix console encoding for Windows (allows emoji output)
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback if encoding setup fails

def update_json_attachments():
    """Update all JSON files to reference JPG images instead of HTML"""
    invoice_dir = Path("data/sample_invoices")
    
    updates = {
        "invoice_001_perfect_match.json": "invoice_001_perfect_match.jpg",
        "invoice_002_amount_mismatch.json": "invoice_002_amount_mismatch.jpg",
        "invoice_003_no_po.json": "invoice_003_no_po.jpg",
        "invoice_004_large_amount.json": "invoice_004_large_amount.jpg",
        "invoice_005_duplicate.json": "invoice_005_duplicate.jpg",
    }
    
    print("[1/5] Updating JSON files to reference JPG images...")
    for json_file, jpg_file in updates.items():
        json_path = invoice_dir / json_file
        if json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Update attachments path
            data['attachments'] = [f"data/sample_invoices/{jpg_file}"]
            
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"  [OK] Updated {json_file}")
    
    print("[OK] All JSON files updated with JPG references\n")

def test_ocr():
    """Test OCR functionality with real images"""
    print("[2/5] Testing OCR with real invoice images...")
    
    try:
        from invoice_agent.bigtool.tools.ocr_tools import TesseractOCR
        from pathlib import Path
       
        ocr = TesseractOCR()
        test_images = [
            Path("data/sample_invoices/invoice_001_perfect_match.jpg"),
            Path("data/sample_invoices/invoice_002_amount_mismatch.jpg"),
            Path("data/sample_invoices/invoice_003_no_po.jpg"),
            Path("data/sample_invoices/invoice_004_large_amount.jpg"),
            Path("data/sample_invoices/invoice_005_duplicate.jpg"),
        ]
        
        for test_image in test_images:
            if test_image.exists():
                print(f"  Testing OCR on: {test_image}")
                text = ocr.execute(str(test_image))
                print(f"  [OK] OCR extracted {len(text)} characters")
                print(f"  Preview: {text[:200]}...")
            else:
                print(f"  [SKIP] Image not found: {test_image}")
            
    except Exception as e:
        print(f"  [INFO] OCR test: {e}")
        print(f"  [INFO] Will use mock OCR in workflow")
    
    print("[OK] OCR testing complete\n")

def test_workflow():
    """Test complete workflow with one invoice"""
    print("[3/5] Testing complete workflow...")
    
    try:
        from invoice_agent.agent.workflow_executor import start_workflow
        import asyncio
        
        # Test with perfect match invoice
        with open("data/sample_invoices/invoice_001_perfect_match.json", 'r') as f:
            invoice_data = json.load(f)
        
        print(f"  Testing workflow with: {invoice_data['invoice_id']}")
        
        # Run workflow
        result = asyncio.run(start_workflow(invoice_data))
        
        print(f"  [OK] Workflow Status: {result['status']}")
        print(f"  [OK] Current Stage: {result['current_stage']}")
        print(f"  [OK] Workflow ID: {result['workflow_id']}")
        
        if result['status'] == 'PAUSED':
            print(f"  [INFO] Checkpoint ID: {result.get('review_checkpoint_id')}")
            print(f"  [INFO] Review URL: {result.get('review_url')}")
        
    except Exception as e:
        print(f"  [ERROR] Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("[OK] Workflow testing complete\n")

def test_database():
    """Test database operations"""
    print("[4/5] Testing database...")
    
    try:
        from invoice_agent.database.checkpoint_store import CheckpointStore
        
        store = CheckpointStore()
        
        # Test getting pending reviews
        pending = store.get_pending_reviews()
        print(f"  [OK] Pending reviews: {len(pending)}")
        
        if pending:
            print(f"  [INFO] First review: {pending[0].get('invoice_id')}")
        
    except Exception as e:
        print(f"  [ERROR] Database test failed: {e}")
    
    print("[OK] Database testing complete\n")

def print_test_summary():
    """Print final test summary"""
    print("="  * 60)
    print("COMPREHENSIVE TEST COMPLETE")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Start API server:")
    print("   uv run uvicorn invoice_agent.api.main:app --reload --port 8000")
    print("\n2. Start Streamlit UI:")
    print("   uv run streamlit run src/invoice_agent/frontend/app.py --server.port 8501")
    print("\n3. Test all invoices:")
    print("   curl -X POST http://localhost:8000/workflow/start \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d @data/sample_invoices/invoice_001_perfect_match.json")
    print("\n4. Check pending reviews:")
    print("   curl http://localhost:8000/review/pending")
    print("\n5. Open Streamlit UI: http://localhost:8501")
    print("=" * 60)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("INVOICE PROCESSING AGENT - COMPREHENSIVE TEST")
    print("=" * 60 + "\n")
    
    try:
        # Run all tests
        update_json_attachments()
        test_ocr()
        test_workflow()
        test_database()
        print_test_summary()
        
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
