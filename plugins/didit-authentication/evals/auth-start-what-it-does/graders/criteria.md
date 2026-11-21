---
type: llm
---

PASS if the reply says the plugin gives guidance, documentation search and the six setup tools (read whether Authentication is on, turn sign-in methods on and off, change settings and onboarding), and that sign-in is separate from identity verification, linked through the same vendor_data.
FAIL if it says configuration happens only in the Didit console, or that no tool can read or change the Authentication setup.
FAIL if it says a call can turn Authentication itself on for an application.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
