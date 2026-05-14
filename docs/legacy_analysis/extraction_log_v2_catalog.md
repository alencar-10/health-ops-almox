# Extraction Log v2: Catalog Registration (Principle & Product)

**Source**: `health-ops-ai_old` (`ProductCreator` service).
**Status**: Critical Rules extracted.

## 1. The 5-Step Pipeline (Operational Truth)
Legacy registration follows a strict stateful workflow to bypass Vivver API limitations:

1. **Step 1: Normalization & Code Gen**: Generate friendly code (8M+) and normalize descriptions (DescriptionFormatter).
2. **Step 2: Principle Creation**: Create `ActiveIngredient` with `codforma` (Pharmaceutical Form).
3. **Step 3: Catalog Sync (Wait)**: Perform a manual sync to find the `DT_RowId` of the new Principle.
4. **Step 4: Product Creation**: Create `Product` with Group/Subgroup IDs.
5. **Step 5: Semantic Linking**: For Medicines, explicitly call `link_principle` to bind Product to Principle.

## 2. Mandatory Dimensions
- **Pharmaceutical Form**: Essential for Principles.
- **Group/Subgroup**: Essential for Product classification (Filter/Reporting).
- **External Identifiers**: 
    - `erp_id` (Internal Database ID in Vivver).
    - `erp_code` (The code displayed to the user).

## 3. Business Logic
- **Item Type Sensitivity**: 
    - `MEDICAMENTO` -> Requires Principle Link.
    - `MATERIAL` -> Principle Link is skipped.
- **Patch Workaround**: Groups/Subgroups often fail during the initial `POST`, requiring a secondary `PATCH` after the Product ID is synced.

## 4. Impact on New Architecture
- **Stateful Registration**: Our Catalog API cannot be a simple CRUD; it must handle this multi-step "State Machine" or at least store the progress of the registration.
- **Data Model**: Must include ERP IDs for 2-way sync stability.
