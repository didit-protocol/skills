---
type: llm
---

PASS if the reply says the tools cannot tell whether Authentication is on and points the person to the Products page of the Didit console for the live application, naming which application is live from its mode (the one named "Sandbox").
FAIL if it claims Authentication is on or off, or offers to turn it on with a tool.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
