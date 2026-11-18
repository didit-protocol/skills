---
type: llm
---

PASS only if the reply states all of these:
1. The access token is an ES256 JWT (`typ` `at+jwt`) verified offline against the issuer's JWKS (`{issuer}/.well-known/jwks.json`), either with `verifyToken` from `@didit-protocol/auth/server` or with a JWT library such as `jose`.
2. The issuer and application ID (or, with `verifyToken`, the publishable key) come from configuration, never from the token, and the token's `iss` and `aud` must match them.
3. It links a docs.didit.me page (the tokens and JWKS page or the JavaScript quickstart).
4. It keeps tokens and keys out of code, URLs and logs.
FAIL if it says the access token may be opaque, or that the validation method depends on the application's runtime: the docs describe one format, an ES256 JWT.
FAIL if it names an npm package other than `@didit-protocol/auth` (and its `/server` entry), `@didit-protocol/auth-react`, `@didit-protocol/auth-nextjs` or a general JWT library such as `jose`, or a Didit function other than `verifyToken` or `createDiditAuth`.
FAIL if it invents an endpoint or a claim name. `GET {issuer}/session/` as a stricter check before a sensitive step is correct.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
