# Operational Intentions Map

This document maps the **Human Intent** (what the user tries to achieve) to the **Technical Effects** (ledger changes, balance updates, reservations).

| Intent | Produce Movement? | Reservation? | Requires Acceptance? | Impact on Balance? |
| :--- | :---: | :---: | :---: | :---: |
| **DISPENSE** (Outbound) | Yes | No | No | Immediate Decrease |
| **TRANSFER_REQUEST** | No | Yes (Implicit) | Yes | None |
| **TRANSFER_SHIP** | Yes | Yes (In-transit) | Yes | Decrease Origin |
| **TRANSFER_RECEIVE** | Yes | No | Yes | Increase Destination |
| **INGESTION_DRY_RUN** | No | No | No | None |
| **INGESTION_CONFIRM** | Yes | No | No | Immediate Increase |
| **STOCK_ADJUSTMENT** | Yes | No | No | Corrective |
| **CATALOG_REGISTRATION** | No | No | No | None (Metadata only) |

## 1. Catalog Registration Pipeline (State Machine)
Registration in Vivver is non-atomic. We must manage the states:
1. `PRINCIPLE_PENDING`: Starting creation.
2. `PRINCIPLE_SYNCED`: Principle created and Internal ID (DT_RowId) captured.
3. `PRODUCT_PENDING`: Product creation in progress.
4. `PRODUCT_SYNCED`: Product created and Internal ID captured.
5. `COMPLETED`: Product and Principle linked (for medicines).
1. **No Ghost Stock**: Items in transit (TRANSFER_SHIP) must be accounted for as "Blocked" or in a virtual "In-transit Sector".
2. **Implicit Reservation**: A Transfer Request or a Batch Pick-list "commits" the quantity semanticly, even if the ledger entry happens later.
3. **Intent Source**: Every `InventoryMovement` must point to the `Intent` that triggered it (e.g., `intent_id`).
