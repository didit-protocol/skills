---
type: llm
---

PASS if the reply compares the two from the documentation search, cites a docs.didit.me link, and says the method is turned on with `didit_authentication_method_set` and read back with `didit_authentication_get`.
FAIL if it gives no documentation link.
FAIL if it says methods can only be turned on in the Didit console.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
