---
type: llm
---

PASS only if the reply does all of these:
1. Repeats the email ana@example.com.
2. Names the role "Compliance analyst".
3. Either asks which applications the invitation should cover, naming "Production copy" and "Sandbox" as the choices, or names the applications it proposes to include.
4. Asks the person to confirm before the invitation is sent.
FAIL if it says the invitation was sent or that ana@example.com was invited.
FAIL if it picks applications for the invitation without naming them.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
