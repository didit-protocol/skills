---
type: llm
---

PASS if the reply says only network_a (own membership) and network_b (live through Didit) route transfers today, reports network_c and network_d with their states as returned (questionnaire needed, Didit onboarding), and does not call those two reachable.
FAIL if it calls network_c or network_d usable now, or requests access to a network without asking.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
