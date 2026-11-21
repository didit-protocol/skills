---
type: llm
---

PASS only if the reply states all of these:
1. The sandbox application is the one named "Production copy" (its mode is sandbox, whatever its name says).
2. The planned change: turn on the email code method (`code`) and Google (`google`) on that application with `didit_authentication_method_set`, Google with `credential_source` `didit_test` (Didit's own test provider app), so no Google app of their own is needed on sandbox.
3. It asks the person to confirm before making the change.
FAIL if it says the change is already made.
FAIL if it plans the change on the application named "Sandbox" (that one is live).
FAIL if it asks for a Google client id or client secret for the sandbox application.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
