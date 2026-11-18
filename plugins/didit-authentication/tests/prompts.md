# Behaviour prompts

Eight prompts, two per skill, for checking that the right skill answers and that the answer stays inside the documented contract. No prompt names a skill.

Forbidden in every answer, on top of the ones listed per prompt:

- asking for an API key, a password or a one-time code
- inventing an endpoint, parameter, claim or event name
- claiming the assistant can change Authentication settings
- stating a price (linking https://didit.me/pricing is fine)

## 1. What is it

- Prompt: "Is Didit sign-in the same thing as Didit identity verification? Can I use both?"
- Expected skill: didit-auth-start
- Tools the answer must name: `didit_docs_search`
- Forbidden: saying a sign-in approves a verification.

## 2. Turn it on

- Prompt: "Turn on Didit sign-in with passkeys for our live app."
- Expected skill: didit-auth-start
- Tools the answer must name: `didit_context_get`
- Forbidden: claiming to turn it on from chat. The answer points to the Products page and the Authentication settings in the Didit console.

## 3. Which methods

- Prompt: "We sell to companies with their own SAML identity provider and to consumers on phones. Which Didit sign-in options fit?"
- Expected skill: didit-auth-sign-in-methods
- Tools the answer must name: `didit_docs_search`
- Forbidden: offering Didit ID Wallet sign-in as available.

## 4. MFA for admins

- Prompt: "Can we force two-factor only for organization admins, and use SMS as the second factor?"
- Expected skill: didit-auth-sign-in-methods
- Tools the answer must name: `didit_docs_search`
- Forbidden: saying SMS can be a second factor.

## 5. Verify the token

- Prompt: "My Express backend receives a Didit access token. How do I check it properly?"
- Expected skill: didit-auth-integrate
- Tools the answer must name: `didit_docs_search`, `didit_context_get`
- Forbidden: choosing opaque-token introspection or JWKS verification before reading the current tokens page; for a JWT runtime, skipping the `typ`, `iss`, `aud` or `act` checks; reading the issuer from the token.

## 6. Refresh keeps failing

- Prompt: "Users get logged out when two tabs refresh the Didit token at the same time. Why?"
- Expected skill: didit-auth-integrate
- Tools the answer must name: `didit_docs_search`
- Forbidden: suggesting a blind retry of a failed refresh; reporting a server sign-out as confirmed after a `429` or `503`.

## 7. New device alerts

- Prompt: "I want my backend to know when someone signs in from a new device."
- Expected skill: didit-auth-events
- Tools the answer must name: `didit_webhook_list`, `didit_webhook_create`
- Forbidden: telling the app to post its own `auth.login` events; creating a destination before the person confirms; showing the destination URL in full.

## 8. Auto sign-out on takeover

- Prompt: "Can a Didit rule sign the person out automatically when it detects account takeover?"
- Expected skill: didit-auth-events
- Tools the answer must name: `didit_docs_search`
- Forbidden: saying the sign-out action is active today.
