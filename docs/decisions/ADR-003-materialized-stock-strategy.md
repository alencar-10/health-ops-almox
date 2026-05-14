# ADR-003: Materialized Stock Strategy

## Status
Proposed (Cycle 4)

## Context
Stock levels need to be highly performant for listing and searching, but also highly accurate and traceable.

## Decision
We will store a `stock_current` column in the `products` table as a **materialized cache**.

1. **Truth Source**: The source of truth for stock is the `inventory_movements` table (the Ledger).
2. **Read-only Cache**: The `stock_current` field in the `products` table is **Read-only** for the Products CRUD API. It cannot be updated via `PATCH /products`.
3. **Atomic Updates**: Any update to `stock_current` MUST happen atomically within the same transaction that creates a record in `inventory_movements`.
4. **Precision**: We use `NUMERIC(15,4)` for all stock-related decimal fields to avoid floating-point errors and support fractional units.
5. **Initialization**: New products always start with `stock_current = 0`.

## Consequences
- Fast lookups for current stock without summing thousands of movement rows.
- Requires strict transactional discipline to keep the cache in sync with the ledger.
- Simplifies the Products API as it doesn't need to handle complex stock adjustment logic.
