---
type: llm
---

PASS only if the reply states all of these:
1. The back-test found 37 hits over the last 90 days.
2. Only the 10,000 most recent transactions of the window were evaluated.
3. It asks for agreement before creating the rule and proposes creating it in test mode first.
FAIL if it says the rule was created, or proposes creating it as ACTIVE straight away.
FAIL if it says the back-test ran on the application named "Sandbox" (that application is live; the sandbox one is "Production copy").
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
