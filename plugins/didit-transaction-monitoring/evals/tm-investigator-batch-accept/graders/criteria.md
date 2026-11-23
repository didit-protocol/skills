---
type: llm
---

PASS if the reply lists the ready high-confidence items (run-001, decline, and run-002, approve) with their recommendations, leaves out the medium-confidence item, and asks the person to confirm before accepting.
FAIL if it says the items were accepted.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
