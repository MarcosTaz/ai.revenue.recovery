# Recovery Radar

Evidence-first system for identifying, quantifying, constructing and defending supplier recovery claims after program cancellation or severe volume reduction.

## v0.1 source truth

The dedicated repository existed with only `.gitkeep` on `main`; no prior implementation was present in repository source. This branch establishes the canonical Recovery Radar implementation without changing the business thesis.

Implemented:

- deterministic recovery event model;
- stranded exposure by category;
- mitigation and prior reimbursement deduction;
- explicit entitlement states;
- exposure != entitlement != claimable;
- ownership checks;
- duplicate economic-loss fail-closed control;
- missing-evidence detection;
- claim package projection;
- legal/high-risk review boundary;
- Alpha Components clean cancellation;
- zero-defensible-claim synthetic case;
- €1M exposure / €420k partially supported review case;
- independent arithmetic oracle;
- claimable value never becomes PAID automatically.

Not yet implemented: persistence/auth/tenant isolation, document ingestion, claim workflow/payment ledger, broad adversarial document tests, backup/restore, web UI, real supplier evidence or WTP.
