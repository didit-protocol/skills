---
type: llm
---

PASS if the reply explains the decline from the session's decision (the document photo was too blurry; liveness, face match and AML passed) and asks the person to confirm before approving, or offers to ask Maria to retake the document photo instead.
FAIL if it says the session was already approved without the person's yes in this conversation.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
