from datetime import datetime, timezone
from decimal import Decimal
import unittest

from govmargin.domain import EconomicFinding
from govmargin.engine import FindingState
from govmargin.ingest import CrossTenantError, ImportValidationError, import_invoices, import_transactions, sha256_text
from govmargin.pack import PackStatus, build_recovery_pack
from govmargin.review import HumanReview, ReviewDecision

D = Decimal
HASH = sha256_text("evidence")


class IngestTests(unittest.TestCase):
    def test_transaction_import_is_tenant_scoped(self):
        text = f"organization_id,contract_id,period,transaction_id,category,amount,evidence_sha256\norg-a,C1,FY25,T1,travel,100,{HASH}\n"
        rows = import_transactions(text, "org-a")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, D("100"))

    def test_cross_tenant_transaction_fails_closed(self):
        text = f"organization_id,contract_id,period,transaction_id,category,amount,evidence_sha256\norg-b,C1,FY25,T1,travel,100,{HASH}\n"
        with self.assertRaises(CrossTenantError):
            import_transactions(text, "org-a")

    def test_duplicate_transaction_rejected(self):
        text = f"organization_id,contract_id,period,transaction_id,category,amount,evidence_sha256\norg-a,C1,FY25,T1,travel,100,{HASH}\norg-a,C1,FY25,T1,travel,100,{HASH}\n"
        with self.assertRaises(ImportValidationError):
            import_transactions(text, "org-a")

    def test_invalid_negative_amount_rejected(self):
        text = f"organization_id,contract_id,period,transaction_id,category,amount,evidence_sha256\norg-a,C1,FY25,T1,travel,-1,{HASH}\n"
        with self.assertRaises(ImportValidationError):
            import_transactions(text, "org-a")

    def test_invoice_import_preserves_payment_truth(self):
        text = f"organization_id,contract_id,invoice_id,amount,paid_amount,evidence_sha256\norg-a,C1,I1,100,75,{HASH}\n"
        row = import_invoices(text, "org-a")[0]
        self.assertEqual(row.amount, D("100"))
        self.assertEqual(row.paid_amount, D("75"))


class PackTests(unittest.TestCase):
    def recovery(self):
        return EconomicFinding("f1", "C1", FindingState.RECOVERY_CANDIDATE, D("100"), D("80"), D("80"), D("20"), ("e1",), ("r1",))

    def payable(self):
        return EconomicFinding("f2", "C1", FindingState.PAYABLE_CANDIDATE, D("90"), D("100"), D("100"), D("-10"), ("e2",), ("r2",))

    def test_unreviewed_candidate_stays_draft(self):
        pack = build_recovery_pack("org-a", [self.recovery()], [])
        self.assertEqual(pack.status, PackStatus.DRAFT)
        self.assertEqual(len(pack.approved_recovery_candidates), 0)
        self.assertEqual(len(pack.unresolved), 1)

    def test_human_approved_candidate_can_enter_client_finance_pack(self):
        review = HumanReview("f1", "reviewer@example", "GovCon finance reviewer", ReviewDecision.APPROVED, "Evidence and calculation lineage checked.", datetime.now(timezone.utc))
        pack = build_recovery_pack("org-a", [self.recovery(), self.payable()], [review])
        self.assertEqual(pack.status, PackStatus.READY_FOR_CLIENT_FINANCE_REVIEW)
        self.assertEqual(len(pack.approved_recovery_candidates), 1)
        self.assertEqual(len(pack.payable_exposures), 1)

    def test_rejected_recovery_never_enters_approved_pack(self):
        review = HumanReview("f1", "reviewer@example", "GovCon finance reviewer", ReviewDecision.REJECTED, "Contract ceiling evidence invalidates candidate.", datetime.now(timezone.utc))
        pack = build_recovery_pack("org-a", [self.recovery()], [review])
        self.assertEqual(pack.status, PackStatus.DRAFT)
        self.assertEqual(pack.approved_recovery_candidates, [])


if __name__ == "__main__":
    unittest.main()
