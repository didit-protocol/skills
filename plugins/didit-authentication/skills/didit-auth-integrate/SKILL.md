---
name: didit-auth-integrate
description: Used when a developer is wiring Didit sign-in into their app or backend, starting the hosted sign-in with PKCE, exchanging the authorization code, validating access tokens the way the application's documented runtime requires (opaque session check or ES256 JWT with the JWKS), checking a session, rotating refresh tokens, signing users out, or registering redirect URLs.
---

# Integrate the hosted sign-in

Follow the rules of didit-auth-start first: call `didit_context_get` for the application, and call `didit_docs_search` for the current tokens and quickstart pages before writing code. Docs mark Authentication as new. Never put a secret, a token or an API key in code, URLs or logs.

## 0. Prefer the SDKs

The docs list official packages per platform: `@didit-protocol/auth` (JavaScript, with `verifyToken` in `@didit-protocol/auth/server`), `@didit-protocol/auth-react`, `@didit-protocol/auth-nextjs`, the `DiditAuth` Swift package, `me.didit:didit-auth` for Android, `@didit-protocol/auth-react-native` and `didit_auth` for Flutter. Read the matching quickstart for the current version and setup. Build the steps below by hand only when no SDK fits.

## 1. Before code

- Each application has its own sign-in origin, which is also its token issuer: `https://<slug>.auth.didit.me` (live) or `https://<slug>.sandbox.auth.didit.me` (sandbox), or a verified custom domain. The console shows it.
- Register every exact redirect URL in the console (up to 50). The `redirect_uri` must match character by character. Live accepts only `https://`; sandbox also accepts `http://` on `localhost`, `127.0.0.1` or `[::1]`. No wildcards, fragments or custom schemes.
- If browser code calls the runtime API, add its origin to Allowed origins (no path, no trailing slash).
- The publishable key (`pk_live_...` or `pk_test_...`) identifies the application. It is not a secret.

## 2. Start sign-in (authorization code with PKCE)

Clients are public: no client secret. `client_id` is the application ID. PKCE method `S256` only.

1. Make a random PKCE verifier and a random `state`. Keep both in the tab or app that starts sign-in.
2. Open `{issuer}/sign-in` with `redirect_uri`, `state` (up to 512 characters), `code_challenge` (base64url SHA-256 of the verifier, 43 characters) and `code_challenge_method=S256`. Optional: `nonce`, `scope`, `login_hint` (prefills the email only), `ui_locales`, `max_age`, `prompt`.
3. The browser returns to `redirect_uri` with `code` and `state`. Reject the callback if `state` does not match.

## 3. Exchange the code

Within 60 seconds, once per code, send to `{issuer}/token/` (JSON or form body):

```text
POST {issuer}/token/
  grant_type    = authorization_code
  code          = <code from the callback>
  code_verifier = <the PKCE verifier>
  redirect_uri  = <the same redirect_uri>
```

The answer holds `access_token`, `id_token`, `refresh_token`, `token_type`, `expires_in` and `session_id`. `400 invalid_grant` covers an unknown, used or expired code, a verifier or redirect mismatch, a blocked person, and similar cases. Do not send `client_secret`; it is rejected as an unknown field.

## 4. Validate an access token on the server

The access token format depends on the application's Authentication runtime as documented. Before choosing a method, read the current tokens page with `didit_docs_search` (https://docs.didit.me/authentication/tokens-and-jwks) and follow what it says for this application:

- **Opaque access token:** do not decode it. Validate it with `GET {issuer}/session/` (see step 5) and cache the answer only briefly.
- **ES256 JWT access token** (`typ` `at+jwt`): verify it offline against the JWKS with the checks below.

Do not mix the two, and never invent a JWKS URL for a runtime that does not publish one. Take the issuer and application ID from configuration, never from the token. For a JWT, check all of these:

1. Header `alg` is `ES256` and `typ` is `at+jwt`. Reject anything else, `none` included.
2. The `kid` is in `{issuer}/.well-known/jwks.json` and the signature verifies.
3. `iss` equals the configured issuer; `aud` equals the application ID.
4. `exp` and `iat` are valid with up to 60 seconds of clock skew; `sub`, `sid` and `jti` are present.
5. `act` is null. A non-null `act` is an AI agent acting for the person: reject it unless the endpoint accepts agents, then allow only what `act.scopes` grants.

Keys: cache the JWKS for 5 minutes, keyed by `kid`. For an unknown `kid`, refetch at most once a minute, then reject. Keys rotate every 30 days with a day of overlap.

Useful claims: `sub` (the identity in this application), `vendor_data` (the same person across Didit products), `amr`, `org`, `verified`. The ID token has `typ: JWT` and adds `auth_time`, `email_verified` and, when set, `email`, `name`, `phone_number`. Check `nonce` on the ID token from the code exchange only. Never accept an ID token as an access token.

## 5. Check the session when it matters

Offline JWT checks cannot see a session that just ended. Before a sensitive step (a payout, for example), call `GET {issuer}/session/` with the access token as a Bearer token. A `401 invalid_token` means this access token is no longer accepted: the session may have ended, or the token expired. Refresh once; if the refresh answers `400 invalid_grant`, treat the person as signed out. A `429` or `503` proves nothing either way: block the sensitive step and retry later. It is rate limited, so do not call it on every request.

## 6. Refresh

Send `grant_type = refresh_token` and `refresh_token` to `{issuer}/token/`. Access tokens last at most 5 minutes.

- Each refresh returns a new access, ID and refresh token, and the old refresh token stops working. Replace all three together.
- Reuse ends the session: a used refresh token sent again revokes the session.
- Run one refresh at a time per session, across tabs, devices and servers.
- On `400` or no answer, start sign-in again; do not retry blindly. On `503 temporarily_unavailable`, retry with backoff. On `429`, wait for `Retry-After`.

## 7. Sign out

Signing out has two parts. Report them separately:

- **Local sign-out:** clear the tokens and user state in the app. Always do this when the person signs out.
- **Server revocation:** `DELETE {issuer}/session/` with the current access token. Only a `204` confirms the session was revoked on the server.

A `401` here means the access token was rejected, not that the session ended: refresh, then send the `DELETE` again with the new token. If that refresh answers `400 invalid_grant`, the session cannot be refreshed; treat the person as signed out locally. A `429`, a `503` or no answer means revocation is not confirmed: say so, retry with backoff (respect `Retry-After`), and never report the server session as ended. Then send the person to the configured `post_logout_redirect_uri`, if any. There is no end-session endpoint.

## 8. Store tokens by purpose

Keep verification API keys and console tokens on the server. Keep browser access tokens in memory where possible, or in secure HttpOnly cookies with CSRF protection. Store mobile refresh tokens in platform-protected storage.

## What good output looks like

- Code that follows the steps above, with each endpoint and claim backed by a cited docs link.
- Issuer and application ID read from configuration.
- No secret, token or key printed or hard-coded.

## Do not

- Never invent an endpoint, parameter, claim or header.
- Never send a verification API key or console token to the sign-in endpoints.
- Never ask for credentials (password, API key, one-time code).
- Never state prices. Link https://didit.me/pricing.
