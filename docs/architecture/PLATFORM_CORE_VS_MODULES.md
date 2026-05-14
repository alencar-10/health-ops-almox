# Platform Core vs. Operational Modules

This document defines the **Modular Monolith** strategy. We distinguish between the shared "Platform Infrastructure" and the specific "Domain Modules".

## 1. Platform Core (Shared Foundation)
These components are shared across ALL future modules (Inventory, Regulation, etc.).

- **Identity & Access (IAM)**: Users, Permissions, Unit/Sector Access matrix.
- **Operational Context**: Hierarchy resolution (`Tenant -> Unit -> Sector`).
- **Observability**: Structured Logging, Correlation IDs, Audit Trails.
- **Ingestion Engine**: Staging-to-Prod transactional logic.
- **Administrative Tools**: Code Generation, Sequence Management.

## 2. Operational Modules (Domain Specific)
These are independent business modules that plug into the Core.

### A. Inventory (Almoxarifado)
- Catalog (Products).
- Stock (Balances, Movements).
- Logistics (Transfers).

### B. Regulation (Regulação) - *Future*
- Procedures.
- Scheduling.
- External Integrations.

## 3. Interaction Rules
- **Modules MUST NOT** talk directly to other modules' databases.
- **Modules MUST** use the Platform Core for context resolution.
- **Platform Core MUST NOT** contain domain-specific logic (e.g., Core should not know about "Stock").

## 4. Scaling & Reversibility
- By keeping the Core clean, we can spin up a new project (e.g., "Health-Ops-Regulacao") by reusing only the `Core/` directory.
- This allows for "Separate projects but shared DNA".
