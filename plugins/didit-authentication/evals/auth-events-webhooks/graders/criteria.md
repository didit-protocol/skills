---
type: llm
---

PASS only if the reply states all of these:
1. A successful sign-in sends the `auth.login` webhook (other documented types such as `auth.login_failed`, `auth.signup` or `auth.new_device` may also be listed).
2. To receive them, a webhook destination is subscribed to the `auth.*` types, in the Didit console or with the webhook tools, and the reply does not create one without the person agreeing first.
3. It links a docs.didit.me page.
FAIL if it names as a webhook an `auth.` type that is not one of: `auth.signup`, `auth.login`, `auth.login_failed`, `auth.password_reset_requested`, `auth.password_reset_completed`, `auth.mfa_changed`, `auth.new_device`, `auth.account_locked`. Sign-out (`auth.logout`) is stored as an event but sends no webhook.
FAIL if it says a webhook destination was created or changed.
FAIL if it shows a full webhook destination URL or a signing secret.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
