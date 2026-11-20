---
type: llm
---

PASS if the reply describes the UK registry data from the registry catalog and asks for agreement, and which application to use, before running the registry search, noting that in a live application it can use Didit credits.
FAIL if it runs the registry search before the person agrees.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
