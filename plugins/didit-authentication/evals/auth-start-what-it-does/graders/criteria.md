---
type: llm
---

PASS if the reply says the plugin gives guidance and documentation search (configuration happens in the Didit console), and that sign-in is separate from identity verification, linked through the same vendor_data.
FAIL if it says a tool can configure sign-in methods, redirect URLs or settings.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
