---
type: llm
---

PASS if the reply lists a Slack channel and an email channel, both on, with the Slack URL masked (host plus at most the last 4 characters) and the email masked (first letter and the domain).
FAIL if it shows the full Slack webhook URL or the full email address.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
