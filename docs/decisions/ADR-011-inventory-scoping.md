# ADR-011: Inventory Scoping and Decoupling (Catalog vs Stock)

## Status
Proposed (Cycle 11 - Architectural Correction)

## Context
Initial implementation tied the `stock_current` field directly to the `Product` model. In a multi-site operational system (Hospital, Pharmacy, Central Warehouse), the same Product exists across multiple locations with different stock levels. 

## Decision
We will decouple the **Product Catalog** from **Inventory Balances**:

1.  **Product Entity (Tenant-Scoped)**:
    -   Represents the global catalog entry for the organization.
    -   Belongs to a **Tenant**.
    -   Contains master data (Name, Manufacturer, SKU, EAN, Internal Code).
    -   **NO STOCK DATA** at this level.
2.  **Inventory Balance (Unit/Sector-Scoped)**:
    -   A new materialized entity representing the current stock of a Product at a specific location.
    -   Scoped by: **Tenant + Unit + Sector**.
    -   Unique combination: `(product_id, unit_id, sector_id)`.
3.  **Mandatory Operational Context**:
    -   `Unit` and `Sector` are now **MANDATORY** for all transactional operations (movements, ingestion, stock checks).
4.  **Transaction Logic**:
    -   Every `InventoryMovement` must explicitly target a `Sector`.
    -   The movement will trigger a transactional update on the corresponding `InventoryBalance` row.

## Consequences
-   Prevents catalog duplication (one Dipirona entry per tenant).
-   Enables precise, granular stock tracking per hospital wing or specific pharmacy sector.
-   Requires a migration to remove stock fields from the `products` table and initialize the `inventory_balances` table.
