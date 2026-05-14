# Architecture Freeze Checklist (Core Domain)

This document tracks the stability and completeness of the platform's core domain. Crossing these items signifies a "Freeze" of the architectural foundation.

## 1. Multi-tenant Context & Scoping
- [x] **Implicit Context**: `tenant_id`, `unit_id`, and `sector_id` are resolved via request context (`contextvars`).
- [x] **Hierarchical Validation**: Strict `Tenant -> Unit -> Sector` validation exists in the dependency layer.
- [x] **Discovery & Switching**: APIs for `/available` (Allowed) and `/switch` (Active) are implemented and audited.
- [ ] **Auth Binding (ADR-010)**: Context is cryptographically bound to identity (JWT). *[Pending]*

## 2. Inventory Ledger & Balances (ADR-003/011)
- [x] **Immutable Ledger**: `InventoryMovement` is append-only and context-scoped.
- [x] **Materialized Balances**: `InventoryBalance` stores stock per `Product + Unit + Sector`.
- [x] **Decoupled Catalog**: `Product` is a pure Tenant-level entity without stock fields.
- [x] **Rebuild Capability**: `InventoryRebuildService` can reconstruct balances from the ledger.

## 3. Ingestion Pipeline (ADR-006)
- [x] **Staging Architecture**: Data flows from Staging -> Validation -> Confirmation.
- [x] **Contextual Ingestion**: Sessions are bound to a specific operational scope (Tenant/Unit/Sector).
- [x] **Idempotence**: Double-confirmation of ingestion sessions is prohibited.

## 4. Observability & Governance
- [x] **Correlation Tracking**: `correlation_id` is propagated through all layers and logs.
- [x] **Structured Logging**: Context (Tenant, Unit, Sector) is automatically injected into logs.
- [x] **Operational Switch Audit**: Context switches are logged with IP, User Agent, and Correlation ID.

## 5. Next Evolutionary Steps (Non-Freeze)
- [ ] Internal Sector Transfers (ADR-012 logic).
- [ ] Batch/Lot and Expiry tracking.
- [ ] User Permission Matrix (RBAC).

---
**Status**: 90% Core Freeze. Finalizing audit metadata and security binding.
