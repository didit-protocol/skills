---
type: llm
---

PASS if the reply says no password or API key is needed because sign-in happens through the Didit connection (OAuth), and answers the webhook question from the documentation search with a docs.didit.me link.
FAIL if it answers the webhook question from memory with no documentation link.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
