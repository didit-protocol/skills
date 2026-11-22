---
type: llm
---

PASS if the reply summarizes what it can do (transactions, rules and back-tests, wallet screening, alerts and cases, the AI Investigator, the Travel Rule) and, since there are two applications and no default, asks which one to use, naming each with its mode.
FAIL if it silently picks an application.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
