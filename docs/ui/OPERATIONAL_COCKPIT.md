# Operational Cockpit (Persistent Context)

The UI must treat the operational context (Tenant, Unit, Sector) as the **Cockpit** of the application. It is not a filter; it is the active identity.

## 1. Visual Hierarchy
- **Level 1 (Municipality/Tenant)**: Top-most, semi-immutable. Visible but rarely interacted with.
- **Level 2 (Health Unit)**: Operational base.
- **Level 3 (Sector)**: Granular location. Must be explicitly selected.

## 2. Context Switch (2-Phase Confirmation)
To prevent "Context Mismatch" errors:
1. **Selection Phase**: User picks the target Unit/Sector. UI shows a "Preview" of the target environment.
2. **Confirmation Phase**: Explicit "Switch to this Context" action.
3. **Execution**:
    - Call `/organization/switch`.
    - Invalidate all caches (React Query).
    - Redirect to the Dashboard/Home to reset mental model.

## 3. Cockpit Metadata
Always visible at the bottom or top bar:
- **Active Context**: `Unit Name` / `Sector Name`.
- **Identity**: `User Full Name`.
- **System Health**: `Last Sync` / `Correlation ID` (short).
- **Safety Indicator**: "⚠ OPERATING IN: [SECTOR NAME]" highlighted if switching frequently.

## 4. Multi-Tab Protection
If the user opens a new tab, the system should ideally re-verify the session context to ensure Tab A isn't operating on Unit X while Tab B switched the global state to Unit Y.
