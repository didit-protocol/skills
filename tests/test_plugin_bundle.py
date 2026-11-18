#!/usr/bin/env python3
"""Offline checks for the `didit` plugin bundle and the repo's plugin marketplaces.

Stdlib only. Runs on the working tree and, when git is available and HEAD contains the
plugin, on `git archive HEAD:plugins/didit` (what a directory submission would receive).

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
PLUGIN = ROOT / "plugins" / "didit"
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
EM_DASH = "—"
CONFIRM_WORDS = re.compile(r"\b(confirm\w*|agree\w*)\b", re.IGNORECASE)
TOOL_TOKEN = re.compile(r"\bdidit_[a-z0-9_]+\b")
DISCOVERY = {"didit_tool_search", "didit_tool_describe", "didit_tool_call_read", "didit_tool_call_write"}


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


class ManifestTests(unittest.TestCase):
    def test_every_manifest_is_valid_json(self):
        paths = [
            ROOT / ".claude-plugin" / "marketplace.json",
            ROOT / ".agents" / "plugins" / "marketplace.json",
            *PLUGIN.rglob("*.json"),
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                load_json(path)

    def test_no_root_plugin_json(self):
        self.assertFalse((ROOT / ".claude-plugin" / "plugin.json").exists())

    def test_host_manifests_agree(self):
        claude = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
        codex = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        cursor = load_json(PLUGIN / ".cursor-plugin" / "plugin.json")
        for key in ("name", "version", "description"):
            with self.subTest(key=key):
                self.assertEqual(claude[key], codex[key])
                self.assertEqual(claude[key], cursor[key])
        self.assertEqual(claude["name"], "didit")
        self.assertEqual(claude["version"], "1.0.0")
        self.assertLessEqual(len(claude["description"]), 200)
        self.assertEqual(claude["license"], "MIT")
        self.assertEqual(claude["mcpServers"], "./.mcp.json")
        self.assertTrue((PLUGIN / claude["icon"]).is_file())
        for host in (codex, cursor):
            self.assertTrue((PLUGIN / host["skills"]).is_dir())
            self.assertTrue((PLUGIN / host["mcpServers"]).is_file())

    def test_claude_marketplace_resolves(self):
        market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(market["name"], "didit")
        entries = {entry["name"]: entry for entry in market["plugins"]}
        self.assertEqual(set(entries), {"didit", "didit-api"})
        for entry in entries.values():
            self.assertTrue((ROOT / entry["source"]).is_dir(), entry["source"])
        self.assertEqual(entries["didit"]["source"], "./plugins/didit")
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
        self.assertEqual(entries["didit"]["source"], {"source": "local", "path": "./plugins/didit"})
        self.assertTrue((ROOT / entries["didit"]["source"]["path"]).is_dir())

    def test_mcp_server_entry(self):
        self.assertEqual(mcp_problems(PLUGIN), [])

    def test_no_empty_gitmodules(self):
        self.assertFalse((ROOT / ".gitmodules").exists())


class SkillTests(CatalogMixin, unittest.TestCase):
    def test_skill_set_and_frontmatter(self):
        found = sorted(p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir())
        self.assertEqual(found, sorted(PLUGIN_SKILLS))
        for name in PLUGIN_SKILLS:
            path = PLUGIN / "skills" / name / "SKILL.md"
            with self.subTest(skill=name):
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

    def test_no_collision_with_rest_skills(self):
        rest = {p.parent.name for p in REST_SKILLS.glob("*/SKILL.md")}
        self.assertEqual(len(rest), 20)
        self.assertEqual(set(PLUGIN_SKILLS) & rest, set())

    def tool_texts(self):
        for name in PLUGIN_SKILLS:
            yield f"skills/{name}/SKILL.md", (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        yield "tests/prompts.md", PROMPTS.read_text(encoding="utf-8")

    def test_every_tool_exists_in_catalog(self):
        known = self.known_tools()
        for where, text in self.tool_texts():
            for token in sorted(set(TOOL_TOKEN.findall(text))):
                with self.subTest(file=where, tool=token):
                    self.assertIn(token, known)

    def test_confirm_tools_are_confirmed(self):
        confirm_tools = {name for name, tool in self.known_tools().items() if tool["confirm"]}
        for where, text in self.tool_texts():
            for section in sections(text):
                used = confirm_tools & set(TOOL_TOKEN.findall(section))
                if used:
                    with self.subTest(file=where, section=section.split("\n", 1)[0]):
                        self.assertRegex(section, CONFIRM_WORDS, f"{sorted(used)} without a confirmation sentence")

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

    def test_prompts_cover_every_skill_twice(self):
        text = PROMPTS.read_text(encoding="utf-8")
        blocks = [s for s in sections(text) if s.startswith("## ")]
        self.assertEqual(len(blocks), 16)
        counts = {name: 0 for name in PLUGIN_SKILLS}
        for block in blocks:
            prompt = re.search(r'- Prompt: "(.+)"', block)
            expected = re.search(r"- Expected skill: (\S+)", block)
            self.assertTrue(prompt and expected, block.split("\n", 1)[0])
            self.assertIn("- Tools the answer must name:", block)
            self.assertIn("- Forbidden:", block)
            for name in PLUGIN_SKILLS:
                self.assertNotIn(name, prompt.group(1))
            counts[expected.group(1)] += 1
        self.assertEqual(set(counts.values()), {2}, counts)


class BundleTests(unittest.TestCase):
    def test_working_tree_bundle(self):
        self.assertEqual(bundle_problems(PLUGIN), [])

    def test_readme_and_license(self):
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(words_outside_fences(readme), 40)
        license_text = (PLUGIN / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        for heading in ("What this plugin does on your machine and where data goes", "Requirements", "Disconnect"):
            self.assertIn(heading, readme)

    def test_only_one_binary(self):
        binaries = sorted(p.relative_to(PLUGIN).as_posix() for p in PLUGIN.rglob("*.png"))
        self.assertEqual(binaries, ["assets/didit-icon.png"])
        data = (PLUGIN / "assets" / "didit-icon.png").read_bytes()
        width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        self.assertEqual((width, height), (400, 400))

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)

    def test_committed_bundle(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if self._git("rev-parse", "--verify", "HEAD:plugins/didit").returncode != 0:
            self.skipTest("HEAD does not contain plugins/didit yet")
        tree = self._git("ls-tree", "-r", "HEAD", "plugins/didit")
        self.assertEqual(tree.returncode, 0)
        for line in tree.stdout.decode().splitlines():
            mode = line.split()[0]
            self.assertNotIn(mode, {"160000", "120000"}, f"gitlink or symlink: {line}")
        archive = self._git("archive", "--format=tar", "HEAD:plugins/didit")
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


if __name__ == "__main__":
    result = unittest.main(verbosity=1, exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
