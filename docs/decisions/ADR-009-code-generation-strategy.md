# ADR-009: Tenant-Scoped Code Generation Strategy

## Status
Proposed (Cycle 8 - Governance)

## Context
In a multi-tenant operational system, numeric identifiers must be generated in a way that respects tenant-specific ranges (e.g., Tenant A starts at 5M, Tenant B at 8M) while preventing collisions and ensuring auditability.

## Decision
We will implement a **Transactional Backend Code Generator**:

1.  **Backend Authority**: Only the backend can generate internal codes. Frontend must never suggest or pre-calculate these identifiers.
2.  **Sequence Persistence**: A dedicated `code_sequences` table will store the state per tenant and entity type (e.g., products, orders).
3.  **Locking Strategy**:
    -   Use `SELECT ... FOR UPDATE` on the specific sequence row to serialize increments.
    -   **Uniqueness over Gapless**: We prioritize guaranteed uniqueness and monotonicity. While we aim for minimal gaps, they are acceptable in cases of transaction rollbacks or server crashes. Attempting to enforce 100% gapless sequences in a concurrent async system introduces significant locking overhead and risk of deadlocks.
    -   **Global Uniqueness**: Even with tenant-specific ranges, the `internal_code` is enforced as UNIQUE globally to prevent any ambiguity in multi-tenant reports or exports.
4.  **Separation of Concerns**:
    -   `sku`: Operational/Fiscal identifier (manual/external).
    -   `internal_code`: Numeric, system-generated identifier (internal governance).
5.  **Immutability**: Once assigned, the `internal_code` cannot be changed or reused, even if the entity is deleted.

## Consequences
-   Ensures visual and logical separation of data between tenants.
-   Prevents race conditions in code generation.
-   Provides a clean, numeric identifier for internal reporting and physical labeling.
