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
# Tokens that look like tool names but are not: a record field and the Flutter Authentication package.
NOT_TOOLS = {"didit_internal_id", "didit_internal_id_list", "didit_auth"}


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
    files = [p for p in base.rglob("*")]
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
README_FORBIDDEN = [
    (re.compile(r"\bno binaries\b", re.I), "say 'no executable binaries': the icon is a binary file"),
    (re.compile(r"only the tools this plugin uses", re.I), "a toolset connection is a shorter tool list, not only this plugin's tools"),
]


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
        """(where, text) for every SKILL.md and the prompts file of one plugin."""
        out = []
        for name in EXPECTED_SKILLS[base.name]:
            out.append((f"{base.name}/skills/{name}/SKILL.md", (base / "skills" / name / "SKILL.md").read_text(encoding="utf-8")))
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
                self.assertEqual(claude["version"], "1.0.0")
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
                self.assertEqual(entry["version"], "1.0.0")
                manifest = load_json(self.t.plugins / name / ".claude-plugin" / "plugin.json")
                self.assertEqual(entry["description"], manifest["description"])
                self.assertTrue(entry.get("category"))
                self.assertTrue(entry.get("keywords"))
        api = entries["didit-api"]
        self.assertEqual(api["source"], "./")
        self.assertIs(api["strict"], False)
        self.assertEqual(api["version"], "5.2.0")
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
        known = self.t.known_tools()
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
                    "Never send an id the tool does not declare",
                    "inside `arguments`, never next to `name`",
                    "only when they are themselves in your tool list",
                    "proxy call",
                    "wait for a clear yes before calling the tool",
                    "`confirm: true`",
                    "only after the person agreed to that exact action in this conversation",
                    "a password, an API key or a one-time code",
                    "`didit_docs_search`",
                    "https://didit.me/pricing",
                ):
                    self.assertIn(phrase, text)
                for skill in EXPECTED_SKILLS[plugin]:
                    if skill != start:
                        self.assertIn(skill, text, f"{start} must route to {skill}")
                if plugin in {"didit-transaction-monitoring", "didit-user-management"}:
                    self.assertIn("Never add `confirm` to any other tool", text)
                    named = set(re.findall(r"didit_[a-z0-9_]+", text.split("Only some tools declare", 1)[1].split("Send `confirm", 1)[0]))
                    self.assertTrue(named and named <= CONFIRM_TOOLS, named)
        auth = (self.t.plugins / "didit-authentication" / "skills" / "didit-auth-start" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Products page of the Didit console", auth)

    def test_secrets_are_not_displayed_or_stored(self):
        team = (self.t.plugins / "didit-user-management" / "skills" / "didit-users-team" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotRegex(team, r"write it (straight )?to [^.\n]*if they asked")
        self.assertIn("never offer to", team)
        prompts = (self.t.plugins / "didit-user-management" / "tests" / "prompts.md").read_text(encoding="utf-8")
        self.assertIn("writing the secret to `.env`", prompts)
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

    def test_authentication_has_no_configuration_tools(self):
        known = self.t.known_tools()
        # The catalog has no tool that configures Authentication in this build.
        for name, tool in known.items():
            with self.subTest(tool=name):
                self.assertNotIn("authentication", tool.get("permission") or "")
                self.assertNotRegex(name, r"^didit_(auth|sign_?in|sso|passkey|jwks)")
        core = {tool["name"] for tool in self.t.catalog()["profiles"]["core"]["tools"]}
        for where, text in self.t.skill_texts(self.t.plugins / "didit-authentication"):
            for token in set(TOOL_TOKEN.findall(text)) - NOT_TOOLS:
                with self.subTest(file=where, tool=token):
                    self.assertIn(token, core, "Authentication skills only use core tools")
        readme = (self.t.plugins / "didit-authentication" / "README.md").read_text(encoding="utf-8")
        self.assertIn("this plugin is guidance + documentation search; configuration happens in the didit console", readme.lower())

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

    def test_readme_claims_are_rejected(self):
        self.assertNotEqual(readme_problems("It has no hooks, no scripts and no binaries."), [])
        self.assertNotEqual(readme_problems("If you want only the tools this plugin uses, connect it."), [])
        self.assertEqual(readme_problems("no executable binaries; for a shorter tool list, connect it."), [])


if __name__ == "__main__":
    result = unittest.main(verbosity=1, exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
