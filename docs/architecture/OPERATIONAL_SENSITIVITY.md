# Operational Sensitivity Matrix

This document defines the **Scoping Requirements** for different system modules. Not all operations require the same level of context granularity.

| Module | Sensitivity Level | Context Requirement | Rationale |
| :--- | :--- | :--- | :--- |
| **Inventory** | **SECTOR** | Tenant + Unit + Sector | Stock is physically located in a specific sector. |
| **Ingestion** | **SECTOR** | Tenant + Unit + Sector | Bulk entries must be tied to a receiving sector. |
| **Catalog** | **TENANT** | Tenant only | Product list is shared across the entire municipality. |
| **IAM/Auth** | **NONE** | System-wide | Managing users is an administrative cross-tenant task. |
| **Regulation** | **UNIT** | Tenant + Unit | Referrals are usually between units, not sectors. |
| **Audit Logs** | **TENANT** | Tenant minimum | Forensic trails must be visible at the tenant level. |

## Enforcement Strategy
1. **Implicit Scoping**: The context middleware must verify the required scope before allowing the request to reach the service layer.
2. **Context Cockpit**: The UI must automatically hide/disable the "Sector" selector when the active screen is only **UNIT** or **TENANT** sensitive.
3. **Audit Binding**: Every transaction must be stamped with the *highest possible* sensitivity level available in the context.
