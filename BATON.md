# BATON — Recovery Radar

MISSION: customer program cancellation / severe volume reduction → stranded exposure → contractual basis → evidence → defensible supplier claim → review → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN SOURCE TRUTH AT RECOVERY: repository contained only `.gitkeep`; no prior Recovery Radar implementation was present in GitHub source.

BUSINESS_STATE: `SIGNAL / HIGH COMPETITIVE COLLISION / COMMERCIAL SUCCESS UNPROVEN`.

SURVIVING WEDGE: supplier-side pre-audit and claim construction for customer program cancellation / severe volume reduction, especially stranded E&O / raw material / WIP / finished goods / tooling / NRE. Do not broaden into generic AP recovery, warranty recovery, or generic planning evidence.

DONE:
- event and stranded-exposure model;
- explicit exposure != entitlement != claimable;
- contractual/support states and documentary lineage;
- mitigation and prior-reimbursement deductions;
- ownership fail-closed handling;
- duplicate economic-loss protection;
- zero-defensible-claim case;
- partial-recovery case (€1M exposure / €420k reviewable cap);
- Alpha Components and RedTeam Industrial fixtures;
- independent arithmetic oracle and claim-line scorer;
- claim package;
- settlement/payment state machine with `SETTLED != PAID`;
- evidenced multiple payment records and duplicate/currency/overpayment controls;
- tenant-scoped SQLite claim persistence and audit events;
- pre-authenticated Principal service boundary with no caller-supplied workspace ID;
- cross-tenant guessed-ID/injection tests;
- reviewer cannot create, submit, negotiate, settle or record payment;
- backup/restore economic digest.

ORACLE RESULTS — SYNTHETIC ONLY:
- Alpha: €800 net exposure → €800 claimable; paid €0.
- Zero recovery: €1,000 exposure → €0 defensible claim.
- Partial recovery: €1,000,000 exposure → €420,000 `REQUIRES_REVIEW`; not silently €1M claimable.
- RedTeam: truth positive €670 = €250 CLAIMABLE + €420 REQUIRES_REVIEW; false claims 0; missed claims 0; overclaims 0; underclaims 0; state mismatches 0; absolute value error €0 for the covered fixture.

PRODUCT_TRUTH:
`CLAIMABLE` means the modeled economic/documentary prerequisites are satisfied. It is not legal certainty, customer approval, settlement or cash. `PAID` requires verified payment records exactly reconciling to the settlement amount.

SECURITY TRUTH:
Storage/service tenant scoping is implemented and tested. Authentication itself is NOT implemented; `Principal` is assumed to have been authenticated by an external boundary. Therefore secure company workspace remains PARTIAL, not GREEN.

LAST EXACT GREEN:
`15f34174b90716bd261cd6378f7f3debe006ecb4` — GitHub Actions `Recovery Radar` SUCCESS; 27 passed in 0.17s. This includes reviewer commercial-disposition restrictions and all source committed before documentation refresh.

CURRENT HEAD:
Documentation commits after the last exact test invalidate that SHA as current-head proof until CI reruns on the newest branch head.

P0/P1:
No known P0/P1 in the currently tested deterministic surface. This is not evidence of absence in a real authenticated/document-processing application. Authentication, document attacks, broader persistence, migration/failure testing and real supplier data remain incomplete.

COMPETITION / KILL TEST:
- SupplyWhy materially collides with automotive demand-change → operational cost exposure → claim evidence / recovery review.
- TRIGO provides evidence-based audits of program-cancellation supplier claims, including tooling, equipment, inventory and development work; current public positioning is especially buyer/OEM-side claim validation.
- Stellantis publicly hires dedicated Supplier Claims Auditors/Managers to substantively test cancellation claims, inventories, tooling and contractual eligibility.
- Generic supplier billing recovery and warranty supplier recovery are already crowded adjacent categories.

This does NOT kill the narrow supplier-side wedge yet, but eliminates generic “supplier claim evidence” as sufficient differentiation. The next decision-changing proof is whether a supplier-side pre-audit can materially improve claim completeness, defensibility, time-to-submit or realized recovery versus current manual/commercial process.

ACTIVE:
1. persist current competitive thesis/kills and pilot readiness truth;
2. make latest HEAD exact-CI GREEN;
3. attack evidence/document ingestion and conflict handling before UI polish.

NEXT:
- structured document/evidence registry with hashes, source/version identity and untrusted-text boundary;
- event/exposure/entitlement persistence, not only claim workflow persistence;
- document conflicts: PO vs terms, forecast vs release, email vs contract, stale cost, unsigned/irrelevant attachments;
- broader synthetic suppliers: Nova Precision, Titan, Legacy, Distressed;
- failure injection: DB lock, partial import, migration failure, backup corruption;
- scale/export acceptance;
- real auth/session boundary or integration with an existing trusted identity provider;
- historical supplier-pair pilot protocol only after PILOT_READY.

WAIT:
- real supplier/customer confidential data;
- external claim submission / supplier or OEM communication;
- negotiation or settlement action;
- production deployment / secrets / provider configuration;
- spending;
- WTP or paid-pilot evidence;
- merge to `main` without explicit authorization.

RESUME_AT:
`EVIDENCE REGISTRY → DOCUMENT CONFLICTS → PERSISTED LINEAGE → ADVERSARIAL DOCUMENT TESTS → EXACT-HEAD CI`.
