# Extraction Log v1: Context Discovery (Unit/Sector)

**Source**: Legacy Vivver cURLs and Screenshots.
**Target**: `Seg::Operador::ConexaoQuery`

## 1. Findings: Permission-First Filtering
- **Evidence**: `where=,codmunicipio=2918001,codoperador=1642`
- **Rule**: The list of available Units is NOT just a list of all units in the Tenant. It is explicitly filtered by the **Operator ID**.
- **Impact**: Our `OrganizationService` must always join with `UserUnitAccess` for discovery.

## 2. Findings: Cascading Sector Dependency
- **Evidence**: Second cURL includes `codunidade=2` in the `where` clause.
- **Rule**: Sector discovery is a sub-query of the selected Unit + Operator permissions.
- **Impact**: UI must clear Sector selection immediately upon Unit change.

## 3. Findings: Persistent Identity (Sticky Context)
- **Evidence**: Bottom bar shows "52 - UNIDADE DE VIGILANCIA SANITARIA". User confirms context persists until manual intervention.
- **Rule**: The system must remember the "Last Active Posto de Trabalho".
- **Impact**: User model needs `last_unit_id` and `last_sector_id`.

## 4. Findings: Non-Standard Identifiers
- **Evidence**: `codunidade`, `codsetor`, `codmunicipio`.
- **Note**: These appear to be integer codes. Our system uses UUIDs internally, but we must store these as "External References" for future integration.

## 5. Artifacts Analyzed
- [Screenshot]: Bottom status bar, dropdown lookup pattern.
- [cURL 1]: Unit lookup with operator filter.
- [cURL 2]: Sector lookup with unit+operator filter.
