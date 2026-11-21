#!/usr/bin/env python3
"""Offline checks for every plugin bundle under plugins/ and the repo's plugin marketplaces.

Stdlib only. Every content check runs twice: on the working tree and on HEAD extracted with
`git archive` (what a submission receives), so an expected plugin missing from HEAD fails.
Every generic check runs on every plugin folder; the `didit`-specific ones stay pinned to it.

    python3 tests/test_plugin_bundle.py
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PLUGIN_SKILLS = [
    "didit-connect",
    "didit-verify-people",
    "didit-review-queue",
    "didit-run-checks",
    "didit-verify-businesses",
    "didit-monitor-transactions",
    "didit-reports",
    "didit-workspace-admin",
]

# Every plugin folder and its exact skill set. A new folder under plugins/ must be added here.
EXPECTED_SKILLS = {
    "didit": PLUGIN_SKILLS,
    "didit-transaction-monitoring": [
        "didit-tm-start",
        "didit-tm-transactions",
        "didit-tm-rules",
        "didit-tm-wallet-screening",
        "didit-tm-alerts-cases",
        "didit-tm-investigator",
        "didit-tm-travel-rule",
    ],
    "didit-user-management": [
        "didit-users-start",
        "didit-users-records",
        "didit-users-businesses",
        "didit-users-lists",
        "didit-users-team",
    ],
    "didit-authentication": [
        "didit-auth-start",
        "didit-auth-sign-in-methods",
        "didit-auth-integrate",
        "didit-auth-events",
    ],
}
FOCUSED = [name for name in EXPECTED_SKILLS if name != "didit"]
START_SKILL = {
    "didit-transaction-monitoring": "didit-tm-start",
    "didit-user-management": "didit-users-start",
    "didit-authentication": "didit-auth-start",
}
WHICH_HEADING = "## Which Didit plugin should I install?"

MAX_FILES = 512
MAX_BYTES = 256 * 1024
IMAGE_SUFFIXES = {".png", ".svg"}
TEXT_SUFFIXES = {".md", ".json", ".txt"}

LAUNCHERS = re.compile(r"\b(npx|uvx|bunx|pnpm dlx|yarn dlx|pipx run|uv run)\b")
CURL = re.compile(r"curl ")
SECRETS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}"),
    re.compile(r"Bearer [A-Za-z0-9._-]{20,}"),
    re.compile(r"api_key\s*[=:]\s*['\"]?[A-Za-z0-9_-]{8,}", re.IGNORECASE),
]
SOLICIT = re.compile(
    r"\b(paste|enter|type|send|share|provide|give me|tell me|input)\s+(your|the|me your)\s+"
    r"(api[ _-]?key|password|passcode|one[- ]time code|otp|secret|token|credentials)",
    re.IGNORECASE,
)
EM_DASH = chr(0x2014)
TOOL_TOKEN = re.compile(r"\bdidit_[a-z0-9_]+\b")
DISCOVERY = {"didit_tool_search", "didit_tool_describe", "didit_tool_call_read", "didit_tool_call_write"}
# Tokens that look like tool names but are not: record fields (a Travel Rule settings field included)
# and the Flutter Authentication package.
NOT_TOOLS = {"didit_internal_id", "didit_internal_id_list", "didit_auth", "didit_network", "didit_test"}
AUTHENTICATION_SETUP_TOOLS = {
    "didit_authentication_get",
    "didit_authentication_method_set",
    "didit_authentication_settings_get",
    "didit_authentication_settings_update",
    "didit_authentication_onboarding_get",
    "didit_authentication_onboarding_update",
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_frontmatter(text: str, where: str) -> tuple[dict[str, str], str]:
    """Strict minimal parser: only `name` and `description`, each a one-line plain scalar."""
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        raise AssertionError(f"{where}: frontmatter must start on line 1 with ---")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(f"{where}: frontmatter is not closed with ---") from None
    fields: dict[str, str] = {}
    for raw in lines[1:end]:
        match = re.fullmatch(r"([a-z]+): (\S.*)", raw)
        if not match:
            raise AssertionError(f"{where}: unsupported frontmatter line {raw!r}")
        key, value = match.group(1), match.group(2).strip()
        if key not in {"name", "description"}:
            raise AssertionError(f"{where}: frontmatter key {key!r} is not allowed (only name, description)")
        if key in fields:
            raise AssertionError(f"{where}: duplicate frontmatter key {key!r}")
        if value[0] in "|>[{&*!%@`'\"" or value.endswith(":"):
            raise AssertionError(f"{where}: {key} must be a plain one-line scalar")
        if ": " in value or " #" in value:
            raise AssertionError(f"{where}: {key} contains ': ' or ' #', which YAML would not read as plain text")
        fields[key] = value
    if set(fields) != {"name", "description"}:
        raise AssertionError(f"{where}: frontmatter needs exactly name and description, got {sorted(fields)}")
    return fields, "\n".join(lines[end + 1 :])


def sections(markdown: str) -> list[str]:
    """Split markdown into heading sections (any heading level starts a new one)."""
    parts: list[str] = []
    current: list[str] = []
    for line in markdown.split("\n"):
        if re.match(r"#{1,6} ", line) and current:
            parts.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        parts.append("\n".join(current))
    return parts


def words_outside_fences(markdown: str) -> int:
    stripped = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'.-]*", stripped))


def bundle_problems(base: Path) -> list[str]:
    """File-level directory rules for one copy of the plugin folder."""
    problems: list[str] = []
    # evals/results/ holds local `claude plugin eval` output; .gitignore keeps it out of every commit.
    files = [p for p in base.rglob("*") if not p.relative_to(base).as_posix().startswith("evals/results")]
    regular = [p for p in files if p.is_file() or p.is_symlink()]
    if len(regular) > MAX_FILES:
        problems.append(f"{len(regular)} files, limit {MAX_FILES}")
    for path in files:
        rel = path.relative_to(base).as_posix()
        if path.is_symlink():
            problems.append(f"symlink: {rel}")
            continue
        if path.name == ".DS_Store":
            problems.append(f".DS_Store: {rel}")
        if path.is_dir():
            if path.parent == base and path.name in {"hooks", "agents", "bin", "commands"}:
                problems.append(f"top-level {path.name}/ is not allowed in v1: {rel}")
            continue
        suffix = path.suffix.lower()
        if path.name != "LICENSE" and suffix not in TEXT_SUFFIXES | IMAGE_SUFFIXES:
            problems.append(f"file type not allowed: {rel}")
        data = path.read_bytes()
        if suffix not in IMAGE_SUFFIXES or suffix == ".svg":
            if len(data) >= MAX_BYTES:
                problems.append(f"{rel} is {len(data)} bytes (limit {MAX_BYTES})")
        if data.startswith(b"version https://git-lfs"):
            problems.append(f"LFS pointer: {rel}")
        if suffix == ".png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                problems.append(f"{rel} is not a PNG")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel} is not UTF-8 text")
            continue
        if LAUNCHERS.search(text):
            problems.append(f"package launcher in {rel}: {LAUNCHERS.search(text).group(0)}")
        if CURL.search(text):
            problems.append(f"'curl ' in {rel}")
        for pattern in SECRETS:
            hit = pattern.search(text)
            if hit:
                problems.append(f"secret-looking string in {rel}: {hit.group(0)[:12]}...")
        hit = SOLICIT.search(text)
        if hit:
            problems.append(f"credential-soliciting phrase in {rel}: {hit.group(0)!r}")
        if EM_DASH in text:
            problems.append(f"em dash in {rel}")
    return problems


def mcp_problems(base: Path) -> list[str]:
    problems: list[str] = []
    data = load_json(base / ".mcp.json")
    servers = data.get("mcpServers", {})
    if list(servers) != ["didit"]:
        problems.append(f".mcp.json servers must be exactly ['didit'], got {list(servers)}")
    for name, server in servers.items():
        if server.get("type") != "http":
            problems.append(f"{name}: type must be http")
        url = server.get("url", "")
        if not url.startswith("https://"):
            problems.append(f"{name}: url must be absolute https")
        if "${" in json.dumps(server):
            problems.append(f"{name}: variable substitution is not allowed")
        if any(key in server for key in ("command", "args")):
            problems.append(f"{name}: a remote server entry must not launch a command")
    if servers.get("didit", {}).get("url") != "https://mcp.didit.me/mcp":
        problems.append("didit url must be https://mcp.didit.me/mcp")
    return problems


# Tools whose schema declares `confirm`. Kept by hand so a catalog change is noticed here.
CONFIRM_TOOLS = {
    "didit_case_manage",
    "didit_investigator_accept",
    "didit_investigator_batch_accept",
    "didit_investigator_override",
    "didit_investigator_question_answer",
    "didit_investigator_question_dismiss",
    "didit_investigator_rereview",
    "didit_org_create_api_key",
    "didit_session_batch_delete",
    "didit_session_delete",
    "didit_vendor_business_delete",
    "didit_vendor_user_delete",
}
# A sentence about getting the person's agreement (checked with backticked spans removed).
AGREEMENT = re.compile(
    r"(wait for (a clear yes|a yes|the person to (confirm|agree))"
    r"|ask (the person )?to confirm"
    r"|after (the person|they) (has |have )?(agreed|confirmed|said yes)"
    r"|after that (yes|agreement)"
    r"|(get|getting) the person's agreement"
    r"|the person's agreement)",
    re.IGNORECASE,
)
BACKTICKED = re.compile(r"`[^`\n]*`")
# Blanket rules that contradict the tool schemas.
BLANKET_RULES = [
    (re.compile(r"\b(pass|send)\w*\s+(both\s+)?`organization_id`\s+and\s+`application_id`\s+(on|to|with|in)\s+(every|all|later|each|any)\b", re.I),
     "tells the model to pass both scope ids on every call"),
    (re.compile(r"\b(always|every call)\b[^\n.]{0,20}\b(pass|send)\w*\s+(both\s+)?`organization_id`\s+and\s+`application_id`", re.I),
     "tells the model to always pass both scope ids"),
    (re.compile(r"\bpass\s+no\s+ids\b", re.I), "tells the model to pass no ids, which breaks tools that require them"),
    (re.compile(r"\b(tools|actions|changes|anything|everything)\b[^\n.]{0,80}\b(take|takes|need|needs|require|requires|get|gets)\s+`confirm(: true)?`", re.I),
     "attaches `confirm` to a class of actions instead of to tools that declare it"),
    (re.compile(r"\ball\s+(take|need|require)\s+`confirm", re.I), "attaches `confirm` to a class of actions"),
    (re.compile(r"\b(deletions?|deleting|deletes|overwrit\w+|irreversible|credentials?)\b[^\n.]{0,60}\b(take|takes|need|needs|require|requires)\s+`confirm", re.I),
     "attaches `confirm` to a class of actions"),
]
# Tools the hosted server does not list to customers (HOSTED_APP_EXCLUDED_TOOLS); a local stdio server has them.
LOCAL_ONLY_TOOLS = ("didit_org_reveal_application_api_key", "didit_org_top_up")
LOCAL_ONLY = re.compile(r"local (?:\(stdio\) )?server only", re.I)
# The rule for an application API key connection, word for word, in all four start skills.
API_KEY_RULE = (
    "If `didit_context_get` shows `connection.type: api_key`, this connection is one application with no person: "
    "member, role, API key, billing-detail (plan, payment methods, receipts), compliance and audit-log tools are not available; "
    "the credit balance (`didit_org_get_balance`) still is. Say so and point the person to sign in with OAuth for "
    "the missing ones."
)
# Measured live with Reader, Developer and Compliance Officer accounts: the context lists no applications for them.
ZERO_APPS_RULE = "If `didit_context_get` shows an organization with zero applications, do not conclude there are none."
ROLE_REFUSAL_RULE = "refused with `forbidden` (sometimes `missing_scope`)"
RECONNECT_RULE = "After a role change the person must reconnect Didit"
# Recipes whose person-only tools need a note in the same section.
PERSON_ONLY_SKILLS = {
    "didit": ["didit-workspace-admin", "didit-reports"],
    "didit-user-management": ["didit-users-team"],
}
PERSON_SIGN_IN_NOTE = "Needs a person sign-in"
ROLE_SENTENCE = "The list is the same for every role; a call your role does not allow is refused, with the missing permission in the error."
CONFIRM_TICK = re.compile(r"`confirm(: true)?`")
ARG_LINE_COLON = re.compile(r"^\s*(?:-|\d+\.)\s+`(didit_[a-z0-9_]+)`:\s*(.*)$")
ARG_LINE_WITH = re.compile(r"`(didit_[a-z0-9_]+)`\s+(?:with|takes|needs)\s+((?:`[^`]+`(?:\s*(?:,|and/or|and|or)\s*)?)+)")
ARG_TOKEN = re.compile(r"`([a-z][a-z0-9_]*)(?::[^`]*)?`")
BILLING_WORDS = re.compile(r"\b(credits|billed|billable|bills)\b", re.I)
BILLABLE_IN_SECTION = {"didit_transaction_create", "didit_transaction_screen_wallet"}
BILLABLE_IN_FILE = {
    "didit_session_create",
    "didit_verify_aml",
    "didit_verify_database",
    "didit_verify_face_match",
    "didit_verify_face_search",
    "didit_verify_id",
    "didit_verify_passive_liveness",
    "didit_verify_poa",
    "didit_verify_kyb_search",
}
# The routing rule, word for word, in all four start skills and in skills/didit-mcp-server.
ROUTING_RULE = (
    "Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional "
    "`organization_id` or `application_id` only when the context shows several organizations or applications, "
    "or when it returned no default for that id: then ask the person which organization or application to use "
    "and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy "
    "(`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside "
    "`arguments`, never next to `name`."
)
LIVE_BILLING = "In a live application this can use your Didit credits"
# Billing claims that overstate or understate charges.
BILLING_FORBIDDEN = [
    (re.compile(r"\b(every|each)\b[^.\n]{0,60}\b(costs?|is billed|are billed|uses?\s+(the organization's\s+)?(Didit\s+)?credits)\b", re.I),
     "says every action costs credits; say it can use credits"),
    (re.compile(r"\bfree\b(?! to test in| text| of charge)", re.I), "claims something is free; only 'sandbox applications are free to test in'"),
    (re.compile(r"\bnever bills?\b|\buse no Didit credits\b", re.I), "claims something never bills"),
]
# Displaying a webhook or destination URL in full (a secret can sit in its path or query).
FULL_URL_DISPLAY = re.compile(
    r"\b(show|display|print|echo)\w*\s+(the|its|each|their)\s+(full\s+)?(destination\s+|webhook\s+|slack\s+)?url\b(?!\s+masked)",
    re.I,
)
SHARED_README_SECTIONS = ("## Which Didit plugin should I install?", "## Shorter tool list (optional)")
CLAUDE_AI_STATUS = "(manual marketplace; directory listing pending)"
README_FORBIDDEN = [
    (re.compile(r"\bno binaries\b", re.I), "say 'no executable binaries': the icon is a binary file"),
    (re.compile(r"only the tools this plugin uses", re.I), "a toolset connection is a shorter tool list, not only this plugin's tools"),
]


# The conditional-instruction rule, word for word, in all four start skills and in didit-review-queue.
CONDITIONAL_RULE = (
    "An instruction given in advance or with a condition ('if it is only X, approve') is not agreement. "
    "Report what you found, say exactly what you would change and in which application (sandbox or live), "
    "then wait for a yes."
)
CONDITIONAL_RULE_SKILLS = {
    "didit": ["didit-connect", "didit-review-queue"],
    "didit-transaction-monitoring": ["didit-tm-start"],
    "didit-user-management": ["didit-users-start"],
    "didit-authentication": ["didit-auth-start"],
}
# A JSON example in a skill names its tool on the fence: ```json didit_tool_name
JSON_FENCE = re.compile(r"^([ \t]*)```json(?:[ \t]+(\S+))?[ \t]*\n(.*?)^[ \t]*```[ \t]*$", re.M | re.S)
# Nested shapes the catalog does not carry, kept by hand from the server's schemas (mcp/src/tools).
RULE_TOOLS = {"didit_transaction_rule_backtest", "didit_transaction_rule_create", "didit_transaction_rule_update"}
RULE_CONDITION_KEYS = {"field", "operator", "value", "value_type", "score", "group_index", "group_logic", "groups_logic"}
RULE_CONDITION_OPERATORS = {
    "eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "not_contains", "contains_any", "regex",
    "fuzzy_match", "exists", "is_not_empty", "is_not_null", "not_exists", "is_empty", "is_null",
}
RULE_AGGREGATION_KEYS = {"metric", "field", "operator", "value", "window", "filters"}
RULE_METRICS = {"count", "sum", "max", "min", "avg", "distinct_count", "unique_count"}
RULE_AGG_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte"}
RULE_SCOPE_KEYS = {"transaction_types", "directions", "action_types"}
RULE_ACTION_TYPES = {"add_score", "change_status", "add_tags", "add_note", "add_to_list", "open_case"}
# didit_questionnaire_create / _update form_elements items (live hosted schema): no `placeholder`,
# and `title` is an object of locale to text.
QUESTION_KEYS = {"element_type", "title", "is_required", "choices"}
QUESTION_TYPES = {
    "SHORT_TEXT", "LONG_TEXT", "PARAGRAPH", "DROPDOWN", "SINGLE_CHOICE", "MULTIPLE_CHOICE", "NUMBER", "IMAGE",
    "FILE_UPLOAD", "TIME", "EMAIL", "ADDRESS", "PHONE", "COUNTRY", "DATE_PICKER", "CONSENT", "SECTION_HEADER",
    "SEPARATOR", "HEADING", "REPEATABLE_GROUP",
}
QUESTIONNAIRE_TOOLS = {"didit_questionnaire_create", "didit_questionnaire_update"}
WORKFLOW_FEATURES = {
    "AGE_ESTIMATION", "AML", "BANK_VERIFICATION", "DATABASE_VALIDATION", "DOCUMENT_AI", "EMAIL_VERIFICATION",
    "FACE_MATCH", "GEOLOCATION", "IP_ANALYSIS", "KYB_DOCUMENTS", "KYB_KEY_PEOPLE", "KYB_REGISTRY", "LIVENESS", "NFC",
    "OCR", "PHONE_VERIFICATION", "PROOF_OF_ADDRESS", "QUESTIONNAIRE", "SIGNATURE",
}
# Arguments the schemas declare as arrays (a lone string is a wrong call).
ARRAY_ARGS = {
    "didit_org_invite_member": {"emails", "app_ids"},
    "didit_workflow_create": {"features"},
    "didit_questionnaire_create": {"form_elements"},
    "didit_travel_rule_send_message": {"requested_documents", "files"},
    "didit_case_create": {"links", "tags"},
    **{tool: {"conditions", "aggregation", "actions"} for tool in RULE_TOOLS},
}


def rule_definition_problems(args: dict) -> list[str]:
    problems = []
    for cond in args.get("conditions", []):
        if not isinstance(cond, dict) or not {"field", "operator"} <= set(cond):
            problems.append(f"condition needs field and operator: {cond}")
            continue
        problems += [f"condition has unknown key {k}" for k in sorted(set(cond) - RULE_CONDITION_KEYS)]
        if cond["operator"] not in RULE_CONDITION_OPERATORS:
            problems.append(f"condition operator {cond['operator']!r} is not in the schema")
    for agg in args.get("aggregation", []):
        if not isinstance(agg, dict) or not {"metric", "operator", "value", "window"} <= set(agg):
            problems.append(f"aggregation needs metric, operator, value and window: {agg}")
            continue
        problems += [f"aggregation has unknown key {k}" for k in sorted(set(agg) - RULE_AGGREGATION_KEYS)]
        if agg["metric"] not in RULE_METRICS:
            problems.append(f"aggregation metric {agg['metric']!r} is not in the schema")
        if agg["operator"] not in RULE_AGG_OPERATORS:
            problems.append(f"aggregation operator {agg['operator']!r} is not in the schema")
        if not isinstance(agg["value"], (int, float)) or isinstance(agg["value"], bool):
            problems.append(f"aggregation value must be a number: {agg['value']!r}")
        if not re.fullmatch(r"\d+[mhd]", str(agg["window"])):
            problems.append(f"aggregation window {agg['window']!r} is not <N>m, <N>h or <N>d")
    if "evaluation_mode" in args and args["evaluation_mode"] not in {"ALL", "ANY"}:
        problems.append(f"evaluation_mode {args['evaluation_mode']!r} is not ALL or ANY")
    scope = args.get("scope", {})
    problems += [f"scope has unknown key {k}" for k in sorted(set(scope) - RULE_SCOPE_KEYS)]
    problems += [f"scope direction {d!r} is not INBOUND or OUTBOUND" for d in scope.get("directions", []) if d not in {"INBOUND", "OUTBOUND"}]
    if "period_days" in args and not (isinstance(args["period_days"], int) and 1 <= args["period_days"] <= 365):
        problems.append(f"period_days {args['period_days']!r} is not 1 to 365")
    for action in args.get("actions", []):
        if action.get("type") not in RULE_ACTION_TYPES:
            problems.append(f"action type {action.get('type')!r} is not in the schema")
    return problems


def questionnaire_problems(args: dict) -> list[str]:
    problems = []
    for element in args.get("form_elements", []):
        if not isinstance(element, dict) or "element_type" not in element:
            problems.append(f"form element needs element_type: {element}")
            continue
        problems += [f"form element has unknown key {k}" for k in sorted(set(element) - QUESTION_KEYS)]
        if element["element_type"] not in QUESTION_TYPES:
            problems.append(f"form element type {element['element_type']!r} is not in the schema")
        if "title" in element and not isinstance(element["title"], dict):
            problems.append(f"form element title must be a locale object: {element['title']!r}")
    if "title" in args and not isinstance(args["title"], str):
        problems.append("the questionnaire title is a string")
    return problems


def fence_lead_problems(text: str) -> list[str]:
    """A ```json example right under a tool's own line (`- `tool`: ...`) is that tool's example."""
    problems = []
    for match in JSON_FENCE.finditer(text):
        before = [line for line in text[: match.start()].split("\n") if line.strip()]
        if not before:
            continue
        lead = re.match(r"^\s*(?:-\s+)?`(didit_[a-z0-9_]+)`:", before[-1])
        if lead and match.group(2) != lead.group(1):
            problems.append(f"```json {match.group(2)} follows the line of {lead.group(1)}")
    return problems


CONFIRM_RULE = "Send `confirm: true` only to a tool whose schema declares `confirm`, and only after the person agreed to that exact action."
CONFIRM_LIST_LEAD = "In this plugin's recipes those tools are:"
CONFIRM_OUTSIDE = ("Any other tool you reach by name or through discovery follows its own schema: "
                   "if it declares `confirm`, the same rule applies.")


def confirm_list(text: str) -> set[str] | None:
    """Tools a start skill lists as the `confirm` tools of its recipes (empty for "none").

    None when the binding rule, the list or the clause for tools outside the recipes is missing.
    """
    if CONFIRM_RULE not in text or CONFIRM_OUTSIDE not in text or CONFIRM_LIST_LEAD not in text:
        return None
    span = text.split(CONFIRM_LIST_LEAD, 1)[1].split(CONFIRM_OUTSIDE, 1)[0]
    return set(TOOL_TOKEN.findall(span))


def confirm_list_problems(listed: set[str] | None, used: set[str], known: dict[str, dict]) -> list[str]:
    """`listed` must equal the tools named in this plugin's skills that declare `confirm`.

    A tool that declares `confirm` but is outside the recipes is not listed: the clause for tools
    reached by name or discovery covers it.
    """
    if listed is None:
        return ["no binding `confirm` rule with a recipe list and a clause for tools outside the recipes"]
    declares = {name for name, tool in known.items() if tool["confirm"]}
    problems = [f"{t} is named in the plugin's skills and takes `confirm`, but the start list omits it" for t in sorted((used & declares) - listed)]
    problems += [f"{t} is in the start list but does not take `confirm`" for t in sorted(listed - declares)]
    return problems


def json_example_problems(text: str, tools: dict[str, dict]) -> list[str]:
    """Every ```json fence names a catalog tool, parses, and uses only arguments that tool declares (required ones included)."""
    problems = []
    for indent, tool, body in JSON_FENCE.findall(text):
        if not tool:
            problems.append("a ```json example must name its tool on the fence (```json didit_...)")
            continue
        if tool not in tools:
            problems.append(f"```json {tool}: not a catalog tool")
            continue
        try:
            args = json.loads(body)
        except json.JSONDecodeError as error:
            problems.append(f"```json {tool}: not valid JSON ({error})")
            continue
        if not isinstance(args, dict):
            problems.append(f"```json {tool}: the example must be an argument object")
            continue
        props, required = set(tools[tool]["properties"]), set(tools[tool]["required"])
        problems += [f"{tool} has no argument {k}" for k in sorted(set(args) - props)]
        problems += [f"{tool} example is missing required {k}" for k in sorted(required - set(args))]
        problems += [f"{tool}: {k} must be a list" for k in sorted(ARRAY_ARGS.get(tool, set()) & set(args)) if not isinstance(args[k], list)]
        if tool in RULE_TOOLS:
            problems += [f"{tool}: {p}" for p in rule_definition_problems(args)]
        if tool in QUESTIONNAIRE_TOOLS:
            problems += [f"{tool}: {p}" for p in questionnaire_problems(args)]
        if tool == "didit_workflow_create":
            problems += [f"{tool}: unknown feature {f.get('feature')!r}" for f in args.get("features", []) if f.get("feature") not in WORKFLOW_FEATURES]
    return problems + fence_lead_problems(text)


def conditional_rule_problems(texts: dict[str, str]) -> list[str]:
    return [f"{where}: missing the conditional-instruction rule" for where, text in texts.items() if CONDITIONAL_RULE not in text]


def strip_ticks(text: str) -> str:
    return BACKTICKED.sub(" ", text)


def confirm_section_problems(text: str, confirm_tools: set[str]) -> list[str]:
    """Every section that names a `confirm` tool needs a sentence about getting agreement (argument syntax does not count)."""
    problems = []
    for section in sections(text):
        used = confirm_tools & set(TOOL_TOKEN.findall(section))
        if used and not AGREEMENT.search(strip_ticks(section)):
            problems.append(f"{section.split(chr(10), 1)[0]!r}: {sorted(used)} without a sentence about the person's agreement")
    return problems


def blanket_problems(text: str) -> list[str]:
    problems = []
    for number, line in enumerate(text.split("\n"), 1):
        for pattern, why in BLANKET_RULES:
            if pattern.search(line):
                problems.append(f"line {number}: {why}: {line.strip()[:120]}")
    return problems


def confirm_attach_problems(text: str, confirm_tools: set[str]) -> list[str]:
    """A line that mentions `confirm` may only name tools that declare it (unless it says the tool takes none)."""
    problems = []
    for number, line in enumerate(text.split("\n"), 1):
        for sentence in re.split(r"(?<=[.;])\s+", line):
            if not CONFIRM_TICK.search(sentence):
                continue
            for tool in sorted(set(TOOL_TOKEN.findall(sentence)) - NOT_TOOLS - confirm_tools):
                if re.search(rf"`{tool}`[^.\n]*\b(takes no|does not declare|has no)\b[^.\n]*`confirm", sentence):
                    continue
                problems.append(f"line {number}: `confirm` next to {tool}, which does not declare it")
    return problems


def arg_pair_problems(text: str, props: dict[str, set[str]]) -> list[str]:
    """`tool`: `arg`, ... and `tool` with `arg` pairs must name arguments the tool declares.

    Only backticked names that are an argument of some catalog tool are checked, so enum values
    and response fields in the same clause are left alone. Parentheses are dropped first.
    """
    union = set().union(*props.values())
    problems = []
    for number, line in enumerate(text.split("\n"), 1):
        pairs: list[tuple[str, str]] = []
        match = ARG_LINE_COLON.match(line)
        if match:
            clause = re.split(r"\.\s", re.sub(r"\([^)]*\)", " ", match.group(2)), maxsplit=1)[0]
            clause = re.split(r"`[a-z_]+`\s+with\s+`|\beach\b", clause, maxsplit=1)[0]  # nested object fields
            pairs += [(match.group(1), arg) for arg in ARG_TOKEN.findall(clause)]
        for tool, args in ARG_LINE_WITH.findall(re.sub(r"\([^)]*\)", " ", line)):
            pairs += [(tool, arg) for arg in ARG_TOKEN.findall(args)]
        for tool, arg in pairs:
            if tool in props and arg in union and arg not in props[tool]:
                problems.append(f"line {number}: {tool} has no argument {arg}")
    return problems


def readme_problems(text: str) -> list[str]:
    return [why for pattern, why in README_FORBIDDEN if pattern.search(text)]


def billing_problems(text: str) -> list[str]:
    problems = []
    for number, line in enumerate(text.split("\n"), 1):
        for pattern, why in BILLING_FORBIDDEN:
            if pattern.search(line):
                problems.append(f"line {number}: {why}: {line.strip()[:120]}")
    return problems


def full_url_problems(text: str) -> list[str]:
    return [f"line {n}: shows a URL in full: {line.strip()[:120]}"
            for n, line in enumerate(text.split("\n"), 1) if FULL_URL_DISPLAY.search(line)]


def local_only_problems(text: str) -> list[str]:
    """Every sentence (or table cell) that names a local-only tool says it is local server only."""
    problems = []
    for line in text.split("\n"):
        for cell in line.split("|"):
            for sentence in re.split(r"(?<=[.!?])\s+", cell):
                named = [tool for tool in LOCAL_ONLY_TOOLS if tool in sentence]
                if named and not LOCAL_ONLY.search(sentence):
                    problems.append(f"{', '.join(named)} outside a 'local server only' sentence: {sentence.strip()[:120]}")
    return problems


def person_note_problems(text: str, person_only: set[str]) -> list[str]:
    """A section that names a tool absent from an API key connection carries the person sign-in note."""
    problems = []
    for section in sections(text):
        missing = sorted(person_only & set(TOOL_TOKEN.findall(section)))
        if missing and PERSON_SIGN_IN_NOTE not in section:
            problems.append(f"{section.split(chr(10), 1)[0]}: {', '.join(missing)} without '{PERSON_SIGN_IN_NOTE}'")
    return problems


def readme_section(text: str, heading: str) -> str:
    """The section from `heading` up to the next level-2 heading (or the end)."""
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end + 1]


class Tree:
    """One copy of the repository: the working tree, or HEAD extracted from git."""

    def __init__(self, root: Path, label: str):
        self.root = root
        self.label = label
        self.plugins = root / "plugins"
        self.plugin = self.plugins / "didit"
        self.rest = root / "skills"
        self.catalog_path = self.plugin / "tests" / "tool-catalog.json"
        self.prompts = self.plugin / "tests" / "prompts.md"
        self._catalog = None

    def plugin_dirs(self) -> list[Path]:
        return sorted(p for p in self.plugins.iterdir() if p.is_dir())

    def catalog(self) -> dict:
        if self._catalog is None:
            self._catalog = load_json(self.catalog_path)
        return self._catalog

    def known_tools(self) -> dict[str, dict]:
        tools: dict[str, dict] = {}
        for profile in self.catalog()["profiles"].values():
            for tool in profile.get("tools", []):
                tools.setdefault(tool["name"], tool)
        return tools

    def skill_texts(self, base: Path) -> list[tuple[str, str]]:
        """(where, text) for every SKILL.md, every skill's references/*.md and, last, the prompts file of one plugin."""
        out = []
        for name in EXPECTED_SKILLS[base.name]:
            out.append((f"{base.name}/skills/{name}/SKILL.md", (base / "skills" / name / "SKILL.md").read_text(encoding="utf-8")))
            for ref in sorted((base / "skills" / name).glob("references/*.md")):
                out.append((f"{base.name}/skills/{name}/references/{ref.name}", ref.read_text(encoding="utf-8")))
        out.append((f"{base.name}/tests/prompts.md", (base / "tests" / "prompts.md").read_text(encoding="utf-8")))
        return out


WORKING = Tree(ROOT, "working tree")
_COMMITTED: list = []


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)


def committed_tree() -> Tree:
    """HEAD extracted once with `git archive` (what a submission from the repo receives)."""
    if not _COMMITTED:
        if shutil.which("git") is None or git("rev-parse", "--verify", "HEAD").returncode != 0:
            raise unittest.SkipTest("git or HEAD not available")
        archive = git("archive", "--format=tar", "HEAD")
        if archive.returncode != 0:
            raise AssertionError(archive.stderr.decode())
        tmp = tempfile.TemporaryDirectory()
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            for member in tar.getmembers():
                if member.issym() or member.islnk():
                    raise AssertionError(f"link in HEAD: {member.name}")
            tar.extractall(tmp.name)
        _COMMITTED.extend([Tree(Path(tmp.name), "HEAD"), tmp])
    return _COMMITTED[0]


class TreeCase(unittest.TestCase):
    tree: Tree = WORKING

    @property
    def t(self) -> Tree:
        return self.tree


class LayoutTests(TreeCase):
    def test_plugin_folders_are_known(self):
        # In HEAD this also fails when an expected plugin was never committed.
        self.assertEqual([p.name for p in self.t.plugin_dirs()], sorted(EXPECTED_SKILLS))


class ManifestTests(TreeCase):
    def test_every_manifest_is_valid_json(self):
        paths = [
            self.t.root / ".claude-plugin" / "marketplace.json",
            self.t.root / ".agents" / "plugins" / "marketplace.json",
            *self.t.plugins.rglob("*.json"),
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(self.t.root).as_posix()):
                load_json(path)

    def test_no_root_plugin_json(self):
        self.assertFalse((self.t.root / ".claude-plugin" / "plugin.json").exists())

    def test_host_manifests_agree(self):
        didit = load_json(self.t.plugin / ".claude-plugin" / "plugin.json")
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                claude = load_json(base / ".claude-plugin" / "plugin.json")
                codex = load_json(base / ".codex-plugin" / "plugin.json")
                cursor = load_json(base / ".cursor-plugin" / "plugin.json")
                for key in ("name", "version", "description"):
                    self.assertEqual(claude[key], codex[key], key)
                    self.assertEqual(claude[key], cursor[key], key)
                self.assertEqual(claude["name"], base.name)
                self.assertEqual(claude["version"], "1.1.2")
                self.assertTrue(claude.get("displayName"))
                self.assertLessEqual(len(claude["description"]), 200)
                self.assertEqual(claude["license"], "MIT")
                self.assertEqual(claude["mcpServers"], "./.mcp.json")
                self.assertTrue((base / claude["icon"]).is_file())
                for key in ("author", "repository", "icon", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"):
                    self.assertEqual(claude[key], didit[key], key)
                for host in (codex, cursor):
                    self.assertTrue((base / host["skills"]).is_dir())
                    self.assertTrue((base / host["mcpServers"]).is_file())
                for key in ("composerIcon", "logo"):
                    self.assertTrue((base / codex["interface"][key]).is_file(), key)
                self.assertTrue((base / cursor["logo"]).is_file())

    def _entries(self, market: dict) -> dict[str, dict]:
        names = [entry["name"] for entry in market["plugins"]]
        self.assertEqual(len(names), len(set(names)), f"duplicate marketplace entries: {names}")
        sources = [json.dumps(entry["source"], sort_keys=True) for entry in market["plugins"]]
        self.assertEqual(len(sources), len(set(sources)), "two marketplace entries share a source")
        return {entry["name"]: entry for entry in market["plugins"]}

    def test_claude_marketplace_resolves(self):
        market = load_json(self.t.root / ".claude-plugin" / "marketplace.json")
        self.assertEqual(market["name"], "didit")
        entries = self._entries(market)
        self.assertEqual(set(entries), set(EXPECTED_SKILLS) | {"didit-api"})
        for entry in entries.values():
            self.assertTrue((self.t.root / entry["source"]).is_dir(), entry["source"])
        for name in EXPECTED_SKILLS:
            with self.subTest(plugin=name):
                entry = entries[name]
                self.assertEqual(entry["source"], f"./plugins/{name}")
                self.assertEqual(entry["version"], "1.1.2")
                manifest = load_json(self.t.plugins / name / ".claude-plugin" / "plugin.json")
                self.assertEqual(entry["description"], manifest["description"])
                self.assertTrue(entry.get("category"))
                self.assertTrue(entry.get("keywords"))
        api = entries["didit-api"]
        self.assertEqual(api["source"], "./")
        self.assertIs(api["strict"], False)
        self.assertEqual(api["version"], "5.2.1")
        listed = api["skills"]
        self.assertEqual(len(listed), len(set(listed)), "duplicate skills in didit-api")
        rest = sorted(p.parent.name for p in self.t.rest.glob("*/SKILL.md"))
        self.assertEqual(sorted(Path(s).name for s in listed), rest)
        for skill in listed:
            self.assertTrue((self.t.root / skill / "SKILL.md").is_file(), skill)

    def test_codex_marketplace_resolves(self):
        market = load_json(self.t.root / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual(market["name"], "didit")
        entries = self._entries(market)
        self.assertEqual(set(entries), set(EXPECTED_SKILLS))
        shape = {key: value for key, value in entries["didit"].items() if key not in {"name", "source"}}
        for name, entry in entries.items():
            with self.subTest(plugin=name):
                self.assertEqual(entry["source"], {"source": "local", "path": f"./plugins/{name}"})
                self.assertTrue((self.t.root / entry["source"]["path"]).is_dir())
                self.assertEqual({k: v for k, v in entry.items() if k not in {"name", "source"}}, shape)

    def test_mcp_server_entry(self):
        reference = (self.t.plugin / ".mcp.json").read_bytes()
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                self.assertEqual(mcp_problems(base), [])
                self.assertEqual((base / ".mcp.json").read_bytes(), reference, "must be identical to plugins/didit/.mcp.json")

    def test_no_empty_gitmodules(self):
        self.assertFalse((self.t.root / ".gitmodules").exists())


class SkillTests(TreeCase):
    def test_skill_set_and_frontmatter(self):
        for base in self.t.plugin_dirs():
            skills = EXPECTED_SKILLS[base.name]
            found = sorted(p.name for p in (base / "skills").iterdir() if p.is_dir())
            self.assertEqual(found, sorted(skills), base.name)
            for name in skills:
                path = base / "skills" / name / "SKILL.md"
                with self.subTest(plugin=base.name, skill=name):
                    text = path.read_text(encoding="utf-8")
                    fields, _ = parse_frontmatter(text, name)
                    self.assertEqual(fields["name"], name)
                    self.assertLessEqual(len(fields["description"]), 600)
                    self.assertNotIn("<", fields["description"])
                    self.assertNotIn("$", fields["description"])
                    self.assertLessEqual(len(text.rstrip("\n").split("\n")), 200)
                    self.assertIn("## What good output looks like", text)
                    self.assertIn("## Do not", text)
                    self.assertIn("https://didit.me/pricing", text)

    def test_didit_has_eight_skills(self):
        self.assertEqual(len(PLUGIN_SKILLS), 8)

    def test_skill_names_unique_across_repo(self):
        rest = {p.parent.name for p in self.t.rest.glob("*/SKILL.md")}
        self.assertEqual(len(rest), 20)
        seen: dict[str, str] = {}
        for plugin, skills in EXPECTED_SKILLS.items():
            for name in skills:
                with self.subTest(skill=name):
                    self.assertNotIn(name, seen, f"{name} is in {seen.get(name)} and {plugin}")
                    self.assertNotIn(name, rest, f"{name} collides with a REST skill")
                    seen[name] = plugin

    def test_every_tool_exists_in_catalog(self):
        # The local-only tools are not in the hosted catalog; test_local_only_tools_are_named_only_as_local guards them.
        known = {**self.t.known_tools(), **{name: {} for name in LOCAL_ONLY_TOOLS}}
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base):
                for token in sorted(set(TOOL_TOKEN.findall(text)) - NOT_TOOLS):
                    with self.subTest(file=where, tool=token):
                        self.assertIn(token, known)

    def test_confirm_tool_list_matches_catalog(self):
        known = self.t.known_tools()
        self.assertEqual({name for name, tool in known.items() if tool["confirm"]}, CONFIRM_TOOLS)
        self.assertEqual({name for name, tool in known.items() if "confirm" in tool["properties"]}, CONFIRM_TOOLS)

    def test_confirm_tools_need_agreement(self):
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                with self.subTest(file=where):
                    self.assertEqual(confirm_section_problems(text, CONFIRM_TOOLS), [])

    def test_confirm_only_on_tools_that_declare_it(self):
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base):
                with self.subTest(file=where):
                    self.assertEqual(confirm_attach_problems(text, CONFIRM_TOOLS), [])

    def test_no_blanket_rules(self):
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base):
                with self.subTest(file=where):
                    self.assertEqual(blanket_problems(text), [])

    def test_tool_argument_pairs(self):
        props = {name: set(tool["properties"]) for name, tool in self.t.known_tools().items()}
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                with self.subTest(file=where):
                    self.assertEqual(arg_pair_problems(text, props), [])

    def test_json_examples_match_the_catalog(self):
        tools = self.t.known_tools()
        seen = 0
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                seen += len(JSON_FENCE.findall(text))
                with self.subTest(file=where):
                    self.assertEqual(json_example_problems(text, tools), [])
        self.assertGreater(seen, 0)

    def test_start_skill_confirm_list_matches_catalog(self):
        """Each start skill lists exactly the tools named in this plugin's skills that declare `confirm`."""
        known = self.t.known_tools()
        starts = {"didit": "didit-connect", **START_SKILL}
        for base in self.t.plugin_dirs():
            used: set[str] = set()
            for _, text in self.t.skill_texts(base)[:-1]:
                used |= set(TOOL_TOKEN.findall(text))
            start = (base / "skills" / starts[base.name] / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(plugin=base.name):
                self.assertEqual(confirm_list_problems(confirm_list(start), used, known), [])

    def test_confirm_tool_outside_the_recipes(self):
        """The umbrella plugin's hosted connection exposes `confirm` tools its recipes never name; the start skill must allow them by schema."""
        known = self.t.known_tools()
        base = self.t.plugins / "didit"
        used: set[str] = set()
        for _, text in self.t.skill_texts(base)[:-1]:
            used |= set(TOOL_TOKEN.findall(text))
        start = (base / "skills" / "didit-connect" / "SKILL.md").read_text(encoding="utf-8")
        listed = confirm_list(start)
        for tool in ("didit_investigator_accept", "didit_session_batch_delete"):
            with self.subTest(tool=tool):
                self.assertTrue(known[tool]["confirm"])
                self.assertNotIn(tool, used)
                self.assertNotIn(tool, listed)
        self.assertIn(CONFIRM_OUTSIDE, start)
        self.assertNotIn("Never add `confirm` to any other tool", start)


    def test_conditional_instruction_is_not_agreement(self):
        texts = {}
        for plugin, skills in CONDITIONAL_RULE_SKILLS.items():
            for skill in skills:
                texts[f"{plugin}/{skill}"] = (self.t.plugins / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(conditional_rule_problems(texts), [])

    def test_rule_definition_is_taught(self):
        for plugin, skill in (("didit", "didit-monitor-transactions"), ("didit-transaction-monitoring", "didit-tm-rules")):
            text = (self.t.plugins / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("### Rule definition", text)
                self.assertIn("`period_days: 90`", text)
                self.assertIn("10,000 most recent transactions", text)
                self.assertIn("A back-test is a read, so it needs no agreement", text)
                self.assertGreaterEqual(text.count("```json didit_transaction_rule_backtest"), 3)

    def test_references_are_mentioned(self):
        for base in self.t.plugin_dirs():
            for name in EXPECTED_SKILLS[base.name]:
                skill = (base / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                for ref in (base / "skills" / name).glob("references/*.md"):
                    with self.subTest(file=ref.name, skill=name):
                        self.assertIn(f"references/{ref.name}", skill)

    def test_billing_notice_before_billable_calls(self):
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                tools = set(TOOL_TOKEN.findall(text))
                if tools & BILLABLE_IN_FILE:
                    with self.subTest(file=where):
                        self.assertRegex(text, BILLING_WORDS)
                        self.assertIn("live application", text)
                for section in sections(text):
                    used = BILLABLE_IN_SECTION & set(TOOL_TOKEN.findall(section))
                    if used and re.search(r"`(" + "|".join(sorted(used)) + r")`\s+(records|sends|checks|submits)", section):
                        with self.subTest(file=where, section=section.split("\n", 1)[0]):
                            self.assertRegex(section, BILLING_WORDS)
                            self.assertIn("https://didit.me/pricing", section)

    def test_billing_wording(self):
        """Billable files say charges can apply, never that every action costs or that anything is free."""
        for base in self.t.plugin_dirs():
            texts = self.t.skill_texts(base) + [(f"{base.name}/README.md", (base / "README.md").read_text(encoding="utf-8"))]
            for where, text in texts:
                with self.subTest(file=where):
                    self.assertEqual(billing_problems(text), [])
                    if where.endswith("SKILL.md") and set(TOOL_TOKEN.findall(text)) & (BILLABLE_IN_FILE | BILLABLE_IN_SECTION):
                        self.assertIn(LIVE_BILLING, text)

    def test_urls_are_never_shown_in_full(self):
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                with self.subTest(file=where):
                    self.assertEqual(full_url_problems(text), [])
        events = (self.t.plugins / "didit-authentication" / "skills" / "didit-auth-events" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("never show it in full", events)
        self.assertIn("masked", events)

    def test_authentication_token_and_logout_contract(self):
        integrate = (self.t.plugins / "didit-authentication" / "skills" / "didit-auth-integrate" / "SKILL.md").read_text(encoding="utf-8")
        sdk = (self.t.rest / "didit-sdk-integration" / "SKILL.md").read_text(encoding="utf-8")
        # The tokens page documents one access token format: an ES256 JWT verified offline against the JWKS.
        self.assertIn("depends on the application's Authentication runtime as documented", re.sub(r"\s+", " ", sdk))
        self.assertIn("The access token is a JWT with header `alg: ES256` and `typ: at+jwt`", integrate)
        self.assertNotIn("Opaque access token", integrate)
        self.assertNotIn("Authentication runtime", integrate)
        self.assertIn("the current tokens page with `didit_docs_search`", integrate)
        self.assertIn("Local sign-out", integrate)
        self.assertIn("revocation is not confirmed", integrate)
        self.assertIn("No answer to the refresh made for sign-out", integrate)
        self.assertIn("Never resend it", integrate)
        self.assertNotIn("A `429`, a `503` or no answer means revocation is not confirmed: say so, retry", integrate)
        self.assertNotIn("the session is already over", integrate)
        self.assertNotIn("do not decode it as a JWT or invent JWKS", sdk)

    def test_mcp_server_skill_contracts(self):
        text = (self.t.rest / "didit-mcp-server" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(ROUTING_RULE, text)
        for tool in ("didit_session_search", "didit_transaction_search", "didit_case_search",
                     "didit_vendor_user_search", "didit_vendor_business_search", "didit_workflow_search"):
            self.assertIn(f"`{tool}`", text)
        self.assertNotIn("the `*_search` tools", text)
        self.assertNotRegex(text, r"`(sar|file_sar)`")
        self.assertIn('action `resolve` with `data.status: "SAR_FILED"`', text)
        self.assertIn("`didit_session_delete` (one session): `session_id` and `confirm: true`", text)
        self.assertIn("`didit_session_batch_delete` (several sessions): `session_numbers`", text)
        self.assertIn("only when the tool declares `confirm` and the error names it", text)
        self.assertIn("On the hosted server `didit_org_create_api_key` also returns the new key's secret once", text)
        self.assertNotIn("API keys and webhook secrets are redacted in what tools read", text)
        self.assertNotIn("Nothing else is redacted", text)  # other handlers redact more (imports, rule values)
        self.assertIn("treat any credential-looking value in a result as sensitive", text)
        self.assertIn("printf '%s' \"$REFRESH_TOKEN\" | curl", text)
        self.assertIn("for Slack, the posting URL in `value`", text)
        self.assertIn("host plus the last 4 characters", text)
        # No secret in process arguments: no shell-expanded header, no token in curl or `-e` arguments.
        self.assertNotRegex(text, r"(?m)^claude mcp add .*(\$DIDIT_|-e DIDIT_ACCESS_TOKEN=)")
        self.assertNotIn('"token=<refresh-token>"', text)
        self.assertIn("--data-urlencode 'token@-'", text)
        self.assertIn('"x-api-key": "${DIDIT_API_KEY}"', text)
        self.assertIn("`didit_org_reveal_application_api_key`", text)
        self.assertIn("`didit_org_top_up` and `didit_org_reveal_application_api_key` are local server only; on the hosted server "
                      "a new key is created with `didit_org_create_api_key`, and credit is added in the Didit console.", text)
        self.assertNotIn("is listed on the hosted server", text)
        self.assertIn(ROLE_SENTENCE, text)
        self.assertIn("178 on an API key connection", text)
        self.assertNotIn("208", text)

    def test_local_only_tools_are_named_only_as_local(self):
        """No skill or README tells an assistant to call the two local-only tools on a hosted connection."""
        files = [self.t.root / "README.md", *sorted(self.t.rest.glob("*/SKILL.md")), *sorted(self.t.rest.glob("*/references/*.md"))]
        for base in self.t.plugin_dirs():
            files.append(base / "README.md")
            files += sorted((base / "skills").rglob("*.md"))
        for path in files:
            with self.subTest(file=path.relative_to(self.t.root).as_posix()):
                self.assertEqual(local_only_problems(path.read_text(encoding="utf-8")), [])
        self.assertEqual(local_only_problems("Call `didit_org_top_up` with an amount."), [
            "didit_org_top_up outside a 'local server only' sentence: Call `didit_org_top_up` with an amount."])

    def test_api_key_rule_in_start_skills(self):
        starts = {"didit": "didit-connect", **START_SKILL}
        for plugin, skill in starts.items():
            text = (self.t.plugins / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn(API_KEY_RULE, text)
                self.assertNotIn("tools your role may use are listed", text)
                if plugin != "didit-authentication":
                    self.assertIn(ROLE_SENTENCE, text)

    def test_person_only_recipes_are_marked(self):
        profiles = self.t.catalog()["profiles"]
        person_only = {t["name"] for t in profiles["all"]["tools"]} - {t["name"] for t in profiles["api_key_all"]["tools"]}
        for plugin, skills in PERSON_ONLY_SKILLS.items():
            for skill in skills:
                text = (self.t.plugins / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                with self.subTest(skill=skill):
                    self.assertTrue(person_only & set(TOOL_TOKEN.findall(text)), "no person-only tool named")
                    self.assertEqual(person_note_problems(text, person_only), [])
        self.assertEqual(person_note_problems("## 1. Members\n\n`didit_org_list_members` lists members.", person_only),
                         ["## 1. Members: didit_org_list_members without 'Needs a person sign-in'"])

    def test_focused_plugins_skip_business_update(self):
        # No recipe uses it (its route does not exist as coded); prompts.md may list it as forbidden.
        for name in FOCUSED:
            for where, text in self.t.skill_texts(self.t.plugins / name)[:-1]:
                with self.subTest(file=where):
                    self.assertNotRegex(text, r"\bdidit_vendor_business_update\b(?!_)")

    def test_catalog_profiles(self):
        profiles = self.t.catalog()["profiles"]
        full = {tool["name"]: tool for tool in profiles["all"]["tools"]}
        read_only = profiles["all_read_only"]["tools"]
        core = {tool["name"] for tool in profiles["core"]["tools"]}
        self.assertTrue(read_only, "all_read_only is empty")
        # The hosted server as measured on 2026-11-21 (v5.1.79) with a new customer account (organization owner, not staff).
        self.assertEqual(len(full), 212)
        self.assertEqual(len(core), 29)
        self.assertEqual(len(read_only), 100)
        expected = {
            "all": (212, 100, 78, 34),
            "core": (29, 22, 3, 4),
            "all_read_only": (100, 100, 0, 0),
            "api_key_all": (178, 81, 66, 31),
            "api_key_core": (27, 21, 3, 3),
            "api_key_read_only": (81, 81, 0, 0),
        }
        self.assertEqual(set(profiles), set(expected))
        for name, profile in profiles.items():
            with self.subTest(profile=name):
                types = [tool["type"] for tool in profile["tools"]]
                counts = (len(types), types.count("read"), types.count("write"), types.count("destructive"))
                self.assertEqual(counts, expected[name])
                self.assertEqual((profile["total"], profile["read"], profile["write"], profile["destructive"]), expected[name])
                names = {tool["name"] for tool in profile["tools"]}
                self.assertEqual(names & set(LOCAL_ONLY_TOOLS), set(), "a local-only tool is listed")
                self.assertEqual([n for n in names if n.startswith("didit_staff")], [], "staff-only tools in the catalog")
        api_key = {tool["name"] for tool in profiles["api_key_all"]["tools"]}
        self.assertTrue(api_key <= set(full))
        person_only = set(full) - api_key
        self.assertEqual(len(person_only), 34)
        # The profile's key is the application's own key, which Authentication setup refuses by design (only a
        # named key with the authentication scope may set it up), so the server lists no setup tool for it.
        self.assertTrue(AUTHENTICATION_SETUP_TOOLS <= person_only)
        for name in ("didit_org_list_members", "didit_org_create_api_key", "didit_billing_get_plan",
                     "didit_compliance_requirements", "didit_audit_log_list", "didit_workflow_build_graph"):
            self.assertIn(name, person_only)
        self.assertIn("didit_org_get_balance", api_key)
        travel = {n for n in full if n.startswith("didit_travel_rule_")}
        self.assertEqual(len(travel), 23)
        for tool in read_only:
            with self.subTest(tool=tool["name"]):
                self.assertEqual(tool["type"], "read")
                self.assertIn(tool["name"], full)
                self.assertEqual(full[tool["name"]]["type"], "read")
        self.assertTrue(DISCOVERY <= core, "core profile should list the discovery tools")
        self.assertIn("didit_context_get", core)
        self.assertEqual({tool["name"] for tool in read_only} & DISCOVERY, set(), "discovery tools appear on all_read_only")
        self.assertEqual(set(full) & DISCOVERY, set(), "discovery tools appear when every toolset loads")
        for name, profile in profiles.items():
            names = [tool["name"] for tool in profile["tools"]]
            self.assertEqual(len(names), len(set(names)), f"duplicate tools in {name}")

    def test_read_only_and_discovery_wording(self):
        connect = (self.t.plugin / "skills" / "didit-connect" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Call `didit_context_get` first",
            "only when they are themselves in your tool list",
            "no write tool and no discovery tool is listed",
            "reconnect without `read_only`",
            "ask an organization admin",
            "never attempt a proxy call",
            "Never decide it from an application's name",
            "`confirm: true`",
            "`didit_docs_search`",
            "?toolsets=core",
            "read_only=true",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, connect)

    def test_start_skills_share_the_rules(self):
        starts = {"didit": "didit-connect", **START_SKILL}
        for plugin, start in starts.items():
            text = (self.t.plugins / plugin / "skills" / start / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=start):
                if plugin != "didit":
                    self.assertLessEqual(len(text.rstrip("\n").split("\n")), 70)
                for phrase in (
                    "Call `didit_context_get` first",
                    "A default is present only when there is exactly one",
                    "could not be listed leaves `default_application_id` out",
                    "establish the target before any change",
                    "Never decide it from an application's name",
                    "say the environment is unknown",
                    "Always send the ids a tool requires",
                    "only when the context shows several organizations or applications",
                    "or when it returned no default for that id",
                    "Never send an id the tool does not declare",
                    "inside `arguments`, never next to `name`",
                    "only when they are themselves in your tool list",
                    "proxy call",
                    "wait for a clear yes before calling the tool",
                    "`confirm: true`",
                    CONFIRM_RULE,
                    CONFIRM_OUTSIDE,
                    "a password, an API key or a one-time code",
                    "`didit_docs_search`",
                    "https://didit.me/pricing",
                ):
                    self.assertIn(phrase, text)
                self.assertIn(ROUTING_RULE, text)
                for skill in EXPECTED_SKILLS[plugin]:
                    if skill != start:
                        self.assertIn(skill, text, f"{start} must route to {skill}")
                self.assertNotIn("Never add `confirm` to any other tool", text)
        auth = (self.t.plugins / "didit-authentication" / "skills" / "didit-auth-start" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Products page of the Didit console", auth)

    def test_non_admin_roles_rule_in_start_skills(self):
        for plugin, start in (("didit", "didit-connect"), ("didit-transaction-monitoring", "didit-tm-start"),
                              ("didit-user-management", "didit-users-start"), ("didit-authentication", "didit-auth-start")):
            text = (self.t.plugins / plugin / "skills" / start / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=start):
                for rule in (ZERO_APPS_RULE, ROLE_REFUSAL_RULE, RECONNECT_RULE, "`accessible_applications`"):
                    self.assertIn(rule, text)

    def test_secrets_are_not_displayed_or_stored(self):
        team = (self.t.plugins / "didit-user-management" / "skills" / "didit-users-team" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotRegex(team, r"write it (straight )?to [^.\n]*if they asked")
        # The server's own rule for a new key: straight to the project's secret store or .env where
        # files can be written, shown once otherwise, never repeated or kept in notes or memory.
        self.assertIn("write it straight to the project's secret store or `.env` and do not print it in the chat", team)
        self.assertIn("Never repeat it later, never put it in notes or memory", team)
        prompts = (self.t.plugins / "didit-user-management" / "tests" / "prompts.md").read_text(encoding="utf-8")
        self.assertIn("repeating the secret", prompts)
        alerts = (self.t.plugins / "didit-transaction-monitoring" / "skills" / "didit-tm-alerts-cases" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Show the channel, destination and on/off state", alerts)
        self.assertIn("masked", alerts)
        for base in self.t.plugin_dirs():
            for where, text in self.t.skill_texts(base)[:-1]:
                with self.subTest(file=where):
                    self.assertNotRegex(text, r"(write|save|store) (it|the (secret|key)) (straight )?(to|in) [^.\n]*\.env[^.\n]*if")

    def test_watch_only_presets_are_not_installed(self):
        rules = (self.t.plugins / "didit-transaction-monitoring" / "skills" / "didit-tm-rules" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("It takes no `mode`", rules)
        self.assertIn("Never install for a watch-only request", rules)
        prompts = (self.t.plugins / "didit-transaction-monitoring" / "tests" / "prompts.md").read_text(encoding="utf-8")
        block = next(s for s in sections(prompts) if "watch them before they act" in s)
        self.assertIn("calling `didit_transaction_rule_install`", block.split("- Forbidden:", 1)[1])
        self.assertNotIn("didit_transaction_rule_install", block.split("- Tools the answer must name:", 1)[1].split("\n", 1)[0])

    def test_authentication_setup_tools(self):
        profiles = self.t.catalog()["profiles"]
        full = {tool["name"]: tool for tool in profiles["all"]["tools"]}
        read_only = {tool["name"] for tool in profiles["all_read_only"]["tools"]}
        # The hosted server sets up Didit Authentication with these six tools (v5.1.78 and later).
        setup = {name for name in full if name.startswith("didit_authentication_")}
        self.assertEqual(setup, AUTHENTICATION_SETUP_TOOLS)
        self.assertEqual(
            {name for name in setup if full[name]["type"] == "read"},
            {"didit_authentication_get", "didit_authentication_settings_get", "didit_authentication_onboarding_get"},
        )
        self.assertEqual(setup & read_only, {name for name in setup if full[name]["type"] == "read"})
        core = {tool["name"] for tool in profiles["core"]["tools"]}
        allowed = core | AUTHENTICATION_SETUP_TOOLS
        for where, text in self.t.skill_texts(self.t.plugins / "didit-authentication"):
            for token in set(TOOL_TOKEN.findall(text)) - NOT_TOOLS:
                with self.subTest(file=where, tool=token):
                    self.assertIn(token, allowed, "Authentication skills use core tools and the setup tools only")
        readme = (self.t.plugins / "didit-authentication" / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("turning authentication itself on for an application", readme)
        self.assertNotIn("has no tools that configure authentication", readme)

    def test_prompts_cover_every_skill_twice(self):
        for base in self.t.plugin_dirs():
            skills = EXPECTED_SKILLS[base.name]
            text = (base / "tests" / "prompts.md").read_text(encoding="utf-8")
            blocks = [s for s in sections(text) if s.startswith("## ")]
            with self.subTest(plugin=base.name):
                self.assertEqual(len(blocks), 2 * len(skills))
                counts = {name: 0 for name in skills}
                for block in blocks:
                    prompt = re.search(r'- Prompt: "(.+)"', block)
                    expected = re.search(r"- Expected skill: (\S+)", block)
                    self.assertTrue(prompt and expected, block.split("\n", 1)[0])
                    self.assertIn("- Tools the answer must name:", block)
                    self.assertIn("- Forbidden:", block)
                    for name in skills:
                        self.assertNotIn(name, prompt.group(1))
                    counts[expected.group(1)] += 1
                self.assertEqual(set(counts.values()), {2}, counts)
        self.assertEqual(len([s for s in sections(self.t.prompts.read_text(encoding="utf-8")) if s.startswith("## ")]), 16)


class BundleTests(TreeCase):
    def test_bundle_rules(self):
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                self.assertEqual(bundle_problems(base), [])

    def test_readme_and_license(self):
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                readme = (base / "README.md").read_text(encoding="utf-8")
                self.assertGreaterEqual(words_outside_fences(readme), 40)
                self.assertEqual(readme_problems(readme), [])
                license_text = (base / "LICENSE").read_text(encoding="utf-8")
                self.assertIn("MIT License", license_text)
                for heading in ("What this plugin does on your machine and where data goes", "Requirements", "Disconnect"):
                    self.assertIn(heading, readme)
                self.assertIn("no executable binaries", readme)
                if base.name != "didit":
                    self.assertIn(WHICH_HEADING, readme)
                    for other in EXPECTED_SKILLS:
                        self.assertIn(f"`{other}`", readme)
                    self.assertIn(f"/plugin install {base.name} --marketplace didit-protocol/skills", readme)
                    self.assertIn("?toolsets=", readme)
                    for skill in EXPECTED_SKILLS[base.name]:
                        self.assertIn(skill, readme)

    def test_shared_readme_sections_are_identical(self):
        readmes = {base.name: (base / "README.md").read_text(encoding="utf-8") for base in self.t.plugin_dirs()}
        self.assertEqual(set(readmes), set(EXPECTED_SKILLS))
        for heading in SHARED_README_SECTIONS:
            copies = {name: readme_section(text, heading) for name, text in readmes.items() if heading in text}
            with self.subTest(section=heading):
                self.assertEqual(set(copies), set(readmes), f"{heading} missing from a plugin README")
                self.assertEqual(len(set(copies.values())), 1, f"{heading} differs between plugin READMEs")
        root = (self.t.root / "README.md").read_text(encoding="utf-8")
        for where, text in [("README.md", root), *readmes.items()]:
            with self.subTest(file=where):
                self.assertIn(CLAUDE_AI_STATUS, text)
                self.assertNotIn("production-ready", text)

    def test_root_readme_install_section(self):
        readme = (self.t.root / "README.md").read_text(encoding="utf-8")
        install = readme.split("## Install", 1)[1].split("### Developer skills for the REST API", 1)[0]
        self.assertEqual(readme_problems(install), [])
        self.assertIn("`didit-api` uses no MCP server", install)
        self.assertIn("is one of the four MCP plugins", install)

    def test_only_one_binary(self):
        reference = (self.t.plugin / "assets" / "didit-icon.png").read_bytes()
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                binaries = sorted(p.relative_to(base).as_posix() for p in base.rglob("*.png"))
                self.assertEqual(binaries, ["assets/didit-icon.png"])
                data = (base / "assets" / "didit-icon.png").read_bytes()
                width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
                self.assertEqual((width, height), (400, 400))
                self.assertEqual(data, reference)


GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def eval_problems(base: Path, known: set[str]) -> list[str]:
    """`claude plugin eval` cases of one plugin: a prompt, at least one grader, and mocks named after catalog tools."""
    evals = base / "evals"
    if not evals.is_dir():
        return []
    problems: list[str] = []
    cases = sorted(p for p in evals.iterdir() if p.is_dir() and p.name not in {"mocks", "results"})
    if not cases:
        problems.append("evals/ has no cases")
    for case in cases:
        where = f"{base.name}/evals/{case.name}"
        prompt = case / "prompt.md"
        if not prompt.is_file():
            problems.append(f"{where}: no prompt.md")
        else:
            text = prompt.read_text(encoding="utf-8")
            body = text.split("\n---\n", 1)[1] if text.startswith("---\n") and "\n---\n" in text else text
            if not body.strip():
                problems.append(f"{where}: prompt.md has no prompt")
        graders = sorted((case / "graders").glob("*.md"))
        if not graders:
            problems.append(f"{where}: no grader")
        for grader in graders:
            match = re.search(r"^type:\s*(\S+)\s*$", grader.read_text(encoding="utf-8"), re.M)
            if not match or match.group(1) not in GRADER_TYPES:
                problems.append(f"{where}/graders/{grader.name}: missing or unknown grader type")
    mock_files = sorted(evals.glob("mocks/*/*.md")) + sorted(evals.glob("*/mocks/*/*.md"))
    for mock in mock_files:
        if mock.stem not in known:
            problems.append(f"{mock.relative_to(base).as_posix()}: {mock.stem} is not a catalog tool")
    return problems


class EvalTests(TreeCase):
    def test_eval_cases(self):
        known = set(self.t.known_tools())
        for base in self.t.plugin_dirs():
            with self.subTest(plugin=base.name):
                self.assertEqual(eval_problems(base, known), [])


class CommittedTree:
    """Mixin: run a test class against HEAD instead of the working tree."""

    @classmethod
    def setUpClass(cls):
        cls.tree = committed_tree()


class CommittedLayoutTests(CommittedTree, LayoutTests):
    pass


class CommittedManifestTests(CommittedTree, ManifestTests):
    pass


class CommittedSkillTests(CommittedTree, SkillTests):
    pass


class CommittedBundleTests(CommittedTree, BundleTests):
    pass


class CommittedEvalTests(CommittedTree, EvalTests):
    pass


class GitTreeTests(unittest.TestCase):
    def test_every_plugin_is_committed_without_links(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        for name in EXPECTED_SKILLS:
            rel = f"plugins/{name}"
            with self.subTest(plugin=name):
                self.assertEqual(git("rev-parse", "--verify", f"HEAD:{rel}").returncode, 0, f"{rel} is not in HEAD")
                tree = git("ls-tree", "-r", "HEAD", rel)
                self.assertEqual(tree.returncode, 0)
                for line in tree.stdout.decode().splitlines():
                    self.assertNotIn(line.split()[0], {"160000", "120000"}, f"gitlink or symlink: {line}")
                archive = git("archive", "--format=tar", f"HEAD:{rel}")
                self.assertEqual(archive.returncode, 0, archive.stderr.decode())
                with tempfile.TemporaryDirectory() as tmp:
                    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
                        tar.extractall(tmp)
                    base = Path(tmp)
                    self.assertEqual(bundle_problems(base), [])
                    self.assertEqual(mcp_problems(base), [])


class LintSelfTests(unittest.TestCase):
    """Each lint must reject the defect it exists for."""

    def test_argument_syntax_is_not_agreement(self):
        text = "## 3. Re-review\n\n- Call didit_investigator_rereview with run_id and `confirm: true`.\n"
        self.assertNotEqual(confirm_section_problems(text, CONFIRM_TOOLS), [])
        text = "## 3. Re-review\n\n- `didit_investigator_rereview`: `run_id`, `confirm: true`. It starts a review.\n"
        self.assertNotEqual(confirm_section_problems(text, CONFIRM_TOOLS), [])
        ok = text + "Name the report and wait for the person to confirm first.\n"
        self.assertEqual(confirm_section_problems(ok, CONFIRM_TOOLS), [])

    def test_blanket_scope_rules_are_rejected(self):
        for bad in (
            "With several, ask which one, then pass `organization_id` and `application_id` on later calls.",
            "Always pass `organization_id` and `application_id`.",
            "When the defaults are present, use them and pass no ids.",
        ):
            with self.subTest(text=bad):
                self.assertNotEqual(blanket_problems(bad), [])
        self.assertEqual(blanket_problems("Always send the ids a tool requires (for example `didit_org_create_api_key` requires `organization_id` and `application_id`)."), [])

    def test_blanket_confirm_rules_are_rejected(self):
        for bad in (
            "5. Tools that overwrite a decision or delete records take `confirm: true`.",
            "Tools that delete records or issue credentials take `confirm: true`.",
            "accepting, overriding, re-reviewing and answering policy questions all take `confirm: true`, sent later.",
        ):
            with self.subTest(text=bad):
                self.assertNotEqual(blanket_problems(bad), [])
        self.assertEqual(blanket_problems("Send `confirm: true` only to a tool whose schema declares it."), [])

    def test_confirm_on_undeclared_tool_is_rejected(self):
        self.assertNotEqual(confirm_attach_problems("`didit_webhook_delete` and `didit_case_manage` need `confirm: true`.", CONFIRM_TOOLS), [])
        self.assertEqual(confirm_attach_problems("No other tool takes `confirm`; `didit_session_update_status` is confirmed by asking.", CONFIRM_TOOLS), [])
        self.assertNotEqual(confirm_attach_problems("- `didit_lists_delete`: `list_uuid`, `confirm: true`.", CONFIRM_TOOLS), [])
        self.assertEqual(confirm_attach_problems("- `didit_session_delete`: `session_id`, `confirm: true`.", CONFIRM_TOOLS), [])
        self.assertEqual(confirm_attach_problems("`didit_lists_delete` takes no `confirm`.", CONFIRM_TOOLS), [])

    def test_undeclared_argument_is_rejected(self):
        props = {"didit_docs_search": {"query", "language", "limit"}, "didit_org_list_members": {"organization_id"}, "didit_case_get": {"case_id", "application_id"}}
        self.assertNotEqual(arg_pair_problems("- `didit_docs_search`: `query`, `organization_id`.", props), [])
        self.assertNotEqual(arg_pair_problems("`didit_org_list_members` with `organization_id` and `application_id`", props), [])
        self.assertEqual(arg_pair_problems("- `didit_docs_search`: `query`, optional `language` (`en`).", props), [])

    def test_json_example_defects_are_rejected(self):
        tools = {
            "didit_org_invite_member": {"properties": ["app_ids", "emails", "organization_id", "role"], "required": ["app_ids", "emails", "role"]},
            "didit_transaction_rule_backtest": {"properties": ["aggregation", "conditions", "evaluation_mode", "period_days", "scope"], "required": []},
        }
        for bad in (
            '```json\n{"emails": ["a@example.com"]}\n```\n',
            '```json didit_unknown_tool\n{}\n```\n',
            '```json didit_org_invite_member\n{"role": "r", "app_ids": ["a"]}\n```\n',
            '```json didit_org_invite_member\n{"emails": "a@example.com", "role": "r", "app_ids": ["a"]}\n```\n',
            '```json didit_org_invite_member\n{"emails": ["a"], "role": "r", "app_ids": ["a"], "team": "x"}\n```\n',
            '```json didit_transaction_rule_backtest\n{"aggregation": [{"metric": "sum", "operator": "gt", "value": 1}]}\n```\n',
            '```json didit_transaction_rule_backtest\n{"aggregation": [{"metric": "total", "operator": "gt", "value": 1, "window": "1d"}]}\n```\n',
            '```json didit_transaction_rule_backtest\n{"aggregation": [{"metric": "sum", "operator": "gt", "value": 1, "window": "1 day"}]}\n```\n',
            '```json didit_transaction_rule_backtest\n{"conditions": [{"field": "amount", "operator": "greater_than", "value": 1}]}\n```\n',
            '```json didit_transaction_rule_backtest\n{"period_days": 400}\n```\n',
            '  ```json didit_transaction_rule_backtest\n  {"period_days": 90,}\n  ```\n',
        ):
            with self.subTest(text=bad):
                self.assertNotEqual(json_example_problems(bad, tools), [])
        ok = ('  ```json didit_org_invite_member\n  {"emails": ["a@example.com"], "role": "<role>", "app_ids": ["<app>"]}\n  ```\n'
              '```json didit_transaction_rule_backtest\n{"aggregation": [{"metric": "sum", "field": "amount", "operator": "gt", '
              '"value": 10000, "window": "1d", "filters": {"subject_vendor_data": "__current__"}}], "period_days": 90}\n```\n')
        self.assertEqual(json_example_problems(ok, tools), [])

    def test_confirm_list_defects_are_rejected(self):
        known = {"didit_a": {"confirm": True}, "didit_b": {"confirm": True}, "didit_c": {"confirm": False}}
        start = f"{CONFIRM_RULE} {CONFIRM_LIST_LEAD} `didit_a` and `didit_c`. {CONFIRM_OUTSIDE}"
        listed = confirm_list(start)
        self.assertEqual(listed, {"didit_a", "didit_c"})
        self.assertEqual(confirm_list(f"{CONFIRM_RULE} {CONFIRM_LIST_LEAD} none. {CONFIRM_OUTSIDE}"), set())
        # Without the clause for tools outside the recipes, a discovered `confirm` tool would be forbidden.
        self.assertIsNone(confirm_list(f"{CONFIRM_RULE} {CONFIRM_LIST_LEAD} `didit_a`."))
        self.assertIsNone(confirm_list("Only some tools declare a `confirm` argument: `didit_a`. Never add `confirm` to any other tool."))
        problems = confirm_list_problems(listed, {"didit_a", "didit_b"}, known)
        self.assertTrue(any("didit_b" in p for p in problems) and any("didit_c" in p for p in problems), problems)
        self.assertNotEqual(confirm_list_problems(None, set(), known), [])
        self.assertEqual(confirm_list_problems({"didit_a"}, {"didit_a", "didit_c"}, known), [])
        # didit_b declares `confirm` but no recipe names it: it stays off the list and is not a defect.
        self.assertEqual(confirm_list_problems({"didit_a"}, {"didit_a"}, known), [])

    def test_nested_example_defects_are_rejected(self):
        tools = {"didit_questionnaire_create": {"properties": ["form_elements", "status", "title"], "required": ["form_elements", "title"]},
                 "didit_org_list_roles": {"properties": [], "required": []}}
        for bad in (
            '```json didit_questionnaire_create\n{"title": "T", "form_elements": [{"element_type": "LONG_TEXT", "title": "Q"}]}\n```\n',
            '```json didit_questionnaire_create\n{"title": "T", "form_elements": [{"element_type": "LONG_TEXT", "title": {"en": "Q"}, "placeholder": "x"}]}\n```\n',
            '```json didit_questionnaire_create\n{"title": "T", "form_elements": [{"element_type": "long_text"}]}\n```\n',
            '- `didit_org_list_roles`: lists roles.\n\n```json didit_questionnaire_create\n{"title": "T", "form_elements": []}\n```\n',
        ):
            with self.subTest(text=bad):
                self.assertNotEqual(json_example_problems(bad, tools), [])
        ok = '`didit_questionnaire_create`:\n\n```json didit_questionnaire_create\n{"title": "T", "form_elements": [{"element_type": "LONG_TEXT", "title": {"en": "Q"}, "is_required": false}]}\n```\n'
        self.assertEqual(json_example_problems(ok, tools), [])

    def test_missing_conditional_rule_is_rejected(self):
        self.assertNotEqual(conditional_rule_problems({"a": "Wait for a clear yes before calling the tool."}), [])
        self.assertNotEqual(conditional_rule_problems({"a": CONDITIONAL_RULE, "b": CONDITIONAL_RULE.replace("is not agreement", "counts")}), [])
        self.assertEqual(conditional_rule_problems({"a": "Rules. " + CONDITIONAL_RULE}), [])

    def test_billing_overstatements_are_rejected(self):
        for bad in ("In a live application each check uses Didit credits.", "In a live application every session is billed.",
                    "Every live submission uses the organization's Didit credits.", "It is free and decides nothing.",
                    "Sandbox applications never bill.", "so they use no Didit credits"):
            with self.subTest(text=bad):
                self.assertNotEqual(billing_problems(bad), [])
        for ok in ("In a live application this can use your Didit credits.", "Sandbox applications are free to test in.",
                   "`search` (free text)"):
            with self.subTest(text=ok):
                self.assertEqual(billing_problems(ok), [])

    def test_full_url_display_is_rejected(self):
        for bad in ("Show the URL and the events and wait.", "Display the destination URL.", "print the full webhook URL"):
            with self.subTest(text=bad):
                self.assertNotEqual(full_url_problems(bad), [])
        self.assertEqual(full_url_problems("Show each URL masked: the host, then `...`."), [])

    def test_readme_section_drift_is_detected(self):
        one = "# A\n\n## Shorter tool list (optional)\n\nSame.\n\n## Next\n"
        two = "# B\n\n## Shorter tool list (optional)\n\nDrifted.\n\n## Next\n"
        self.assertNotEqual(readme_section(one, SHARED_README_SECTIONS[1]), readme_section(two, SHARED_README_SECTIONS[1]))
        self.assertEqual(readme_section(one, SHARED_README_SECTIONS[1]), readme_section(one.replace("# A", "# C"), SHARED_README_SECTIONS[1]))

    def test_readme_claims_are_rejected(self):
        self.assertNotEqual(readme_problems("It has no hooks, no scripts and no binaries."), [])
        self.assertNotEqual(readme_problems("If you want only the tools this plugin uses, connect it."), [])
        self.assertEqual(readme_problems("no executable binaries; for a shorter tool list, connect it."), [])


if __name__ == "__main__":
    result = unittest.main(verbosity=1, exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
