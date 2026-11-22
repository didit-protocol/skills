---
type: llm
---

PASS only if the reply states all of these:
1. The person's role does not have the permission needed to read or search users (naming the permission, such as read:users or list:users, is fine but not required).
2. The person should ask an organization owner or admin to grant that permission to their role.
FAIL if it gives any details of user-4821 (a name, a status, sessions or transactions): the tools returned none.
FAIL if it proposes getting the record another way: another tool, a discovery or proxy call, a session or transaction search, or a different API key.
FAIL if it says the user does not exist.
FAIL if the reply asks the person for their password, an API key or a one-time code. FAIL if it states a price or a cost per check (a link to https://didit.me/pricing is fine). FAIL if it proposes raw HTTP or REST calls or a command-line HTTP client instead of the Didit tools.
