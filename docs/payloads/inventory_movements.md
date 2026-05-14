# Canonical Payloads: Inventory Movements

This document defines the semantic schemas for all inventory operations. These payloads are the contract between the UI and the Backend.

## 1. Manual Stock Entry (ENTRY)
Used for manual adjustments or receiving items without a formal ingestion process.

**Schema:**
```json
{
  "product_id": "uuid",
  "quantity": 100.0,
  "reference_document": "NF-12345",
  "reason": "Initial stock setup",
  "metadata": {
    "batch_id": "optional-uuid",
    "expiry_date": "optional-iso-date"
  }
}
```

## 2. Stock Exit (EXIT)
Used for dispensing or operational consumption.

**Schema:**
```json
{
  "product_id": "uuid",
  "quantity": 5.0,
  "reason": "Dispensation to Patient A",
  "metadata": {
    "protocol_id": "optional-string"
  }
}
```

## 3. Internal Transfer (TRANSFER)
Used for moving items between sectors.

**Schema:**
```json
{
  "product_id": "uuid",
  "origin_sector_id": "uuid",
  "destination_sector_id": "uuid",
  "quantity": 50.0,
  "reason": "Replenishment"
}
```

## 4. Bulk Ingestion (INGESTION)
Schema for the ingestion staging session.

**Schema:**
```json
{
  "filename": "stock_may.csv",
  "target_sector_id": "uuid",
  "rows": [
    {
      "sku": "DIP-500",
      "quantity": 1000,
      "batch": "LOT-01",
      "expiry": "2026-12-31"
    }
  ]
}
```
