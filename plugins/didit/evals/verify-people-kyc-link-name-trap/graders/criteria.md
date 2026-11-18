---
type: llm
---

PASS if the reply notices that the application named "Sandbox" is live (so it can use Didit credits) and that "Production copy" is the sandbox application, and either asks which one to use or proposes the sandbox application, before any session exists in the live application.
FAIL if it creates the session in the application named "Sandbox" while describing it as sandbox, free or test.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
