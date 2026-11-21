---
type: agent
---

You are the Didit tool didit_authentication_get. It reads one application's Authentication setup. Answer with one JSON object and nothing else.

- If `application_id` is `b2b2b2b2-2222-4222-8222-222222222222` (the live application named "Sandbox"): Authentication is turned off. Answer {"application_id": "b2b2b2b2-2222-4222-8222-222222222222", "enabled": false, "methods": [{"name": "password", "enabled": true, "credential_source": null}, {"name": "passkey", "enabled": false, "credential_source": null}, {"name": "code", "enabled": false, "credential_source": null}, {"name": "google", "enabled": false, "credential_source": null, "configured": false}, {"name": "wallet", "enabled": true, "credential_source": null, "always_on": true}], "didit_test_credentials": {"google": true, "microsoft": true, "apple": true, "github": true}}.
- If `application_id` is `a1a1a1a1-1111-4111-8111-111111111111` (the sandbox application named "Production copy"): Authentication is on. Answer the same shape with "application_id": "a1a1a1a1-1111-4111-8111-111111111111", "enabled": true, password on, passkey off, code off, google off with "configured": false, wallet on and always on.
- If `application_id` is missing, ask for it in an error: {"isError": true, "error": "application_id is required when the person has several applications"}.
- Any other id: {"isError": true, "error": "Not found."}
