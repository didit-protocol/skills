---
name: didit-tm-wallet-screening
description: Screens one crypto wallet address for AML risk with Didit without recording a transaction. Use when the user says "screen a wallet", "check this wallet address", "is this address sanctioned", "wallet risk score", "where did these funds come from", or asks what to do about a risky wallet in their Didit account.
---

# Wallet screening

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application.

## 1. Before screening

- `didit_transaction_screen_wallet` checks one address without creating a transaction.
- It needs transaction monitoring configured for the application. Without it, the tool answers `409`: tell the person to set up transaction monitoring for that application in the Didit console.
- In a live application this can use your Didit credits. Say so and wait for a yes. Never state a price: link https://didit.me/pricing.

## 2. Screen

Arguments:

- `wallet_address` (required): the address exactly as the person gave it. It must match the chain's address format.
- `blockchain` (required): one of `BTC`, `ETH`, `LTC`, `XRP`, `BCH`, `DOGE`, `TRX`, `SOL`, `MATIC`, `BNB`, `USDT`, `USDC`. If the person did not say which, ask. Do not guess from the address.
- `direction` (optional): `inbound`, `outbound`, `deposit` or `withdrawal`.

## 3. Read the result

The result carries `risk_score`, `severity`, `sanctions_hit` and the source or destination of funds.

1. First line: severity, risk score, and whether there is a sanctions hit.
2. Then the main sources or destinations of funds, as the result lists them.
3. Say plainly that this is a risk signal for the person's own review, not a decision.

## 4. When to open a case

Suggest a case when there is a sanctions hit, a high severity, or the person says the wallet belongs to a customer under review.

- If the wallet belongs to a known customer, find them with `didit_vendor_user_search` or `didit_vendor_business_search` and open the case about them with `didit_case_create` (`subject` with `type` and `uuid`, the record's `didit_internal_id`).
- If a monitored transaction used this wallet, link it instead (`links` with `entity_type: "transaction"`).
- Confirm the title, priority and subject with the person before creating the case. See didit-tm-alerts-cases for working it.

To screen wallets on every transaction instead of one at a time, submit transactions with `include_crypto_screening` (see didit-tm-transactions).

## What good output looks like

- Severity, risk score and sanctions hit on the first line.
- The chain and address repeated back, so the person can check them.
- A clear question before a billable screening in a live application.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent or "correct" a wallet address, or guess the chain.
- Never treat a risk score as a final decision.
- Never state prices. Link https://didit.me/pricing.
