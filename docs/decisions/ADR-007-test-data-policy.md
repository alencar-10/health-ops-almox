# ADR-007: Test Data and Cleanup Policy

## Status
Proposed (Cycle 6 - Hardening)

## Context
With the introduction of an immutable inventory ledger (ADR-004) and a transactional ingestion pipeline (ADR-006), the risk of database corruption and historical inconsistency increases when performing "cleanup" operations in non-production environments.

## Decision
We will enforce a strict policy regarding data manipulation and environment cleanup:

1. **Production-Table Immutability**:
   - Production entities (`products`, `inventory_movements`, `manufacturers`, `active_ingredients`) must **NEVER** be deleted directly via `DELETE` statements in any environment intended for persistent historical integrity.
   - **Exception**: Ephemeral environments (CI/CD pipelines, isolated local testing databases) may be fully recreated or purged to ensure a clean state for automated test suites.
   - For test cleanup in persistent dev environments, we prefer using transactional rollbacks in test suites.

2. **Disposable Ingestion Layer**:
   - `import_staging` and `import_sessions` are considered part of the "Operational Buffer". They can be purged during development cycles to keep the staging area clean, provided no active session is being processed.

3. **Cleanup Script Safety**:
   - Any cleanup script must be restricted to ephemeral/dev environments and must clearly distinguish between "disposable buffer data" and "immutable operational data".
   - Purging operational data for local testing should ideally be done by recreating the entire database schema (`alembic downgrade base` -> `alembic upgrade head`) rather than selective `DELETE` which can orphan ledger records.

4. **Fixture Usage**:
   - Use standardized fixtures for master data (Manufacturers, Ingredients) to ensure consistent validation results across team members.

## Consequences
- Protects the integrity of the ledger as the "Single Source of Truth".
- Encourages the use of proper automated testing environments instead of manual DB manipulation.
- Prevents accidental data loss in environments that might have pseudo-production data.
