---
type: llm
---

PASS only if the reply states all of these:
1. The live application is the one named "Sandbox" (its mode is live, whatever its name says).
2. Didit Authentication (Didit sign-in) is turned off for it, as `didit_authentication_get` reports (`enabled: false`).
3. Turning it on is done by a person in the Didit console, not by a tool.
FAIL if it says Authentication is on for the live application.
FAIL if it calls "Production copy" the live application, or calls "Sandbox" a sandbox or test application.
FAIL if it offers to turn Authentication itself on with a tool.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
