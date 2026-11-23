---
expect:
  country_code: string
---

{
  "request_id": "kyb-5520",
  "status": "Results found",
  "country_code": "{{input.country_code}}",
  "results": [
    {
      "company_name": "Northwind Trading Ltd",
      "registration_number": "09876543",
      "status": "Active"
    }
  ]
}
