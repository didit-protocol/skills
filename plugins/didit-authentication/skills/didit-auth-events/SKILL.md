---
name: didit-auth-events
description: Used when a developer asks how Didit sign-in activity shows up in the console, which auth webhooks exist and what they carry, how to subscribe to them, how sign-in events feed event rules and fraud views, or how to link sign-in risk to identity verification and transaction monitoring.
---

# Sign-in events and webhooks

Follow the rules of didit-auth-start first: call `didit_context_get` for the application, and call `didit_docs_search` for the current events and webhooks page before giving details. Docs mark Authentication as new: Didit turns on event delivery for the application.

## 1. What is sent

Authentication sends its own activity to Didit. The app does not submit sign-in events itself, and must not also post its own `auth.login` events for the same sign-ins: they would be stored twice.

| Activity | Stored as | Webhook |
|---|---|---|
| Sign-up | `auth.signup` | `auth.signup` |
| Sign-in | `auth.login` | `auth.login` |
| Failed sign-in | `auth.login_failed` | `auth.login_failed` |
| Sign-out or session revoked | `auth.logout` | none |
| Forgot password | `auth.password_forgot` | `auth.password_reset_requested` |
| Password reset | `auth.password_reset` | `auth.password_reset_completed` |
| Password changed | `security.password_changed` | none |
| Authenticator added or changed | `security.mfa_changed` | `auth.mfa_changed` |
| Sign-in from a new device | `security.device_changed` | `auth.new_device` |
| Account locked or blocked | `security.account_locked` | `auth.account_locked` |

Each event carries the sign-in method, a reason for failures and locks, the IP address, device context and the session ID. Bot protection decisions are also stored as `auth.*` events.

## 2. Where they show

- Each person gets a sign-in summary (`status` `ACTIVE`, `LOCKED` or `BLOCKED`, methods, MFA, last sign-in) on the People list and profile.
- Sign-in events appear on the console Events page and on each person's Events tab, next to their verifications and transactions, linked by `vendor_data`.
- The Events page has ready-made fraud views, for example one device used by several people, a spike of failed sign-ins from one IP, and a new device followed by a payout.

## 3. Webhooks

- Subscribe a webhook destination to the `auth.*` types the developer needs. Only subscribed destinations receive them.
- With the MCP tools, `didit_webhook_list` shows existing destinations and `didit_webhook_create` adds one (`label`, HTTPS `url`, `subscribed_events`). A destination URL can carry a secret in its path or query, so never show it in full: show it masked (the host, then `...` and the last 4 characters), with the label and the subscribed events, and wait for the person to confirm before creating it. Never print a signing secret.
- Deduplicate on `auth_event.event_id`; it stays the same across deliveries.
- `vendor_data`, `vendor_user_id` and `authentication` are null for an attempt that names no known person.
- Verify the signature as for every Didit webhook. Read the webhooks page with `didit_docs_search` for the method.

## 4. Event rules

Sign-in events run through the same event rules as other events. An Authentication fraud bundle has presets for account takeover, credential stuffing, a new device then a payout, and impossible travel.

The two sign-in actions, sign the person out of every session and block the person from signing in, are not active yet: a rule records them as `DISABLED` and does not apply them. Score, status, tags, notes, lists and cases work as usual. Say this plainly when a developer plans to rely on automatic sign-out or blocking.

## 5. Linking risk across products

- Use the person's `vendor_data` from a verified access token for verification sessions, transactions and the app's own events (profile changes, payout requests), which the app submits itself.
- Sign-in events then reach the same person's timeline and rules, so a risky sign-in can be weighed together with their verification and transactions.
- Each product's decision stays separate: a sign-in never approves a verification or a payment.

## 6. Billing

Authentication events are not billed per event; Authentication is billed by monthly active user. Never state a price: link https://didit.me/pricing.

## What good output looks like

- The exact `auth.*` webhook types for the developer's use case, from the table above.
- A deduplication and signature check in any webhook handler.
- Inactive rule actions named as not active yet.

## Do not

- Never invent an event type, payload field or rule field.
- Never tell the app to post its own `auth.login` events.
- Never ask for credentials (password, API key, one-time code).
- Never state prices. Link https://didit.me/pricing.
