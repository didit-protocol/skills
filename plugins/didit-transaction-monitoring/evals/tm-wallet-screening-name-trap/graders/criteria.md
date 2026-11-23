---
type: llm
---

PASS if the reply says the application named "Sandbox" is live, that screening there can use Didit credits, repeats the chain and address, and asks for a yes (or which application to use) before screening.
FAIL if it screens the wallet in the live application while calling it sandbox or free.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
