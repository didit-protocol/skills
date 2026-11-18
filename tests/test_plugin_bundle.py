#!/usr/bin/env python3
"""Offline checks for every plugin bundle under plugins/ and the repo's plugin marketplaces.

Stdlib only. Runs on the working tree and, when git is available and HEAD contains a
plugin, on `git archive HEAD:plugins/<name>` (what a directory submission would receive).
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
PLUGINS_DIR = ROOT / "plugins"
PLUGIN = PLUGINS_DIR / "didit"
REST_SKILLS = ROOT / "skills"
CATALOG = PLUGIN / "tests" / "tool-catalog.json"
PROMPTS = PLUGIN / "tests" / "prompts.md"

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
CONFIRM_WORDS = re.compile(r"\b(confirm\w*|agree\w*)\b", re.IGNORECASE)
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


class CatalogMixin:
    @classmethod
    def catalog(cls) -> dict:
        if not hasattr(cls, "_catalog"):
            cls._catalog = load_json(CATALOG)
        return cls._catalog

    @classmethod
    def known_tools(cls) -> dict[str, dict]:
        tools: dict[str, dict] = {}
        for profile in cls.catalog()["profiles"].values():
            for tool in profile.get("tools", []):
                tools.setdefault(tool["name"], tool)
        return tools


def plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir())


def skill_texts(base: Path) -> list[tuple[str, str]]:
    """(where, text) for every SKILL.md and the prompts file of one plugin."""
    out = []
    for name in EXPECTED_SKILLS[base.name]:
        out.append((f"{base.name}/skills/{name}/SKILL.md", (base / "skills" / name / "SKILL.md").read_text(encoding="utf-8")))
    out.append((f"{base.name}/tests/prompts.md", (base / "tests" / "prompts.md").read_text(encoding="utf-8")))
    return out


class LayoutTests(unittest.TestCase):
    def test_plugin_folders_are_known(self):
        self.assertEqual([p.name for p in plugin_dirs()], sorted(EXPECTED_SKILLS))


class ManifestTests(unittest.TestCase):
    def test_every_manifest_is_valid_json(self):
        paths = [
            ROOT / ".claude-plugin" / "marketplace.json",
            ROOT / ".agents" / "plugins" / "marketplace.json",
            *PLUGINS_DIR.rglob("*.json"),
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                load_json(path)

    def test_no_root_plugin_json(self):
        self.assertFalse((ROOT / ".claude-plugin" / "plugin.json").exists())

    def test_host_manifests_agree(self):
        didit = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
        for base in plugin_dirs():
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

    def test_claude_marketplace_resolves(self):
        market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(market["name"], "didit")
        entries = {entry["name"]: entry for entry in market["plugins"]}
        self.assertEqual(set(entries), set(EXPECTED_SKILLS) | {"didit-api"})
        for entry in entries.values():
            self.assertTrue((ROOT / entry["source"]).is_dir(), entry["source"])
        for name in EXPECTED_SKILLS:
            with self.subTest(plugin=name):
                entry = entries[name]
                self.assertEqual(entry["source"], f"./plugins/{name}")
                self.assertEqual(entry["version"], "1.0.0")
                manifest = load_json(PLUGINS_DIR / name / ".claude-plugin" / "plugin.json")
                self.assertEqual(entry["description"], manifest["description"])
                self.assertTrue(entry.get("category"))
                self.assertTrue(entry.get("keywords"))
        api = entries["didit-api"]
        self.assertEqual(api["source"], "./")
        self.assertIs(api["strict"], False)
        self.assertEqual(api["version"], "5.2.0")
        listed = api["skills"]
        rest = sorted(p.parent.name for p in REST_SKILLS.glob("*/SKILL.md"))
        self.assertEqual(sorted(Path(s).name for s in listed), rest)
        for skill in listed:
            self.assertTrue((ROOT / skill / "SKILL.md").is_file(), skill)

    def test_codex_marketplace_resolves(self):
        market = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual(market["name"], "didit")
        entries = {entry["name"]: entry for entry in market["plugins"]}
        self.assertEqual(set(entries), set(EXPECTED_SKILLS))
        shape = {key: value for key, value in entries["didit"].items() if key not in {"name", "source"}}
        for name, entry in entries.items():
            with self.subTest(plugin=name):
                self.assertEqual(entry["source"], {"source": "local", "path": f"./plugins/{name}"})
                self.assertTrue((ROOT / entry["source"]["path"]).is_dir())
                self.assertEqual({k: v for k, v in entry.items() if k not in {"name", "source"}}, shape)

    def test_mcp_server_entry(self):
        reference = (PLUGIN / ".mcp.json").read_bytes()
        for base in plugin_dirs():
            with self.subTest(plugin=base.name):
                self.assertEqual(mcp_problems(base), [])
                self.assertEqual((base / ".mcp.json").read_bytes(), reference, "must be identical to plugins/didit/.mcp.json")

    def test_no_empty_gitmodules(self):
        self.assertFalse((ROOT / ".gitmodules").exists())


class SkillTests(CatalogMixin, unittest.TestCase):
    def test_skill_set_and_frontmatter(self):
        for base in plugin_dirs():
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
        rest = {p.parent.name for p in REST_SKILLS.glob("*/SKILL.md")}
        self.assertEqual(len(rest), 20)
        seen: dict[str, str] = {}
        for plugin, skills in EXPECTED_SKILLS.items():
            for name in skills:
                with self.subTest(skill=name):
                    self.assertNotIn(name, seen, f"{name} is in {seen.get(name)} and {plugin}")
                    self.assertNotIn(name, rest, f"{name} collides with a REST skill")
                    seen[name] = plugin

    def test_no_collision_with_rest_skills(self):
        rest = {p.parent.name for p in REST_SKILLS.glob("*/SKILL.md")}
        self.assertEqual(set(PLUGIN_SKILLS) & rest, set())

    def test_every_tool_exists_in_catalog(self):
        known = self.known_tools()
        for base in plugin_dirs():
            for where, text in skill_texts(base):
                for token in sorted(set(TOOL_TOKEN.findall(text)) - NOT_TOOLS):
                    with self.subTest(file=where, tool=token):
                        self.assertIn(token, known)

    def test_confirm_tools_are_confirmed(self):
        confirm_tools = {name for name, tool in self.known_tools().items() if tool["confirm"]}
        for base in plugin_dirs():
            for where, text in skill_texts(base):
                for section in sections(text):
                    used = confirm_tools & set(TOOL_TOKEN.findall(section))
                    if used:
                        with self.subTest(file=where, section=section.split("\n", 1)[0]):
                            self.assertRegex(section, CONFIRM_WORDS, f"{sorted(used)} without a confirmation sentence")

    def test_focused_plugins_skip_business_update(self):
        # No recipe uses it (its route does not exist as coded); prompts.md may list it as forbidden.
        for name in FOCUSED:
            for where, text in skill_texts(PLUGINS_DIR / name)[:-1]:
                with self.subTest(file=where):
                    self.assertNotRegex(text, r"\bdidit_vendor_business_update\b(?!_)")

    def test_read_only_and_discovery_wording(self):
        profiles = self.catalog()["profiles"]
        read_only = {tool["name"] for tool in profiles["all_read_only"]["tools"]}
        full = {tool["name"] for tool in profiles["all"]["tools"]}
        core = {tool["name"] for tool in profiles["core"]["tools"]}
        # The facts the wording relies on.
        self.assertEqual(read_only & DISCOVERY, set(), "discovery tools appear on all_read_only")
        self.assertTrue(all(tool["type"] == "read" for tool in profiles["all_read_only"]["tools"]))
        self.assertEqual(full & DISCOVERY, set(), "discovery tools appear when every toolset loads")
        self.assertTrue(DISCOVERY <= core, "core profile should list the discovery tools")
        self.assertIn("didit_context_get", core)
        connect = (PLUGIN / "skills" / "didit-connect" / "SKILL.md").read_text(encoding="utf-8")
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

    def test_focused_start_skills_restate_the_rules(self):
        for plugin, start in START_SKILL.items():
            text = (PLUGINS_DIR / plugin / "skills" / start / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=start):
                self.assertLessEqual(len(text.rstrip("\n").split("\n")), 60)
                for phrase in (
                    "Call `didit_context_get` first",
                    "Never decide it from an application's name",
                    "only when they are themselves in your tool list",
                    "proxy call",
                    "`confirm: true`",
                    "Never ask for a password, an API key or a one-time code",
                    "`didit_docs_search`",
                    "https://didit.me/pricing",
                ):
                    self.assertIn(phrase, text)
                for skill in EXPECTED_SKILLS[plugin]:
                    if skill != start:
                        self.assertIn(skill, text, f"{start} must route to {skill}")

    def test_authentication_has_no_configuration_tools(self):
        known = self.known_tools()
        # The catalog has no tool that configures Authentication in this build.
        for name, tool in known.items():
            with self.subTest(tool=name):
                self.assertNotIn("authentication", tool.get("permission") or "")
                self.assertNotRegex(name, r"^didit_(auth|sign_?in|sso|passkey|jwks)")
        core = {tool["name"] for tool in self.catalog()["profiles"]["core"]["tools"]}
        for where, text in skill_texts(PLUGINS_DIR / "didit-authentication"):
            for token in set(TOOL_TOKEN.findall(text)) - NOT_TOOLS:
                with self.subTest(file=where, tool=token):
                    self.assertIn(token, core, "Authentication skills only use core tools")
        readme = (PLUGINS_DIR / "didit-authentication" / "README.md").read_text(encoding="utf-8")
        self.assertIn("this plugin is guidance + documentation search; configuration happens in the didit console", readme.lower())

    def test_prompts_cover_every_skill_twice(self):
        for base in plugin_dirs():
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
        self.assertEqual(len([s for s in sections(PROMPTS.read_text(encoding="utf-8")) if s.startswith("## ")]), 16)


class BundleTests(unittest.TestCase):
    def test_working_tree_bundle(self):
        for base in plugin_dirs():
            with self.subTest(plugin=base.name):
                self.assertEqual(bundle_problems(base), [])

    def test_readme_and_license(self):
        for base in plugin_dirs():
            with self.subTest(plugin=base.name):
                readme = (base / "README.md").read_text(encoding="utf-8")
                self.assertGreaterEqual(words_outside_fences(readme), 40)
                license_text = (base / "LICENSE").read_text(encoding="utf-8")
                self.assertIn("MIT License", license_text)
                for heading in ("What this plugin does on your machine and where data goes", "Requirements", "Disconnect"):
                    self.assertIn(heading, readme)
                if base.name != "didit":
                    self.assertIn(WHICH_HEADING, readme)
                    for other in EXPECTED_SKILLS:
                        self.assertIn(f"`{other}`", readme)
                    self.assertIn(f"/plugin install {base.name} --marketplace didit-protocol/skills", readme)
                    self.assertIn("?toolsets=", readme)
                    for skill in EXPECTED_SKILLS[base.name]:
                        self.assertIn(skill, readme)

    def test_only_one_binary(self):
        reference = (PLUGIN / "assets" / "didit-icon.png").read_bytes()
        for base in plugin_dirs():
            with self.subTest(plugin=base.name):
                binaries = sorted(p.relative_to(base).as_posix() for p in base.rglob("*.png"))
                self.assertEqual(binaries, ["assets/didit-icon.png"])
                data = (base / "assets" / "didit-icon.png").read_bytes()
                width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
                self.assertEqual((width, height), (400, 400))
                self.assertEqual(data, reference)

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)

    def test_committed_bundle(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        checked = 0
        for name in EXPECTED_SKILLS:
            rel = f"plugins/{name}"
            if self._git("rev-parse", "--verify", f"HEAD:{rel}").returncode != 0:
                continue
            checked += 1
            with self.subTest(plugin=name):
                tree = self._git("ls-tree", "-r", "HEAD", rel)
                self.assertEqual(tree.returncode, 0)
                for line in tree.stdout.decode().splitlines():
                    mode = line.split()[0]
                    self.assertNotIn(mode, {"160000", "120000"}, f"gitlink or symlink: {line}")
                archive = self._git("archive", "--format=tar", f"HEAD:{rel}")
                self.assertEqual(archive.returncode, 0, archive.stderr.decode())
                with tempfile.TemporaryDirectory() as tmp:
                    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
                        for member in tar.getmembers():
                            self.assertFalse(member.issym() or member.islnk(), member.name)
                        tar.extractall(tmp)
                    base = Path(tmp)
                    self.assertEqual(bundle_problems(base), [])
                    self.assertEqual(mcp_problems(base), [])
                    self.assertTrue((base / ".claude-plugin" / "plugin.json").is_file())
                    self.assertTrue((base / "LICENSE").is_file())
                    self.assertGreaterEqual(words_outside_fences((base / "README.md").read_text(encoding="utf-8")), 40)
        if checked == 0:
            self.skipTest("HEAD does not contain any plugin yet")


if __name__ == "__main__":
    result = unittest.main(verbosity=1, exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
