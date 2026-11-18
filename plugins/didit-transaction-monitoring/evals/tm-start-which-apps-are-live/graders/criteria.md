---
type: llm
---

PASS only if the reply states both of these:
1. The application named "Sandbox" is live.
2. The application named "Production copy" is in sandbox mode (not live).
FAIL if it calls "Sandbox" a sandbox or test application, or calls "Production copy" live.
FAIL if it says it cannot tell which application is live.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
