# ADR-012: Atomic Internal Sector Transfers

## Status
Proposed (Cycle 13 - Domain Extension)

## Context
Since the system now requires mandatory sectors and maintains stock balances at the sector level, moving items between sectors (e.g., Central Warehouse to Hospital Pharmacy) is a critical operational task.

## Decision
We will implement a **Transactional Transfer Entity**:

1.  **Atomic Pair Movement**: A transfer is NOT two independent movements. It is an atomic transaction consisting of:
    -   An `EXIT` movement from the origin sector.
    -   An `ENTRY` movement into the destination sector.
2.  **Shared Correlation ID**: Both movements must share the same `correlation_id` and a `transfer_id` reference.
3.  **Governance**:
    -   A transfer can only happen between sectors belonging to the same **Unit** or **Tenant** (cross-unit transfers are allowed but require higher authorization).
    -   Negative stock is prohibited at the origin sector.
4.  **Transfer Request Workflow (Optional)**:
    -   Future extension: Support for "Requested" -> "In Transit" -> "Received" states.

## Consequences
-   Ensures stock consistency across the entire organization.
-   Provides clear audit trails for internal logistics.
-   Prevents data loss during internal redistribution of items.
