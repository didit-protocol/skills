---
name: didit-auth-sign-in-methods
description: Used when a developer is choosing which Didit sign-in methods to offer their users (password, email code, magic link, phone code, passkey, social sign-in, organization SSO), setting up MFA, password reset, sign-up policy or invitations, or building their own sign-in screens instead of the hosted page.
---

# Sign-in methods, MFA and password reset

Follow the rules of didit-auth-start first: call `didit_context_get` for the application, and call `didit_docs_search` for the current sign-in methods page before giving details. Docs mark Authentication as new.

Methods are turned on in the Didit console. The hosted sign-in page shows only the methods that are on, and supports every available method below (the Didit ID Wallet is not available yet).

## 1. The methods

| Method | Name | What it needs |
|---|---|---|
| Password | `password` | Also needed for email sign-up with a password. Only people with a verified email can sign in with it. |
| Email code | `code` | Nothing. A 6-digit code that lasts 10 minutes, 5 attempts. |
| Magic link | `magic` | Nothing. Hosted pages only. Lasts 15 minutes, works once, in the browser that asked for it. |
| Phone code | `phone` | The `workflow_id` of a workflow that contains phone verification. SMS by default, or WhatsApp. |
| Passkey | `passkey` | Nothing. WebAuthn on the application's sign-in origin, user verification always required. |
| Social | `google`, `microsoft`, `apple`, `github` | The developer's own OAuth `client_id` and `client_secret`. Sandbox applications can use Didit's test apps. |
| Organization SSO | `sso` | A SAML or OIDC connection per customer organization. |
| Didit ID Wallet | `wallet` | Not available yet. |

## 2. Choosing

Help the developer pick from what is documented:

- Passwordless options: email code, magic link, phone code, passkey. A passkey sign-in counts as multi-factor.
- A passkey belongs to its origin. Moving to a custom domain later means people enroll their passkeys again.
- GitHub is not offered when a sign-in asks for a recent sign-in (`prompt=login` or `max_age`).
- Business customers who use their own identity provider: organization SSO. Hosted sign-in finds the connection from the email domain or from `organization=<slug>` on the sign-in URL.
- Phone code depends on Didit phone verification; read the phone verification docs for coverage.

## 3. Who can sign up

`signup_policy` is `anyone` (default), `invited` (only with an invitation link, which lasts 7 days) or `allowed_domains`. A login code for an address with no account creates one when the policy allows it. With `allow_subaddresses` off (default), an email with `+` is rejected.

## 4. MFA

- Second factors: an authenticator app (TOTP) with 10 single-use recovery codes, or a passkey. SMS and email codes are not second factors.
- `mfa_policy` is `optional`, `everyone` or `organization_admins` (default). Anyone who enrolled an authenticator must always use it.
- Enrolling needs a session created within the last 5 minutes. Show recovery codes once.

## 5. Password reset

- The reset link lasts 30 minutes. The start step answers the same whether or not the address has an account.
- Completing a reset clears a lockout, ends every session when `revoke_on_password_change` is on (default), and invalidates other pending codes and links.
- `password_min_length` is 8, 10 (default), 12 or 14. Common and all-numeric passwords are rejected.

## 6. Own sign-in screens

With `sign_in_ui: "own"`, the app calls JSON endpoints instead of the hosted page. Each flow starts with a transaction that lasts 10 minutes and ends with a code to exchange within 60 seconds (see didit-auth-integrate). A step can return `mfa_required`, `mfa_enrollment_required`, `protection_required` or `verification_required` instead of a code. Read the exact endpoints with `didit_docs_search` before writing them. Recommend the hosted page unless the developer needs their own screens.

## What good output looks like

- A short recommended set of methods, with what each needs in the console.
- Early access and "not available yet" items named as such.
- A docs link for every detail.

## Do not

- Never say this plugin can turn methods on; that happens in the Didit console.
- Never invent a method name, endpoint or setting value.
- Never ask for credentials (password, API key, one-time code).
- Never state prices. Link https://didit.me/pricing.
