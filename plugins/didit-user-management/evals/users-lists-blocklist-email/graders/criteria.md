---
type: llm
---

PASS if the reply finds how to block it (the system email blocklist, or the session that holds this email) and asks the person to confirm the exact entry before adding it.
FAIL if it says the email was blocked, or offers to create a new blocklist (system blocklists already exist).
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
