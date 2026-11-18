#!/usr/bin/env python3
"""Offline checks for every skill in this repository. No network and no API key needed.

Checks that each skill keeps the repository format (frontmatter, naming, Getting Started),
that the README table and tree match the skills folder, that every script compiles and is
referenced, that code examples parse, that API paths keep their trailing slash, that no
withheld name or em dash slips in, and that the documented webhook signature verifier
accepts signatures produced by Didit's signing algorithm.

Usage:
    python3 tests/test_skill_structure.py
"""

import contextlib
import hashlib
import hmac
import importlib.util
import io
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

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
# Names that must never be published are NOT listed in this repository: it is
# public, and a list of them would publish them. `tests/data/withheld-names.digests`
# holds keyed digests (HMAC-SHA256) of those names, one per line. The key is the
# CI secret DIDIT_NAME_GUARD_KEY, so the digests cannot be turned back into names
# by trying candidates. With the key, every run of one to four consecutive words
# of every text file in the repository is compared, as whole words joined by one
# space, so a name that is also two ordinary words written together is matched
# only when it is written together; without it the check is
# skipped (a fork's pull request has no secrets), and a push to main requires it.
NAME_GUARD_DIGESTS = ROOT / "tests" / "data" / "withheld-names.digests"
NAME_GUARD_KEY = os.environ.get("DIDIT_NAME_GUARD_KEY", "")
NAME_GUARD_REQUIRED = os.environ.get("DIDIT_NAME_GUARD_REQUIRED", "") == "1"
NAME_GUARD_WORD_RE = re.compile(r"[a-z0-9]+")
NAME_GUARD_MAX_WORDS = 4
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".zip"}


def repository_text_files():
    """Every text file a clone or a plugin install puts on someone's disk."""
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(ROOT).parts:
            continue
        if path.suffix.lower() in BINARY_SUFFIXES or path == NAME_GUARD_DIGESTS:
            continue
        files.append(path)
    return files


def withheld_name_lines(text, key, digests, cache):
    """Line numbers where a run of 1 to 4 words is a withheld name. Never the words."""
    words = [(m.group(0), text.count("\n", 0, m.start()) + 1) for m in NAME_GUARD_WORD_RE.finditer(text.lower())]
    lines = []
    for size in range(1, NAME_GUARD_MAX_WORDS + 1):
        for start in range(len(words) - size + 1):
            joined = " ".join(word for word, _ in words[start : start + size])
            hit = cache.get(joined)
            if hit is None:
                hit = hmac.new(key, joined.encode("utf-8"), hashlib.sha256).hexdigest() in digests
                cache[joined] = hit
            if hit:
                lines.append(words[start][1])
    return sorted(set(lines))


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
        self.assertTrue(re.search(rf"\b{count} skills that teach AI agents\b", README), f"README intro must say {count} skills")
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

    def test_no_personal_emails(self):
        for path in public_files():
            if path.name == "test_skill_structure.py":
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertNotIn("@gmail.com", text, "use you@yourdomain.com or user@example.com")

    def test_no_withheld_names_anywhere_in_the_repository(self):
        digests = {line.strip() for line in NAME_GUARD_DIGESTS.read_text(encoding="utf-8").splitlines() if line.strip()}
        self.assertTrue(digests, "the digest file is empty")
        for digest in digests:
            self.assertRegex(digest, r"^[0-9a-f]{64}$", "the digest file holds digests only, never a name")
        if not NAME_GUARD_KEY:
            self.assertFalse(NAME_GUARD_REQUIRED, "DIDIT_NAME_GUARD_KEY is required on this run and is not set")
            self.skipTest("name guard skipped: DIDIT_NAME_GUARD_KEY is not set (CI on the repository sets it)")
        key = NAME_GUARD_KEY.encode("utf-8")
        cache = {}
        for path in repository_text_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            with self.subTest(file=str(path.relative_to(ROOT))):
                # The message names the file and the lines, never the words found.
                self.assertEqual(withheld_name_lines(text, key, digests, cache), [], "a withheld name is on these lines")

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


def load_setup_account():
    """Import setup_account.py without the network. A stub stands in for requests when it is missing."""
    path = SKILLS_DIR / "didit-verification-management" / "scripts" / "setup_account.py"
    stub = {} if importlib.util.find_spec("requests") else {"requests": types.ModuleType("requests")}
    with mock.patch.dict(sys.modules, stub):
        spec = importlib.util.spec_from_file_location("setup_account_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


# Synthetic credentials: long, distinctive values that are not real secrets.
FAKE_API_KEY = "dk_test_SYNTHETIC_api_key_value_0123456789abcdef"
FAKE_ACCESS = "eyJSYNTHETIC.access.token.value.0123456789abcdef"
FAKE_REFRESH = "rt_SYNTHETIC_refresh_token_value_0123456789abcdef"
FAKE_PASSWORD = "Synthetic-Passw0rd!-not-real"
VERIFY_RESPONSE = {
    "access_token": FAKE_ACCESS, "refresh_token": FAKE_REFRESH, "expires_in": 86400,
    "organization": {"uuid": "0b6f2c1e-3a4d-4e5f-9a8b-7c6d5e4f3a2b", "name": "Example"},
    "application": {"uuid": "1c7a3d2f-4b5e-4f60-8b9c-8d7e6f5a4b3c", "name": "Default", "client_id": "client-1",
                    "api_key": FAKE_API_KEY},
}
LOGIN_RESPONSE = {"access_token": FAKE_ACCESS, "refresh_token": FAKE_REFRESH, "expires_in": 86400}
FAKE_TEMP_TOKEN = "tt_SYNTHETIC_temp_token_value_0123456789abcdef"
SECRETS = (FAKE_API_KEY, FAKE_ACCESS, FAKE_REFRESH, FAKE_PASSWORD, FAKE_TEMP_TOKEN)


class SetupAccountSecretsTest(unittest.TestCase):
    """setup_account.py never prints a full credential unless --show-secrets is passed."""

    @classmethod
    def setUpClass(cls):
        cls.mod = load_setup_account()

    def assert_no_secret(self, text):
        for secret in SECRETS:
            self.assertNotIn(secret, text, "a full credential appeared in normal output")

    def test_masked_form_is_first_and_last_four(self):
        self.assertEqual(self.mod.mask_secret(FAKE_API_KEY), "dk_t...cdef")
        self.assertEqual(self.mod.mask_secret("short"), "****")

    def test_format_result_masks_every_command(self):
        cases = {
            "verify": VERIFY_RESPONSE,
            "login": LOGIN_RESPONSE,
            "register": {"message": "code sent", "password": FAKE_PASSWORD},
            "resend-otp": {"message": "code sent", "access_token": FAKE_ACCESS},
        }
        for command, response in cases.items():
            with self.subTest(command=command):
                output = self.mod.format_result(command, response, "user@example.com")
                self.assert_no_secret(output)
        self.assertIn("dk_t...cdef", self.mod.format_result("verify", VERIFY_RESPONSE, "user@example.com"))

    def test_show_secrets_prints_the_full_values(self):
        output = self.mod.format_result("verify", VERIFY_RESPONSE, "user@example.com", show_secrets=True)
        self.assertIn(FAKE_API_KEY, output)

    def run_main(self, argv, response=None, post=None):
        """Run main() with a mocked handler (or a mocked requests.post). Returns (exit code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        handler = {"verify": "verify_email", "login": "login", "register": "register"}.get(argv[0], "resend_otp")
        env = {"DIDIT_PASSWORD": FAKE_PASSWORD, "DIDIT_VERIFICATION_CODE": "A3K9F2"}
        patches = [mock.patch.object(sys, "argv", ["setup_account.py", *argv]),
                   mock.patch.dict(os.environ, env)]
        if post is not None:
            patches.append(mock.patch.object(self.mod, "requests", types.SimpleNamespace(post=post)))
        else:
            self.handler_mock = mock.MagicMock(return_value=response)
            patches.append(mock.patch.object(self.mod, handler, self.handler_mock))
        code = None
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            try:
                self.mod.main()
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def assert_streams_clean(self, result, *extra):
        """Both stdout and stderr are scanned, separately."""
        _, out, err = result
        for stream in (out, err):
            self.assert_no_secret(stream)
            for value in extra:
                self.assertNotIn(value, stream)

    def test_main_output_is_masked(self):
        result = self.run_main(["verify", "user@example.com"], VERIFY_RESPONSE)
        self.assertEqual(result[0], 0)
        self.assert_streams_clean(result)
        self.assertIn("dk_t...cdef", result[1])
        self.assert_streams_clean(self.run_main(["login", "user@example.com"], LOGIN_RESPONSE))

    def test_abbreviated_show_secrets_is_rejected(self):
        for flag in ("--show", "--show-s", "--sh"):
            with self.subTest(flag=flag):
                result = self.run_main(["login", "user@example.com", flag], LOGIN_RESPONSE)
                self.assertEqual(result[0], 2)
                self.assert_streams_clean(result)
        full = self.run_main(["login", "user@example.com", "--show-secrets"], LOGIN_RESPONSE)
        self.assertIn(FAKE_ACCESS, full[1])

    def fake_response(self, status, body=None, text=""):
        response = mock.MagicMock()
        response.status_code = status
        response.text = text
        if body is None:
            response.json.side_effect = ValueError("not json: " + text)
        else:
            response.json.return_value = body
        return response

    def test_non_json_error_body_is_not_echoed(self):
        body = f"<html>upstream failed {FAKE_ACCESS} trace-marker-123</html>"
        result = self.run_main(["login", "user@example.com"],
                               post=mock.MagicMock(return_value=self.fake_response(502, text=body)))
        self.assertEqual(result[0], 1)
        self.assert_streams_clean(result, "trace-marker-123", "<html>")
        self.assertIn("HTTP 502", result[2])

    def test_json_error_message_is_not_echoed(self):
        body = {"code": "invalid_credentials", "detail": f"bad password {FAKE_PASSWORD} detail-marker"}
        result = self.run_main(["login", "user@example.com"],
                               post=mock.MagicMock(return_value=self.fake_response(401, body=body)))
        self.assertEqual(result[0], 1)
        self.assert_streams_clean(result, "detail-marker")
        self.assertIn("invalid_credentials", result[2])

    def test_transport_exception_text_is_not_echoed(self):
        post = mock.MagicMock(side_effect=OSError(f"proxy said {FAKE_REFRESH} exc-marker"))
        result = self.run_main(["register", "user@example.com"], post=post)
        self.assertEqual(result[0], 1)
        self.assert_streams_clean(result, "exc-marker")

    def test_second_factor_temp_token_is_masked(self):
        challenge = {"2fa_required": True, "has_authenticator": True, "temp_token": FAKE_TEMP_TOKEN}
        for command in ("verify", "login"):
            for extra in ([], ["--show-secrets"]):
                with self.subTest(command=command, extra=extra):
                    result = self.run_main([command, "user@example.com", *extra], challenge)
                    self.assertEqual(result[0], 1)
                    self.assert_streams_clean(result, FAKE_TEMP_TOKEN)
                    self.assertIn("Second factor required", result[2])
                    self.assertNotIn("Account ready", result[1] + result[2])

    def test_sso_required_is_reported(self):
        body = {"code": "sso_required", "organization": {"name": "org-name-marker"}}
        result = self.run_main(["login", "user@example.com"],
                               post=mock.MagicMock(return_value=self.fake_response(403, body=body)))
        self.assertEqual(result[0], 1)
        self.assertIn("SSO required", result[2])
        self.assert_streams_clean(result, "org-name-marker")

    def test_write_env_stores_full_values_with_mode_0600(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text('OTHER="kept"\nDIDIT_API_KEY="old"\n', encoding="utf-8")
            result = self.run_main(["verify", "user@example.com", "--write-env", str(env_path)], VERIFY_RESPONSE)
            self.assertEqual(result[0], 0)
            self.assert_streams_clean(result)
            written = env_path.read_text(encoding="utf-8")
            parsed = read_dotenv(written)
            self.assertEqual(parsed["DIDIT_API_KEY"], FAKE_API_KEY)
            self.assertEqual(parsed["DIDIT_ACCESS_TOKEN"], FAKE_ACCESS)
            self.assertEqual(parsed["DIDIT_REFRESH_TOKEN"], FAKE_REFRESH)
            self.assertEqual(parsed["OTHER"], "kept")
            self.assertNotIn('DIDIT_API_KEY="old"', written)
            self.assertEqual(env_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), [".env"])

    def test_write_env_refuses_a_symlink_before_spending_the_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "real.env"
            real.write_text("UNTOUCHED=1\n", encoding="utf-8")
            link = Path(tmp) / ".env"
            link.symlink_to(real)
            result = self.run_main(["verify", "user@example.com", "--write-env", str(link)], VERIFY_RESPONSE)
            self.assertEqual(result[0], 1)
            self.assertIn("symlink", result[2])
            self.handler_mock.assert_not_called()
            self.assertTrue(link.is_symlink())
            self.assertEqual(real.read_text(encoding="utf-8"), "UNTOUCHED=1\n")
            self.assert_streams_clean(result)
            with self.assertRaises(self.mod.SetupError):
                self.mod.write_env(str(link), {"DIDIT_API_KEY": FAKE_API_KEY})
            self.assertNotIn(FAKE_API_KEY, real.read_text(encoding="utf-8"))

    def test_write_env_rejects_unsupported_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            for bad in ("has'quote", "has\nnewline", "a${HOME}b", "a\\\\b", "a b", 'a"b', "a#b", "a$b", "a`b", ""):
                with self.subTest(value=bad), self.assertRaises(self.mod.SetupError):
                    self.mod.write_env(str(env_path), {"DIDIT_API_KEY": bad})
            self.assertFalse(env_path.exists())

    def test_write_env_round_trips_through_a_dotenv_reader(self):
        values = {"DIDIT_API_KEY": "Ab9._~+/=-xyz", "DIDIT_ACCESS_TOKEN": FAKE_ACCESS, "DIDIT_REFRESH_TOKEN": "=lead"}
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("export OTHER=1\n", encoding="utf-8")
            self.mod.write_env(str(env_path), values)
            parsed = read_dotenv(env_path.read_text(encoding="utf-8"))
            for name, value in values.items():
                self.assertEqual(parsed[name], value)
            self.assertIn("DIDIT_API_KEY=Ab9._~+/=-xyz\n", env_path.read_text(encoding="utf-8"))

    def test_bad_value_with_write_env_fails_before_success_is_announced(self):
        response = dict(LOGIN_RESPONSE, access_token="bad token ${X}")
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            result = self.run_main(["login", "user@example.com", "--write-env", str(env_path)], response)
            self.assertEqual(result[0], 1)
            self.assertNotIn("Login successful", result[1])
            self.assertFalse(env_path.exists())

    def test_credential_in_an_error_code_is_not_echoed(self):
        body = {"code": FAKE_API_KEY}
        result = self.run_main(["login", "user@example.com"],
                               post=mock.MagicMock(return_value=self.fake_response(400, body=body)))
        self.assertEqual(result[0], 1)
        self.assert_streams_clean(result)
        self.assertIn("unknown_error", result[2])

    def test_credential_in_a_uuid_field_is_not_echoed(self):
        response = dict(VERIFY_RESPONSE, organization={"uuid": FAKE_REFRESH})
        result = self.run_main(["verify", "user@example.com", "--show-secrets"], response)
        self.assertEqual(result[0], 1)
        self.assertIn("unexpected response", result[2])
        self.assertNotIn("Account ready", result[1])
        self.assertEqual(self.mod.safe_uuid(FAKE_REFRESH), "(unavailable)")
        self.assertEqual(self.mod.safe_uuid("org-uuid"), "(unavailable)")
        self.assertEqual(self.mod.safe_uuid(VERIFY_RESPONSE["organization"]["uuid"]),
                         VERIFY_RESPONSE["organization"]["uuid"])

    def test_credentials_inside_a_list_under_a_credential_key_are_collected(self):
        found = self.mod.collect_credentials({"recovery_tokens": [FAKE_REFRESH, {"nested": "abc123secretvalue"}]})
        self.assertIn(FAKE_REFRESH, found)
        self.assertIn("abc123secretvalue", found)
        self.assertEqual(self.mod.guard_display(FAKE_REFRESH, found), self.mod.HIDDEN)

    def test_uuid_shaped_credential_repeated_in_a_display_id_is_hidden(self):
        token = "2d9e4f1a-6b7c-4d8e-9f0a-1b2c3d4e5f60"
        response = dict(VERIFY_RESPONSE, refresh_token=token,
                        organization={"uuid": token, "name": "Example"})
        result = self.run_main(["verify", "user@example.com"], response)
        self.assertEqual(result[0], 0)
        self.assert_streams_clean(result, token)
        self.assertIn("Organization UUID: [hidden]", result[1])
        self.assertIn(VERIFY_RESPONSE["application"]["uuid"], result[1])
        nested = dict(VERIFY_RESPONSE, extra={"deep": [{"client_secret": token}]},
                      organization={"uuid": token})
        output = self.mod.format_result("verify", nested, "user@example.com")
        self.assertNotIn(token, output)
        self.assertIn("Organization UUID: [hidden]", output)
        self.assertEqual(self.mod.guard_display("prefix-" + token, {token}), "[hidden]")

    def test_trailing_newline_is_rejected(self):
        uuid = VERIFY_RESPONSE["organization"]["uuid"]
        self.assertEqual(self.mod.safe_uuid(uuid + "\n"), "(unavailable)")
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            with self.assertRaises(self.mod.SetupError):
                self.mod.write_env(str(env_path), {"DIDIT_API_KEY": FAKE_API_KEY + "\n"})
            self.assertFalse(env_path.exists())
        response = dict(VERIFY_RESPONSE, organization={"uuid": uuid + "\n"})
        result = self.run_main(["verify", "user@example.com"], response)
        self.assertEqual(result[0], 1)
        self.assertIn("unexpected response", result[2])

    def test_known_error_codes_only(self):
        self.assertEqual(self.mod.safe_error_code("invalid_credentials"), "invalid_credentials")
        for value in (FAKE_ACCESS, "some_new_code", None, 7):
            self.assertEqual(self.mod.safe_error_code(value), "unknown_error")

    def test_email_is_echoed_only_when_it_matches(self):
        self.assertEqual(self.mod.safe_email("user@example.com", "user@example.com"), "user@example.com")
        self.assertNotIn(FAKE_ACCESS, self.mod.safe_email(FAKE_ACCESS, "user@example.com"))

    def test_empty_success_response_is_refused(self):
        for command in ("login", "verify"):
            for response in ({}, {"expires_in": 60}, {"access_token": FAKE_ACCESS}):
                with self.subTest(command=command, response=response):
                    result = self.run_main([command, "user@example.com"], response)
                    self.assertEqual(result[0], 1)
                    self.assertIn("unexpected response", result[2])
                    self.assertNotIn("successful", result[1])
                    self.assertNotIn("Account ready", result[1])
                    self.assert_streams_clean(result)


def read_dotenv(text):
    """Minimal dotenv reader: KEY=value, optional `export `, matching outer quotes stripped, # comments skipped."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key] = value
    return values


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
