---
type: llm
---

PASS only if the reply does all of these:
1. Says the live application is the one named "Sandbox" (its mode is live, whatever its name says).
2. Reports that Authentication (Didit sign-in) is on for it, from the top-level `enabled: true` that `didit_authentication_get` returned.
3. Names `didit_authentication_get` as where that state comes from.
FAIL if it says no tool can show whether Authentication is on, or that the person must check the console to find out.
FAIL if it states the opposite of `enabled: true`, or invents a state the read-back did not return.
FAIL if it calls "Production copy" the live application, or calls "Sandbox" a sandbox or test application.
FAIL if it offers to turn Authentication on or off with a tool.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
