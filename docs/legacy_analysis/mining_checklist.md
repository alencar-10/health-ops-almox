# Mining Checklist: Operational Reverse Engineering

Use this guide to extract high-fidelity operational data from the legacy system without exposing sensitive credentials.

## 1. Capturing Network Logs (cURLs)
1. Open **Chrome Developer Tools** (F12 or Ctrl+Shift+I).
2. Go to the **Network** tab.
3. Perform the action (e.g., Click "Select Unit").
4. Right-click the relevant request (it usually has `Fetch`, `XHR` or `POST` type).
5. Select **Copy -> Copy as cURL (bash)**.
6. Paste it here (Redact sensitive cookies or tokens if needed, but keep the `Headers` structure).

## 2. Capturing Screenshots
- Capture the **entire screen** if possible to see the "Persistent Context Bar" (bottom/top).
- Highlight areas that change dynamically when a selection is made.

## 3. Behavioral Questions for Each Screen
- **What is the "Intent"?** (e.g., "I am entering stock from a physical invoice").
- **What can go wrong?** (e.g., "The system lets me pick a future date by mistake").
- **What is mandatory?** (e.g., "I cannot save without a batch number").
- **What is a workaround?** (e.g., "I always put '000' in the invoice field if I don't have it").

## 4. First Target: Context Selection
- [ ] Screenshot of Unit/Sector dropdowns.
- [ ] cURL of the `available_units` request.
- [ ] cURL of the `set_context` confirmation.
