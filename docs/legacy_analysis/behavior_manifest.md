# Legacy Behavior Manifest (Vivver Reverse Engineering)

This document tracks **Operational Truth** extracted from the legacy Vivver system. We prioritize behavior (how it works) over technical implementation (how it was coded).

## 1. Confirmed Operational Rules
- **Hierarchical Persistence**: Changing a Unit must force a Sector re-selection.
- **Tenant = Municipality**: The highest scope is always the administrative organization.
- **Materialized Stock**: UI requires fast stock lookups (balances) but auditing requires a movement ledger.
- **Sector "GERAL"**: Every unit has an implicit or explicit general entry point.

## 2. Suspected Rules (Mining Pending)
- [ ] **Batch/Lot Tracking**: Does Vivver allow multiple batches of the same SKU in the same sector?
- [ ] **Expiry Validation**: Does the system block dispensing expired items?
- [ ] **Movement Approval**: Are transfers immediate or do they require "Acceptance" at the destination?
- [ ] **Unit Conversion**: Does ingestion handle different "Entry Units" vs "Stock Units"?

## 3. Workflow Invariants
- **Context Bar**: Operational context (Unit/Sector) must be visible and persistent on every screen.
- **Audit Requirement**: Every movement must have a human-readable "Reference Document" or "Reason".

## 4. Discarded Legacy Patterns (Technical Debt)
- Coupled session states.
- Manual SQL manipulation in the frontend.
- Global stock without location context.
