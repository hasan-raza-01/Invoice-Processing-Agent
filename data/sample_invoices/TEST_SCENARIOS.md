# Invoice Processing Agent - Test Scenarios

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
