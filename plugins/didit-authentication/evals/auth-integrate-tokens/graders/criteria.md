---
type: llm
---

PASS if the reply says the validation depends on the application's Authentication runtime as documented, reads the current tokens page with the documentation search and cites it, and keeps tokens and keys out of code, URLs and logs.
FAIL if it invents an endpoint, a claim name or a JWKS URL with no documentation link.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
