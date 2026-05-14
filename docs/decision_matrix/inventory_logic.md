# Inventory Logic Decision Matrix

This document tracks unresolved domain questions and the final decisions made to ensure architectural consistency.

| Domain Area | Open Question | Current Hypothesis | Final Decision |
| :--- | :--- | :--- | :--- |
| **Batch/Lot** | Is Batch tracking mandatory for all products? | No, only for Medications/Vaccines. | TBD |
| **Expiry** | Is Expiry Date required for every movement? | Required for Entry, optional for Exit. | TBD |
| **Dispensing** | Does the system use FEFO (First Expired, First Out)? | Yes, as it's standard for health. | TBD |
| **Transfers** | Do transfers require dual-approval? | Yes, "Sent" -> "Received". | TBD |
| **UoM** | Do we support internal Unit Conversions (e.g. Box -> Tablet)? | Yes, via Ingestion & Movements. | TBD |
| **Reservation** | Can items be "Reserved" before dispensing? | No, keep it simple (Movement only). | TBD |

## Key Decision Points
1. **Lote por Saldo**: If Batch is mandatory for tracking, the `InventoryBalance` MUST include `batch_id` as part of its uniqueness constraint.
2. **Validade por Saldo**: If Expiry is mandatory, it must also be in the balance key.
