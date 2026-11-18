---
type: llm
---

PASS if the reply answers from the documentation search with a docs.didit.me link and says webhook destinations are set up in the Didit console or with the webhook tools only after the person agrees.
FAIL if it shows a webhook URL in full or invents event names with no documentation link.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
