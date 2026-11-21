---
expect:
  list_uuid: string
---

{
  "uuid": "entry-0001",
  "list_uuid": "{{input.list_uuid}}",
  "value": "{{input.value}}"
}
