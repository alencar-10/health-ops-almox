# ADR-001: Soft Delete Policy

## Status
Proposed (Cycle 3)

## Context
We need a way to remove entities from operational view without losing historical data, auditability, and traceability.

## Decision
We will use a `deleted_at` (TIMESTAMPTZ) column to implement soft delete (archiving).

1. **Semantic**: The operation is called `archive` in services/API, not `delete`.
2. **Persistence**: Archived records **remain** in the database.
3. **Uniqueness**: Archived records **retain** their unique constraints (e.g., a document used by an archived supplier cannot be reused for a new one). This ensures audit trail integrity.
4. **Visibility**: Default API listings MUST filter out records where `deleted_at` is NOT NULL.
5. **Recovery**: Restoration of archived items is possible but requires a specific administrative action (not implemented in MVP).

## Consequences
- Prevents accidental data loss.
- Maintains database integrity for historical movements.
- Requires manual intervention to "release" a unique field if reuse is absolutely necessary (via direct DB update or future Admin tool).
