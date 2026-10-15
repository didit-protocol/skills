#!/usr/bin/env python3
"""Offline checks for every skill in this repository. No network and no API key needed.

Checks that each skill keeps the repository format (frontmatter, naming, Getting Started),
that the README table and tree match the skills folder, that every script compiles and is
referenced, that code examples parse, that API paths keep their trailing slash, that no
supplier names or em dashes slip in, and that the documented webhook signature verifier
accepts signatures produced by Didit's signing algorithm.

Usage:
    python3 tests/test_skill_structure.py
"""

import hashlib
import hmac
import json
import py_compile
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
SKILLS = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
README = (ROOT / "README.md").read_text(encoding="utf-8")

EM_DASH, EN_DASH = chr(0x2014), chr(0x2013)
NAME_RE = re.compile(r"^didit-[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
FENCE_RE = re.compile(r"^```([A-Za-z0-9_+-]*)[^\n]*\n(.*?)^```", re.S | re.M)
# Didit API paths, e.g. /v3/session/{id}/decision/ or https://verification.didit.me/v1/events/
API_PATH_RE = re.compile(r"(?<![\w.])/v[123]/[A-Za-z0-9_{}<>.\-/]*[A-Za-z0-9_{}<>\-/]")
# Supplier names that must never be published (same guard as the public docs repository).
SUPPLIER_RE = re.compile(
    r"\b(prelude|monnai|ipqualityscore|twilio|vonage|sinch|telnyx|plivo|hibp|have.?i.?been.?pwned|"
    r"haveibeenpwned|aml ?watcher|amlwatcher|maxmind|seon|ekata|ipdata|ipgeolocation|iproov|facetec|"
    r"innovatrics|regula|endesa|opensanctions|dilisense|complyadvantage|google maps|mapbox)\b",
    re.I,
)

# Webhook test vector. The signatures were produced by Didit's own signing functions
# (generate_signature, generate_signature_v2 and generate_signature_simple) for this payload.
WEBHOOK_SECRET = "whsec_test_vector_not_a_real_secret"
WEBHOOK_RAW_BODY = (
    '{"created_at":1760000000,"decision":{"aml_score":12.5,"face_matches":[{"score":87,"status":"Approved"}]},'
    '"event_id":"0f6b2f5e-8f4a-4c1b-9d7e-2a1b3c4d5e6f","metadata":{"display_name":"Jos\\u00e9 M\\u00fcller","tier":2},'
    '"session_id":"11111111-2222-4333-8444-555555555555","status":"Approved","timestamp":1760000000,'
    '"vendor_data":"user-42","webhook_type":"status.updated"}'
)
WEBHOOK_HEADERS = {
    "X-Signature": "1ea17c072b7c05aedce1b51d22a4e56921d4bfa039b731755df9730924c28003",
    "X-Signature-V2": "99a6d72d2bec5ae5ef9bbc4620f2be3f84fd2f192f5e44a05b535d3af6e199ca",
    "X-Signature-Simple": "6bb7729b64ef61faf2683171d1a2c499b415a45452128c748c3a5425c8fe3a58",
    "X-Timestamp": "1760000000",
}


def skill_md(skill):
    return (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(text):
    """Return the frontmatter block as text (between the first two '---' lines)."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return match.group(1) if match else ""


def fm_value(fm, key):
    match = re.search(rf"^{key}:[ \t]*(.*)$", fm, re.M)
    return match.group(1).strip() if match else None


def fm_description(fm):
    match = re.search(r"^description:[ \t]*>-?\n((?:[ \t]+.*\n?)+)", fm, re.M)
    if match:
        return " ".join(line.strip() for line in match.group(1).splitlines()).strip()
    return fm_value(fm, "description") or ""


def fm_required_env(fm):
    match = re.search(r"^\s+requires:\s*\n\s+env:[ \t]*(\[\])?\n((?:\s+- .*\n)*)", fm, re.M)
    if not match:
        return None
    if match.group(1):
        return []
    return [line.strip()[2:].strip() for line in match.group(2).splitlines() if line.strip()]


def code_blocks(text, *languages):
    return [body for lang, body in FENCE_RE.findall(text) if lang.lower() in languages]


def public_files():
    files = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
    files += sorted(p for p in SKILLS_DIR.rglob("*") if p.is_file() and p.suffix in {".md", ".py"})
    files += sorted((ROOT / "tests").glob("*.py"))
    return files


class SkillFormatTest(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter(self):
        self.assertGreaterEqual(len(SKILLS), 20)
        for skill in SKILLS:
            with self.subTest(skill=skill):
                fm = frontmatter(skill_md(skill))
                self.assertTrue(fm, "SKILL.md must start with YAML frontmatter")
                self.assertEqual(fm_value(fm, "name"), skill, "frontmatter name must match the folder")
                self.assertRegex(skill, NAME_RE, "names are lowercase kebab-case with the didit- prefix")
                self.assertLessEqual(len(skill), 64)
                self.assertRegex(fm_value(fm, "version") or "", SEMVER_RE)
                description = fm_description(fm)
                self.assertGreater(len(description), 80, "description must say when to use the skill")
                self.assertLessEqual(len(description), 1024, "Agent Skills descriptions are capped at 1024 characters")
                for key in ("metadata", "openclaw", "primaryEnv", "emoji", "homepage"):
                    self.assertRegex(fm, rf"(?m)^\s*{key}:", f"missing {key}")
                self.assertIsNotNone(fm_required_env(fm), "metadata.openclaw.requires.env must be present")

    def test_api_key_skills_have_getting_started(self):
        for skill in SKILLS:
            text = skill_md(skill)
            required = fm_required_env(frontmatter(text)) or []
            if "DIDIT_API_KEY" not in required:
                continue
            with self.subTest(skill=skill):
                self.assertRegex(text, r"(?m)^## Getting Started")
                self.assertIn("application.api_key", text, "the key is returned at application.api_key")
                self.assertIn("Developers > API keys", text, "console path for API keys")

    def test_readme_table_lists_every_skill_with_its_version(self):
        rows = dict(re.findall(r"^\| \[\*\*(didit-[a-z0-9-]+)\*\*\]\(skills/\1/\) \| ([0-9.]+) \|", README, re.M))
        self.assertEqual(sorted(rows), SKILLS, "README table must list exactly the skills in skills/")
        for skill, version in rows.items():
            with self.subTest(skill=skill):
                self.assertEqual(version, fm_value(frontmatter(skill_md(skill)), "version"))

    def test_readme_tree_lists_every_skill_and_script(self):
        tree = dict(re.findall(r"^[├└]── (didit-[a-z0-9-]+)/\s+(.*)$", README, re.M))
        self.assertEqual(sorted(tree), SKILLS, "README repo structure must list every skill")
        for skill, line in tree.items():
            with self.subTest(skill=skill):
                scripts = sorted(p.stem for p in (SKILLS_DIR / skill / "scripts").glob("*.py"))
                listed = re.search(r"scripts/\{?([^}]*?)\}?\.py", line)
                listed = sorted(s.strip() for s in listed.group(1).split(",")) if listed else []
                self.assertEqual(listed, scripts)

    def test_readme_counts_match(self):
        count = len(SKILLS)
        self.assertTrue(re.search(rf"\b{count} production-ready skills\b", README), f"README intro must say {count} skills")
        self.assertTrue(re.search(rf"← {count} skills", README), f"README tree must say {count} skills")


class ScriptTest(unittest.TestCase):
    def test_scripts_compile_and_are_referenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            for skill in SKILLS:
                text = skill_md(skill)
                scripts_dir = SKILLS_DIR / skill / "scripts"
                for script in sorted(scripts_dir.glob("*.py")):
                    with self.subTest(script=str(script.relative_to(ROOT))):
                        py_compile.compile(str(script), cfile=str(Path(tmp) / f"{skill}-{script.stem}.pyc"), doraise=True)
                        self.assertIn(f"scripts/{script.name}", text, "every script must be documented in its SKILL.md")
                        source = script.read_text(encoding="utf-8")
                        self.assertIn("argparse", source)
                        self.assertNotRegex(source, r"api_key\[[-:0-9]", "never print any part of the API key")
                for referenced in sorted(set(re.findall(r"scripts/([a-z0-9_]+\.py)", text))):
                    with self.subTest(skill=skill, referenced=referenced):
                        self.assertTrue((scripts_dir / referenced).is_file(), f"{referenced} is referenced but missing")


class BundleTest(unittest.TestCase):
    """Exercise publishing policies with Git's ignore matcher, without an API key.

    ClawHub reads ignore files from the individual publication folder. The README
    stages both repository policies there, appending matching skill-local rules.
    The actual CLI collector is checked separately before human publication.
    """

    def test_publication_filters_keep_helpers_and_exclude_private_files(self):
        excluded = {".env", ".env.local", "scripts/__pycache__/helper.pyc",
                    "scripts/helper.pyc", "tests/test_local.py", "README.md"}
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "--quiet", tmp], check=True, capture_output=True)
            for skill in SKILLS:
                folder = SKILLS_DIR / skill
                policies = [ROOT / ".gitignore", folder / ".gitignore",
                            ROOT / ".clawhubignore", folder / ".clawhubignore"]
                (Path(tmp) / ".gitignore").write_text(
                    "\n".join(p.read_text(encoding="utf-8") for p in policies if p.exists()),
                    encoding="utf-8",
                )
                included = {"SKILL.md"}
                included.update(p.relative_to(folder).as_posix() for p in folder.rglob("*.py"))
                included.update(re.findall(r"scripts/[a-z0-9_]+\.py", skill_md(skill)))
                result = subprocess.run(
                    ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--stdin"],
                    cwd=tmp, input="\n".join(sorted(included | excluded)) + "\n",
                    text=True, capture_output=True,
                )
                with self.subTest(skill=skill):
                    self.assertIn(result.returncode, (0, 1), result.stderr)
                    ignored = set(result.stdout.splitlines())
                    self.assertEqual(included & ignored, set(), "required bundle files were excluded")
                    self.assertEqual(excluded - ignored, set(), "private/development files were included")


class ContentTest(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for path in public_files():
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), 1):
                with self.subTest(file=str(path.relative_to(ROOT)), line=number):
                    self.assertNotIn(EM_DASH, line, "em dash")
                    self.assertNotIn(EN_DASH, line, "en dash")

    def test_no_supplier_names_or_personal_emails(self):
        for path in public_files():
            if path.name == "test_skill_structure.py":
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertIsNone(SUPPLIER_RE.search(text), "supplier names must not be published")
                self.assertNotIn("@gmail.com", text, "use you@yourdomain.com or user@example.com")

    def test_json_examples_parse(self):
        for skill in SKILLS:
            for index, block in enumerate(code_blocks(skill_md(skill), "json")):
                with self.subTest(skill=skill, block=index):
                    try:
                        json.loads(block)
                    except json.JSONDecodeError as error:
                        self.fail(f"invalid JSON example: {error}\n{block[:300]}")

    def test_python_examples_compile(self):
        for skill in SKILLS:
            for index, block in enumerate(code_blocks(skill_md(skill), "python", "py")):
                with self.subTest(skill=skill, block=index):
                    compile(block, f"{skill}-example-{index}", "exec")

    def test_api_paths_keep_the_trailing_slash(self):
        for skill in SKILLS:
            for number, line in enumerate(skill_md(skill).splitlines(), 1):
                for path in API_PATH_RE.findall(line):
                    with self.subTest(skill=skill, line=number, path=path):
                        self.assertTrue(path.endswith("/"), "Didit API paths end with a slash")


class WebhookSignatureTest(unittest.TestCase):
    """The hub skill's verifier must accept signatures produced by Didit's signing code."""

    @classmethod
    def setUpClass(cls):
        namespace = {}
        sources = [
            block
            for block in code_blocks(skill_md("didit-verification-management"), "python", "py")
            if "def verify_webhook" in block
        ]
        if not sources:
            raise AssertionError("didit-verification-management must document a verify_webhook(...) Python function")
        exec(compile(sources[0], "verify_webhook_example", "exec"), namespace)
        cls.verify = staticmethod(namespace["verify_webhook"])

    def call(self, body, headers):
        return self.verify(body, headers, WEBHOOK_SECRET, now=int(WEBHOOK_HEADERS["X-Timestamp"]) + 30)

    def test_accepts_didit_signature_on_the_raw_body(self):
        self.assertTrue(self.call(WEBHOOK_RAW_BODY.encode(), dict(WEBHOOK_HEADERS)))

    def test_accepts_v2_after_middleware_re_encoding(self):
        reencoded = json.dumps(json.loads(WEBHOOK_RAW_BODY), ensure_ascii=False, indent=2)
        reencoded = reencoded.replace('"score": 87', '"score": 87.0')
        headers = {k: v for k, v in WEBHOOK_HEADERS.items() if k != "X-Signature"}
        self.assertTrue(self.call(reencoded.encode(), headers))

    def test_rejects_a_tampered_body(self):
        tampered = WEBHOOK_RAW_BODY.replace('"Approved","timestamp"', '"Declined","timestamp"')
        self.assertFalse(self.call(tampered.encode(), dict(WEBHOOK_HEADERS)))

    def test_rejects_a_stale_timestamp(self):
        stale = self.verify(WEBHOOK_RAW_BODY.encode(), dict(WEBHOOK_HEADERS), WEBHOOK_SECRET,
                            now=int(WEBHOOK_HEADERS["X-Timestamp"]) + 3600)
        self.assertFalse(stale)

    def test_vector_matches_the_documented_algorithm(self):
        expected = hmac.new(WEBHOOK_SECRET.encode(), WEBHOOK_RAW_BODY.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(expected, WEBHOOK_HEADERS["X-Signature"])


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
