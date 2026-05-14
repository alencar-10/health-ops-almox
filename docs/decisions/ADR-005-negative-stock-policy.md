# ADR-005: Negative Stock Policy

## Status
Proposed (Cycle 5)

## Context
Operating with negative stock levels undermines trust in the system and complicates physical audits.

## Decision
The system will **Prohibit Negative Stock** levels.

1. **Validation**: Every `EXIT` movement must be validated against the current `stock_current` of the product.
2. **Atomic Lock**: Validation MUST occur while holding a database lock (`SELECT FOR UPDATE`) on the product row to prevent race conditions (two exits consuming the same last items).
3. **Rejection**: If `quantity_requested > stock_current`, the transaction MUST be rolled back and an error returned to the user.
4. **Exceptions**: `ADJUSTMENT` types might technically lead to negative stock if forced by an administrator, but for the MVP, the rule applies to all movement types to maintain absolute consistency.

## Consequences
- Ensures physical and digital stock remains synchronized.
- Prevents operational chaos in the warehouse.
- Requires immediate investigation when "system says no" but "physical says yes" (unrecorded entries).
