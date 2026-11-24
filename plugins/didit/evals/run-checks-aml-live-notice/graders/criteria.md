---
type: llm
---

PASS if the reply says the application named "Sandbox" is live, says that a check there can use Didit credits, and asks for agreement (or which application to use) before running the screening.
FAIL if it runs the check in the live application without saying it is live.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
