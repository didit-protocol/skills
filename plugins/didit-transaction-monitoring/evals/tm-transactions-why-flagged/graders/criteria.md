---
type: llm
---

PASS if the reply names the two rules that matched (Large single transfer, which sent it to review, and New beneficiary, which added to the score) and says the high-risk country rule did not match.
FAIL if it invents a rule title or an action not in the result.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
