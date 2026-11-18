---
name: didit-tm-travel-rule
description: Runs Travel Rule compliance for crypto transfers in a Didit account (settings, VASP directory, counterparty contacts, wallet address book, messages, networks, sandbox tests). Use when the user mentions the Travel Rule with Didit, says "find a VASP", "counterparty VASP", "travel address", "add a wallet to the address book", "confirm wallet ownership", "UNCONFIRMED_OWNERSHIP", "message the other exchange", "cancel or resend a transfer", "which networks can we use", "due-diligence questionnaire", or "send a test inbound transfer".
---

# Travel Rule

Follow the rules of didit-tm-start first: call `didit_context_get`, pick the application and read sandbox or live from `mode`, never from its name. The hosted server lists 23 Travel Rule tools, such as `didit_travel_rule_get_settings`. When they are not in your tool list, reach them through the discovery tools if those are listed.

A Travel Rule transfer lives on a Didit transaction: the tools that act on one take `transaction_id`, the Didit transaction UUID. Find it with `didit_transaction_search` or read it with `didit_transaction_get` (see didit-tm-transactions). Outbound transfers start when a transaction is submitted; in a live application this can use your Didit credits (see didit-tm-transactions). Never state a price: link https://didit.me/pricing.

## 1. Settings

- `didit_travel_rule_get_settings` returns the VASP profile, thresholds and timeouts, the proof methods, `ownership_validation_mode`, `data_sharing_fields` and `matching_rules` per entity type, `disabled_networks`, each network's state, whether the application is listed in the Didit network (`didit_network`, with what is missing) and its travel address. Read it before any change.
- `didit_travel_rule_update_settings` is a partial update: send only the fields that change. Turning it on (`is_enabled: true`) needs a non-blank `legal_name`. `data_sharing_fields` and `matching_rules` replace the whole entity type they name, and a jurisdiction's rules can refuse a data-sharing choice that leaves out data it requires: show the old and the new value of each field and wait for a clear yes before calling it.
- Being discoverable (`is_discoverable`) also needs a live application, Travel Rule on, a legal name and a confirmed compliance email: report what `didit_network.missing` lists instead of guessing.

## 2. Find a counterparty VASP

- `didit_travel_rule_search_vasps`: `search` (name, trading name, LEI or domain), `network`, `jurisdiction`, `reachable`, `kind`, `limit`, `offset`. Each row lists `routes[]` with a status. Only a route with status `available` carries a transfer; a network listing alone is not a route. Say which routes are available.
- `didit_travel_rule_get_vasp`: `vasp_id`, for one entry with the same fields.
- Only `kind: directory` rows can be set as a transfer's counterparty or given contacts. A listed Didit customer (`kind: didit`) is reached by Didit on its own when the destination wallet is proven in its address book.

## 3. Counterparty contacts

- `didit_travel_rule_list_counterparty_contacts`: optional `vasp_id`, `limit`, `offset`. It shows the curated contacts and the application's own, with `is_invalid` and `invalid_reason` when an address bounced. The email rail uses them to reach a VASP.
- `didit_travel_rule_add_counterparty_contact`: `vasp_id` (a `kind: directory` row), `email`, optional `name`. The contact is private to this application. Repeat the VASP and the address and wait for the person to confirm.
- `didit_travel_rule_delete_counterparty_contact`: `contact_id`. Only the application's own contacts can be deleted, and it cannot be undone. Name the contact and wait for the person to confirm.

Mask contact emails when you list them: first letter and the domain.

## 4. Wallet address book and ownership

- `didit_travel_rule_list_wallet_addresses`: `limit`, `offset`. The wallets the application controls, with their ownership-verification state. Inbound internal transfers resolve against them.
- `didit_travel_rule_add_wallet_address`: `address`, optional `chain`, `holder_name`, `holder_vendor_data`, `entity_type`, `travel_address`, `self_declared`. With `self_declared: true` the entry is created already ownership-verified by self-declaration, so inbound transfers skip `UNCONFIRMED_OWNERSHIP`: say that before asking for agreement.
- `didit_travel_rule_update_wallet_address`: `entry_uuid` plus the holder fields to change.
- `didit_travel_rule_delete_wallet_address`: `entry_uuid`. The entry stops matching new transfers at once and the address is freed. Name the address and wait for the person to confirm.
- `didit_travel_rule_confirm_ownership`: `transaction_id`, `confirmed`. It decides a transfer waiting in `UNCONFIRMED_OWNERSHIP` (for example after the person reviewed a screenshot proof). `confirmed: true` verifies the address book entry and runs the name match; `false` declines both sides. The decision cannot be undone: state the transfer, the wallet and the decision, and wait for a clear yes before calling the tool.

## 5. Messages with the counterparty

- `didit_travel_rule_list_messages`: `transaction_id`. Messages and document requests on a transfer, oldest first. A document request is open while `fulfilled_at` is empty. Attachment download links expire: do not paste them as lasting links.
- `didit_travel_rule_send_message`: `transaction_id`, `kind` (`MESSAGE` or `DOCUMENT_REQUEST`), `body`, `requested_documents`, `reply_to`, `files`. Only transfers with another Didit customer or over email carry messages; network rails refuse them. To answer a document request, `reply_to` its id with files attached. The counterparty receives it at once and it cannot be recalled: show the person the exact message and wait for a clear yes before sending.

## 6. Act on a transfer

- `didit_travel_rule_transfer_action`: `transaction_id` plus exactly one of `payment_txn_id` (the on-chain hash, finishes a completed outbound transfer) or `action` (`cancel` any transfer that is not final, or `resend` to re-run routing after `COUNTERPARTY_VASP_NOT_FOUND`, `COUNTERPARTY_VASP_NOT_REACHABLE` or `NOT_ENOUGH_COUNTERPARTY_DATA`). Finishing and cancelling cannot be undone: say so and wait for the person to confirm.
- `didit_travel_rule_set_counterparty_vasp`: `transaction_id`, `vasp_id` (a `kind: directory` row). It sets the beneficiary VASP of an outbound transfer Didit could not route and re-runs the exchange. It sends the transfer's Travel Rule data to that VASP: name the VASP and its available route, and wait for a clear yes. The reply shows the queued state; read the transaction later for the outcome.

## 7. Networks and the questionnaire

- `didit_travel_rule_list_networks` returns each network's state for this application, with the reason. Only `own_membership` and `live_through_didit` route transfers. Report every state as returned and never present a network as reachable unless its state routes.
- `didit_travel_rule_request_network`: `network` (one of the values its schema lists). It asks to join on Didit's membership. It is refused on sandbox applications, and a request is not a connection: the participant turns active only when the network confirms. Name the network and wait for the person to confirm.
- `didit_travel_rule_get_network_questionnaire` returns the due-diligence questionnaire: status, saved answers, the reviewer's note and the history.
- `didit_travel_rule_update_network_questionnaire` saves answers while the status is `draft` or `changes_requested`. Send only the answers that change; a list such as `licences` is replaced whole. Each field ending in `_attested` is a statement on the organization's behalf: set one to `true` only after the person agreed to that exact statement.
- `didit_travel_rule_submit_network_questionnaire` sends the saved answers to Didit's review; they cannot be edited while in review. Show the saved answers and wait for the person to confirm before submitting.

## 8. Sandbox tests

- `didit_travel_rule_get_sandbox_scenarios` returns the Didit Test VASP that sandbox applications exchange with and its scenarios, each with the beneficiary name and wallet that select it on an outbound sandbox transfer. In sandbox nothing reaches a real VASP or network.
- `didit_travel_rule_trigger_test_inbound`: `beneficiary_wallet_address`, optional `scenario`, `chain`, `amount`, `currency`, `reference`. Sandbox applications only: check `mode` first. The application's own settings decide the outcome; on this trigger only `name_mismatch` changes it. Repeating a `reference` returns the first result. Say what will be sent and wait for a yes.

## What good output looks like

- The application and its mode stated once, read from `didit_context_get`.
- For a VASP: its name, kind, and which routes are available, in plain words.
- For networks: each state exactly as returned, with the ones that route marked.
- The exact change, message or decision shown before it runs, and a clear yes before any call that sends data to a counterparty or cannot be undone.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent a VASP id, wallet address, transaction id or questionnaire answer, and never set an attestation the person did not make.
- Never call a network reachable when its state does not route, or a VASP reachable without an available route.
- Never state prices. Link https://didit.me/pricing.
