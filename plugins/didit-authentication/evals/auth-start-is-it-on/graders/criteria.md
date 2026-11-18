---
type: llm
---

PASS only if the reply states all of these:
1. The live application is the one named "Sandbox" (its mode is live, whatever its name says).
2. The tools cannot show whether Authentication (Didit sign-in) is turned on for it.
3. The person can check it on the Products page of the Didit console.
FAIL if it states as fact that Authentication is on, or that it is off, for the live application.
FAIL if it calls "Production copy" the live application, or calls "Sandbox" a sandbox or test application.
FAIL if it offers to turn Authentication on with a tool.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
