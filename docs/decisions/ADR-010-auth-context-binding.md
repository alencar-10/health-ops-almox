# ADR-010: Authentication and Operational Context Binding

## Status
Proposed (Cycle 10 - Security Foundation)

## Context
Currently, the multi-tenant context (Tenant, Unit) is resolved via HTTP headers (`X-Tenant-ID`, `X-Unit-ID`). While convenient for development and initial integration, this is insecure as it allows "context spoofing" (a user manually changing headers to access other tenants).

## Decision
We will transition to a **Secure Context Binding** strategy:

1.  **Identity-Derived Context**: The operational context must ultimately derive from a cryptographically signed token (JWT) or a secure server-side session.
2.  **Context Switching API**: Users will select their active context via a dedicated API endpoint (`/organization/switch`). This endpoint will:
    -   Validate that the user has permission to access the requested Tenant/Unit.
    -   Issue a new token or update the session with the bound context.
3.  **Middleware Authority**: The middleware will prioritize the context bound to the identity. Headers will only be accepted for administrative tasks or explicitly authorized development modes.
4.  **Hierarchical Enforcement**: Even with headers, the system must always validate that the `unit_id` belongs to the `tenant_id`.

## Consequences
-   Prevents unauthorized cross-tenant access.
-   Provides a clear path for implementing Roles and Permissions (RBAC) at different levels (Tenant Admin, Unit Pharmacist, etc.).
-   Requires an Identity and Access Management (IAM) layer.
