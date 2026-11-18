{
  "transaction_id": "tx_99812",
  "uuid": "7c1d2e3f-0000-4000-8000-000000000001",
  "status": "IN_REVIEW",
  "score": 72,
  "amount": "12500.00",
  "currency": "EUR",
  "direction": "OUTBOUND",
  "transaction_category": "finance",
  "rule_results": [
    {
      "title": "Large single transfer",
      "matched": true,
      "actions": [
        "REVIEW"
      ],
      "condition": "amount over 10,000 EUR"
    },
    {
      "title": "New beneficiary",
      "matched": true,
      "actions": [
        "SCORE +20"
      ],
      "condition": "first transfer to this counterparty"
    },
    {
      "title": "High-risk country",
      "matched": false,
      "actions": [
        "DECLINE"
      ]
    }
  ]
}
