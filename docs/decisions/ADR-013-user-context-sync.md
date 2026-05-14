# ADR-013: Dynamic User Context Synchronization

## Status
Proposed (Cycle 14 - IAM & UX Foundation)

## Context
In the Vivver operational model, users are granted access to specific Units and Sectors within a Municipality (Tenant). These permissions can change dynamically (e.g., a pharmacist being assigned to a new health unit). The platform must handle these changes without requiring a full logout and must track which context is "Active" vs "Allowed".

## Decision
We will implement a **Context Discovery and Switching** mechanism:

1.  **Access Matrix**: Permissions will be stored in hierarchical junction tables: `User -> Unit` and `User -> Sector`.
2.  **Explicit Context Selection**:
    -   The system will NOT automatically pick a context (unless a default is set).
    -   The UI must provide a "Context Switcher" based on the `/organization/available` API.
3.  **Context Polling/Sync**: The frontend should periodically refresh the "Available Contexts" to detect new grants (e.g., every 5-10 minutes).
4.  **Auditable Switching**: Every switch of the active context must be logged as a "Context Switch Event" with the timestamp and user ID.
5.  **Context Bound to Operations**: Every transactional log (movements, ingestion) must include the context active at the moment of the operation.

## Consequences
-   Enables secure and flexible multi-unit management.
-   Provides high-quality audit logs for organizational changes.
-   Simplifies the frontend by centralizing context discovery in a single API.
