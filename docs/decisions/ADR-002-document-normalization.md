# ADR-002: Document Normalization

## Status
Proposed (Cycle 3)

## Context
Entities like Manufacturers and Suppliers use documents (CNPJ/CPF) as primary identification. These documents come in various formats (with or without dots, dashes, slashes).

## Decision
Documents will be normalized to contain **only numeric characters** before being saved to the database.

1. **Normalization Logic**: Remove all non-numeric characters (`\D`) and trim.
2. **Implementation**: Validation/Normalization happens at the **Schema (Pydantic)** layer for immediate user feedback and consistent API input.
3. **Storage**: `VARCHAR(20)` to accommodate various document lengths without masks.
4. **Uniqueness**: Documents are unique only when provided (Postgres allows multiple `NULL`s in unique columns).

## Consequences
- Simplifies search and comparison logic.
- Avoids duplicates caused by formatting differences (e.g., `12.345` vs `12345`).
- Frontend/Users are responsible for masking/displaying the document; the API/DB handles only the raw data.
