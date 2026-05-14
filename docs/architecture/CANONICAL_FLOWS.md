# Canonical Operational Flows

These flows define the mandatory sequence of actions and state changes for the core platform operations.

## 1. Context Switch Workflow
**Invariants:**
1.  Frontend requests available contexts.
2.  User selects a Unit + Sector.
3.  Frontend calls `/organization/switch`.
4.  Backend validates hierarchy and audits the event.
5.  Frontend invalidates all stock-related caches (Query Invalidation).
6.  Persistent context bar updates.

## 2. Inventory Movement Workflow (Ledger-first)
**Invariants:**
1.  Frontend captures movement data + active context.
2.  Backend locks the `InventoryBalance` row (`FOR UPDATE`).
3.  Backend appends a new `InventoryMovement` (Immutable Ledger).
4.  Backend updates the `InventoryBalance` (Materialized View).
5.  Transaction commits.

## 3. Bulk Ingestion Workflow (Staging-to-Prod)
**Invariants:**
1.  File upload -> Create `ImportSession` in `PENDING`.
2.  Dry-run Validation -> Update `ImportSession` to `VALIDATED`.
3.  User Review (Manual intervention).
4.  Confirmation -> Process valid rows -> Create Movements -> Update Balances.
5.  Update `ImportSession` to `COMPLETED`.

## 4. Disaster Recovery (Balance Rebuild)
**Invariants:**
1.  Admin identifies inconsistency.
2.  Admin locks product/sector balance.
3.  System sums all ledger movements for that product/sector.
4.  System overwrites `InventoryBalance`.
