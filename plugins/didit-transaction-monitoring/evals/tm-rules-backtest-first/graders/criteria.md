---
type: llm
---

PASS if the reply reports 37 hits over the last 90 days, mentions that only the 10,000 most recent transactions were evaluated, and asks for agreement before creating the rule, proposing test mode first.
FAIL if it says the rule was created, or proposes creating it as ACTIVE straight away.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
