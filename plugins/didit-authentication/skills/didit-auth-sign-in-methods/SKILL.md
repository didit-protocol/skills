---
name: didit-auth-sign-in-methods
description: Helps choose and set up the sign-in methods their users get with Didit Authentication. Use when the user asks about "passkeys", "magic links", "email or phone codes", "social sign-in", "organization SSO", "MFA", "password reset", "who can sign up", "invitations", or building their own sign-in screens with Didit.
---

# Sign-in methods, MFA and password reset

Follow the rules of didit-auth-start first: call `didit_context_get` for the application, and call `didit_docs_search` for the current sign-in methods page before giving details. Docs mark Authentication as new.

Methods are turned on and off with `didit_authentication_method_set` (see section 7) or in the Didit console. The hosted sign-in page shows only the methods that are on, and supports every available method below (the Didit ID Wallet is not available yet).

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

## 7. Turning methods on and off

- First read the setup with `didit_authentication_get` for the application, and check from `didit_context_get` whether it is sandbox or live (its `mode`, never its name). If `enabled` is false, Authentication is off for the application: no change can be made until a person turns it on in the Didit console.
- Describe the exact change (application, method, on or off, credential source) and wait for a clear yes before calling `didit_authentication_method_set` (rule 6 of didit-auth-start).
- Social methods (google, microsoft, apple, github) on a sandbox application can use `credential_source: "didit_test"`, Didit's own test provider apps, so they work without the developer's own provider app. A live application refuses it (`sandbox_only`): there the method needs the developer's own provider client id and client secret, with `credential_source: "own"`. Only the person can supply those; never invent them, and never repeat the secret back (the tools never return it).
- Phone needs the verification workflow whose phone step sends the code (`workflow_id`). The Didit ID Wallet method is always on.
- After each change call `didit_authentication_get` again and report what it shows.

## What good output looks like

- A short recommended set of methods, with what each needs (Didit's test app on sandbox, the developer's own provider app on live).
- Early access and "not available yet" items named as such.
- A docs link for every detail.

## Do not

- Never turn a method on or off without the person's clear yes, and never say a change worked without reading it back with `didit_authentication_get`.
- Never say a tool can turn Authentication itself on for an application; a person does that in the Didit console.
- Never invent a method name, endpoint or setting value.
- Never ask for credentials (password, API key, one-time code).
- Never state prices. Link https://didit.me/pricing.
