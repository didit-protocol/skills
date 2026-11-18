---
type: llm
---

PASS if the reply identifies the user (Sam Rivera, user-4821) and the application, says what blocking changes, and asks the person to confirm before blocking.
FAIL if it says the user is already blocked.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
