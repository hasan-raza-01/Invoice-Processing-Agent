"""Demo script for testing the workflow"""
import asyncio
import json
from pathlib import Path

from invoice_agent.agent.workflow_executor import start_workflow
from invoice_agent.utils.logger import logger


async def run_demo():
    """Run demo with sample invoices"""
    
    print("=" * 80)
    print("🚀 INVOICE PROCESSING AGENT DEMO")
    print("=" * 80)
    
    # Load sample invoices
    samples_dir = Path("data/sample_invoices")
    
    test_cases = [
        {
            "file": "invoice_matched.json",
            "description": "Perfect Match - Should auto-complete"
        },
        {
            "file": "invoice_failed_match.json",
            "description": "Match Failure - Should trigger HITL checkpoint"
        },
        {
            "file": "invoice_new_vendor.json",
            "description": "New Vendor - Should complete with enrichment"
        }
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'='  * 80}")
        print(f"TEST CASE {idx}: {test_case['description']}")
        print(f"File: {test_case['file']}")
        print("=" * 80)
        
        invoice_path = samples_dir / test_case["file"]
        
        if not invoice_path.exists():
            print(f"⚠️  Sample file not found: {invoice_path}")
            continue
        
        # Load invoice
        with open(invoice_path) as f:
            invoice_data = json.load(f)
        
        print(f"\n📄 Invoice ID: {invoice_data['invoice_id']}")
        print(f"💰 Amount: ${invoice_data['amount']:.2f}")
        print(f"🏢 Vendor: {invoice_data['vendor_name']}")
        
        # Run workflow
        print(f"\n▶️  Starting workflow...\n")
        
        try:
            result = await start_workflow(invoice_data)
            
            print(f"\n✅ Workflow Result:")
            print(f"   Status: {result['status']}")
            print(f"   Current Stage: {result['current_stage']}")
            
            if result.get('checkpoint_id'):
                print(f"   ⏸️  Checkpoint Created: {result['checkpoint_id']}")
                print(f"   🔗 Review URL: {result['review_url']}")
            
            print(f"\n📋 Execution Logs:")
            for log in result.get('logs', [])[-5:]:  # Show last 5 logs
                print(f"   - {log}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print(f"\n{'='  * 80}")
        
        # Pause between test cases
        if idx < len(test_cases):
            await asyncio.sleep(2)
    
    print(f"\n{'='  * 80}")
    print("✅ DEMO COMPLETED!")
    print("=" * 80)
    print("\n💡 Next Steps:")
    print("1. Check the Streamlit UI at http://localhost:8501 for HITL reviews")
    print("2. View logs in ./logs/ directory")
    print("3. Check database: invoice_agent.db")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
