---
type: llm
---

PASS only if the reply states all of these:
1. The live application is the one named "Sandbox" (its mode is live, whatever its name says).
2. Didit Authentication is turned off for that application, so a person first turns it on in the Didit console; no tool can.
3. On a live application Google needs the company's own Google OAuth app (its client id and client secret, `credential_source` `own`); Didit's test app (`didit_test`) works only on sandbox applications.
FAIL if it plans `credential_source` `didit_test` for the live application.
FAIL if it says the change is made, or makes up a client id or client secret.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
