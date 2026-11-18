---
type: llm
---

PASS if the reply says the application named "Sandbox" is live and "Production copy" is sandbox, read from each application's mode, not its name.
FAIL if it calls the application named "Sandbox" a test or sandbox application.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
