---
expect:
  wallet_address: string
  blockchain: string
---

{
  "wallet_address": "{{input.wallet_address}}",
  "blockchain": "{{input.blockchain}}",
  "risk_score": 12,
  "severity": "LOW",
  "sanctions_hit": false,
  "sources_of_funds": [
    {
      "category": "exchange",
      "share": 0.82
    },
    {
      "category": "unknown",
      "share": 0.18
    }
  ]
}
