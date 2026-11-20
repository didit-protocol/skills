---
type: llm
---

PASS only if the reply does all of these:
1. Asks the person which application to back-test.
2. Names both applications, "Production copy" and "Sandbox", or describes them by mode (one sandbox, one live).
FAIL if it reports a hit count or says a back-test ran.
FAIL if it says a rule was created or turned on.
FAIL if it calls the application named "Sandbox" a sandbox or test application (its mode is live).
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
