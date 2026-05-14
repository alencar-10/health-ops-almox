# ADR-008: Operational Context and Multi-tenancy Strategy

## Status
Proposed (Cycle 7 - Foundation)

## Context
As the Almoxarifado system evolves into a multi-organization platform, we need a consistent way to isolate data and scope operations. Currently, all data is "global". We need to support multiple organizations (Tenants), their physical locations (Units), and internal subdivisions (Sectors).

## Decision
We will implement an **Implicit Operational Context** based on a three-level hierarchy:

1.  **Hierarchy**:
    -   **Tenant**: The legal organization/client (e.g., "Prefeitura de Guaraciama").
    -   **Unit**: A physical site or branch (e.g., "Hospital Municipal", "Almoxarifado Central").
    -   **Sector**: A specific operational area within a unit (e.g., "Farmácia", "Laboratório").

2.  **Isolation Strategy**:
    -   **Shared Database, Logical Isolation**: All tenants share the same database and tables.
    -   Isolation is enforced via `tenant_id` and `unit_id` columns in operational tables.
    -   **Implicit Scoping**: Context resolution will happen via Middleware/Dependency Injection, preventing manual passing of IDs in every service call.

3.  **Implementation Phases**:
    -   **Phase 1**: Define organizational models (Tenants, Units, Sectors).
    -   **Phase 2**: Implement Context Middleware to resolve the active context from request headers/tokens.
    -   **Phase 3**: Retrofit operational entities (Products, Movements) with the corresponding context IDs.

## Consequences
-   Enables multi-client and multi-site operations within a single deployment.
-   Requires strict discipline in query construction (always filtering by tenant/unit).
-   Simplifies frontend development by providing a "global context" switcher that implicitly scopes all subsequent API calls.
