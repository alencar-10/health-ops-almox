# ADR-006: Ingestion Pipeline Strategy

## Status
Proposed (Cycle 6)

## Context
Bulk data entry (importing products/stock) is a high-risk operation that can corrupt master data and inventory levels if not properly validated and reviewed.

## Decision
All bulk imports must follow a multi-stage **Ingestion Pipeline** instead of direct database writing.

1. **Staging Layer**: Raw data from files (CSV/XLSX) is first saved into a `import_staging` table.
2. **Session Management**: Every import belongs to an `import_session` with state tracking (PENDING, VALIDATED, COMPLETED, FAILED).
3. **Dry-run Validation**: Before persistence, the system performs a "Dry-run" to check for:
    - Missing mandatory fields (SKU).
    - Relational existence (Active Ingredient, Manufacturer).
    - Duplicates (EAN/SKU in production).
4. **Human-in-the-loop**: Persistence to production tables ONLY occurs after explicit user confirmation of the "Preview" report.
5. **Transactional Finality**: The final "Commit to Production" must happen in a single atomic transaction.

## Consequences
- Prevents database corruption from "dirty" files.
- Allows users to catch errors (like a typo in a manufacturer name) before they become permanent.
- Provides a clear audit trail of who imported what and when.
- Increases complexity but significantly increases operational reliability.
