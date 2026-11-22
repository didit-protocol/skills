---
expect:
  session_id: string
  new_status: string
---

{
  "session_id": "{{input.session_id}}",
  "status": "{{input.new_status}}",
  "updated": true
}
