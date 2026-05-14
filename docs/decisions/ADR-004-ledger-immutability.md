# ADR-004: Ledger Immutability

## Status
Proposed (Cycle 5)

## Context
Inventory accuracy depends on a reliable audit trail. Allowing edits or deletions of movements creates "shadow drifts" in stock levels.

## Decision
All records in `inventory_movements` are **Immutably Append-only**.

1. **No Edits**: The API will NOT provide `PATCH` or `PUT` endpoints for movements.
2. **No Deletions**: The API will NOT provide `DELETE` endpoints for movements.
3. **Error Correction**: If a movement was entered incorrectly (e.g., wrong quantity or product), it must be corrected by a counter-movement or an `ADJUSTMENT` type record.
4. **Traceability**: Every record is a permanent part of the history.

## Consequences
- Guarantees a perfect audit trail for any stock level at any point in time.
- Simplifies logic (no need to handle cascading effects of movement edits).
- Requires users to be more deliberate or perform "storno" operations for corrections.
