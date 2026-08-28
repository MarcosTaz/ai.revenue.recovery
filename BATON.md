# BATON — Recovery Radar

MISSION: customer program cancellation / severe volume reduction → stranded exposure → contractual basis → registered evidence → defensible supplier claim → review → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN SOURCE TRUTH AT RECOVERY: repository contained only `.gitkeep`; no prior Recovery Radar implementation was present in GitHub source.

BUSINESS_STATE: `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN / COMMERCIAL SUCCESS UNPROVEN`.

SURVIVING WEDGE: **supplier-side cancellation-claim pre-audit** for customer program cancellation / severe volume reduction, especially stranded E&O / raw material / WIP / finished goods / tooling / NRE. Do not broaden into generic AP recovery, warranty recovery or generic planning evidence.

DONE:
- event and stranded-exposure model;
- exposure != entitlement != claimability;
- contractual/support states and documentary lineage;
- mitigation and prior-reimbursement deductions;
- ownership fail-closed handling;
- duplicate economic-loss protection;
- zero-defensible-claim and partial-recovery cases;
- Alpha Components and RedTeam Industrial fixtures;
- independent arithmetic oracle + claim-line scorer;
- structured claim package;
- settlement/payment workflow with `SETTLED != PAID`;
- evidenced multi-payment records, duplicate/currency/overpayment controls;
- tenant-scoped SQLite claim persistence and audit events;
- pre-authenticated Principal service boundary; no caller-selected workspace ID;
- guessed-ID and cross-tenant injection tests;
- reviewer limited to evidence/review states and cannot submit/settle/pay;
- backup/restore economic digest;
- SHA-256 evidence metadata registry;
- persistent tenant-scoped document identities/hashes;
- document ID/version and duplicate-content controls;
- wrong supplier/customer/program/tenant and signature checks;
- untrusted extracted-text marker;
- deterministic fact-conflict resolver: disagreements do not silently choose precedence;
- registered-evidence claimability gate requiring registered event, cost/inventory, contractual/support and conditional mitigation/reimbursement evidence before claim package readiness.

ORACLE RESULTS — SYNTHETIC ONLY:
- Alpha: €800 net exposure → €800 candidate claim after complete registered evidence gate; PAID €0.
- Zero recovery: €1,000 exposure → €0 defensible claim.
- Partial: €1,000,000 exposure → €420,000 remains `REQUIRES_REVIEW`; not silently €1M claimable.
- RedTeam: truth positive €670 = €250 claimable + €420 requires review; false claims 0; missed claims 0; overclaims 0; underclaims 0; state mismatches 0; absolute value error €0 for covered fixture.

PRODUCT_TRUTH:
Nonempty evidence-reference strings are not enough for package readiness. The registered-evidence gate must resolve each required source to a registered, correctly scoped evidence record. Gate failure downgrades the line to `POTENTIAL_ENTITLEMENT`. `CLAIMABLE` remains a workflow/economic conclusion, not legal certainty, settlement or cash. `PAID` requires verified payment records reconciling exactly to the settlement amount.

SECURITY TRUTH:
Storage/service tenant scoping is implemented and tested for claim and evidence records. Authentication itself is NOT implemented; `Principal` is assumed to be authenticated by an external boundary. Therefore secure company workspace remains PARTIAL, not GREEN.

LAST EXACT GREEN:
`dec1f0893592900ac0d3b04c66250b19b6d61dcd` — GitHub Actions SUCCESS; **46 passed in 0.18s** on Python 3.13.15. Documentation commits after that SHA require another exact-head CI observation before the newest branch HEAD is called GREEN.

P0/P1:
No known P0/P1 in the covered deterministic surface. This does not establish absence across production authentication, raw-document parsing, full evidence persistence, migration/failure recovery or real supplier data.

COMPETITION / KILL TEST:
- SupplyWhy collides materially with automotive demand-change → inventory/cost exposure → claim evidence/recovery review.
- TRIGO provides evidence-based program-cancellation supplier-claim audits covering tooling/equipment/inventory/development work, especially buyer/OEM-side validation.
- Stellantis publicly operates dedicated supplier cancellation-claim audit roles performing substantive tests, tooling/inventory verification and contractual/commercial review.
- Public automotive terms show cancellation claims can have short submission windows, detailed supporting-data requirements, audit rights, category exclusions and tooling-specific conditions.

This kills generic “supplier claim evidence” positioning but not yet the narrower supplier-side **pre-audit before OEM scrutiny** hypothesis.

ACTIVE:
1. make the newest documentation/current branch HEAD exact-CI GREEN;
2. persist full event/exposure/entitlement state, not only claim workflow/evidence metadata;
3. expand conflict tests into stale costs, ownership disagreement and release/forecast contradictions;
4. attack failure/recovery and migration paths before UI polish.

NEXT:
- full claim evidence graph persistence and linkage IDs;
- Nova Precision / Titan / Legacy / Distressed synthetic suppliers;
- DB lock, partial import, migration failure and backup-corruption tests;
- scale/export acceptance;
- authentication/session provider boundary;
- historical supplier pilot protocol only after PILOT_READY.

WAIT:
- real supplier/customer confidential data;
- external claim submission / supplier or OEM communication;
- negotiation or settlement action;
- production deployment / secrets / provider configuration;
- spending;
- WTP or paid-pilot evidence;
- merge to `main` without explicit authorization.

RESUME_AT:
`EXACT HEAD GREEN → PERSIST EVENT/EXPOSURE/ENTITLEMENT GRAPH → ADVERSARIAL CONFLICTS → FAILURE/RECOVERY`.
