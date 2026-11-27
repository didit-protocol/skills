#!/usr/bin/env python3
"""Didit Account Setup - Register, verify, resend the code, and log in programmatically.

Usage:
    python scripts/setup_account.py register <email>
    python scripts/setup_account.py verify <email> [--write-env <path>] [--show-secrets]
    python scripts/setup_account.py resend-otp <email>
    python scripts/setup_account.py login <email> [--write-env <path>] [--show-secrets]

Environment:
    DIDIT_PASSWORD           Optional. The account password for register, resend-otp and login.
                             When it is not set, the script prompts for it without echo.
    DIDIT_VERIFICATION_CODE  Optional. The 6-character code for verify. When it is not set,
                             the script prompts for it without echo.
    The endpoints themselves are unauthenticated; no API key is needed.

Examples:
    read -rs DIDIT_PASSWORD && export DIDIT_PASSWORD                  # optional
    python scripts/setup_account.py register you@yourdomain.com      # prompts if DIDIT_PASSWORD is unset
    python scripts/setup_account.py verify you@yourdomain.com --write-env .env   # prompts for the code
    python scripts/setup_account.py resend-otp you@yourdomain.com
    python scripts/setup_account.py login you@yourdomain.com --write-env .env

Notes:
    - Do not pass the password or the code as a command-line argument. Other local users can
      read it in the process list, and it stays in shell history and agent logs (CWE-214).
      A positional password or code still works for backward compatibility, but prints a
      warning (the value has already been exposed by then).
    - Password: at least 8 characters with an uppercase letter, a lowercase letter,
      a digit and a special character.
    - The 6-character code expires 10 minutes after the most recent code was sent, and it
      works once. Pass --write-env on verify so the API key is saved the first time.
    - Output is a fixed summary: response bodies, server messages and exception text are never
      printed. A value from a response is echoed only after a structural check: UUIDs must be
      canonical 8-4-4-4-12 hex, error codes must be in a known list (anything else prints
      `unknown_error`), and an email is echoed only when it equals the one you passed. A display
      value that equals or contains any credential in the response (any value under a key
      matching token, secret, key or password, at any depth) prints as `[hidden]`. Success
      is announced only when the expected fields are present; otherwise the script says
      "unexpected response" and exits 1. Credentials in the summary are masked (first 4 and last
      4 characters; values under 12 characters are hidden completely). `--write-env <path>`
      writes the full API key and tokens to that file (mode 0600) as unquoted
      DIDIT_API_KEY=..., DIDIT_ACCESS_TOKEN=... and DIDIT_REFRESH_TOKEN=... lines; a value with
      any character outside [A-Za-z0-9._~+/=-] is refused, and so are a symlink or anything
      that is not a regular file.
      `--show-secrets` prints those credentials in full instead; use it only when you mean to,
      because terminals and agent logs keep it. Flags must be spelled out in full.
    - An account with a second factor, or one whose organization enforces SSO, cannot finish
      here: the script says so and exits 1. Sign in at https://business.didit.me instead.
"""
import argparse
import getpass
import os
import re
import stat
import sys
import tempfile

import requests

AUTH_BASE_URL = "https://apx.didit.me/auth/v2"
PASSWORD_HELP = ("Deprecated: exposes the password in the process list and shell history. "
                 "Omit it and set DIDIT_PASSWORD or enter it at the prompt.")
CODE_HELP = ("Deprecated: exposes the code in the process list and shell history. "
             "Omit it and set DIDIT_VERIFICATION_CODE or enter it at the prompt.")
CONSOLE_URL = "https://business.didit.me"

# Environment variable written by --write-env for each credential found in the response.
ENV_NAMES = (
    ("DIDIT_API_KEY", ("application", "api_key")),
    ("DIDIT_ACCESS_TOKEN", ("access_token",)),
    ("DIDIT_REFRESH_TOKEN", ("refresh_token",)),
)
LABELS = {
    "DIDIT_API_KEY": "API key (application.api_key)",
    "DIDIT_ACCESS_TOKEN": "Access token",
    "DIDIT_REFRESH_TOKEN": "Refresh token",
}
# A UUID from a response is echoed only in canonical 8-4-4-4-12 hex form.
# Always applied with fullmatch, so a trailing newline is rejected.
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# Error codes echoed from a response; any other value prints as unknown_error.
KNOWN_ERROR_CODES = frozenset({
    "bad_request", "invalid_credentials", "invalid_code", "code_expired", "invalid_password",
    "email_already_registered", "email_already_verified", "user_not_found", "not_found",
    "account_locked", "account_disabled", "too_many_requests", "throttled", "rate_limited",
    "sso_required", "forbidden", "unauthorized", "server_error", "temporarily_unavailable",
})
# Characters allowed in a credential written by --write-env (no quoting is ever needed).
ENV_VALUE_RE = re.compile(r"[A-Za-z0-9._~+/=-]+")  # applied with fullmatch: no trailing newline
# Response keys whose string values are treated as credentials, at any depth.
CREDENTIAL_KEY_RE = re.compile(r"token|secret|key|password", re.IGNORECASE)
HIDDEN = "[hidden]"
STATUS_HINTS = {
    400: "the request was rejected; check the email, password rules or code",
    401: "the email, password or code was not accepted",
    403: "the account is not allowed to sign in this way",
    404: "no matching pending account",
    409: "the email is already registered and verified; use login",
    429: "too many attempts; wait and try again",
}


class SetupError(Exception):
    """A failure whose message is fixed text written by this script (never server or OS text)."""


def mask_secret(value):
    """First 4 and last 4 characters of a credential; short values are hidden completely."""
    if not isinstance(value, str) or not value:
        return "(none)"
    if len(value) < 12:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def safe_uuid(value) -> str:
    return value if isinstance(value, str) and UUID_RE.fullmatch(value) else "(unavailable)"


def safe_error_code(value) -> str:
    return value if isinstance(value, str) and value in KNOWN_ERROR_CODES else "unknown_error"


def safe_email(value, supplied: str) -> str:
    """The email is echoed only when it is exactly the one the user passed."""
    return supplied if isinstance(value, str) and value == supplied else "the address you entered"


def collect_credentials(value) -> set:
    """Every credential-like string in a response, at any depth: the values of keys matching
    token|secret|key|password (api_key, access_token, refresh_token, temp_token, client_secret...)."""
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if CREDENTIAL_KEY_RE.search(str(key)):
                found |= _all_strings(item)
            else:
                found |= collect_credentials(item)
    elif isinstance(value, list):
        for item in value:
            found |= collect_credentials(item)
    return found


def _all_strings(value) -> set:
    """Every non-empty string under a credential key, whatever the nesting (string, list or object)."""
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, dict):
        return set().union(*[_all_strings(item) for item in value.values()]) if value else set()
    if isinstance(value, list):
        return set().union(*[_all_strings(item) for item in value]) if value else set()
    return set()


def guard_display(text: str, credentials: set) -> str:
    """A display value (id, email, code) is printed only when it neither equals nor contains a credential."""
    if not isinstance(text, str):
        return text
    return HIDDEN if any(secret in text for secret in credentials) else text


def missing_success_fields(command: str, result: dict) -> bool:
    """True when a verify or login response lacks the fields that mean it succeeded."""
    if command not in ("verify", "login"):
        return False
    found = credentials_from(result)
    if "DIDIT_ACCESS_TOKEN" not in found or "DIDIT_REFRESH_TOKEN" not in found:
        return True
    if command == "verify":
        organization = result.get("organization")
        application = result.get("application")
        if not (isinstance(organization, dict) and UUID_RE.fullmatch(str(organization.get("uuid", "")))):
            return True
        if not (isinstance(application, dict) and UUID_RE.fullmatch(str(application.get("uuid", "")))):
            return True
        if "DIDIT_API_KEY" not in found:
            return True
    return False


def credentials_from(result: dict) -> dict:
    """The credentials in a verify or login response, keyed by environment variable name."""
    found = {}
    for env_name, path in ENV_NAMES:
        value = result
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, str) and value:
            found[env_name] = value
    return found


def second_factor_message(result: dict) -> str:
    """Fixed text for a second-factor challenge. The temp_token is always masked."""
    lines = ["Second factor required: this account has a second factor, which this script cannot complete."]
    if "temp_token" in result:
        lines.append(f"temp_token (masked, expires in 5 minutes): {mask_secret(result.get('temp_token'))}")
    lines.append(f"Sign in at {CONSOLE_URL}, or use the Didit MCP server's device login.")
    return "\n".join(lines)


def format_result(command: str, result: dict, email: str, show_secrets: bool = False) -> str:
    """Allowlisted summary printed for one command. Credentials are masked unless show_secrets is True."""
    if not isinstance(result, dict):
        result = {}
    if result.get("2fa_required"):
        return second_factor_message(result)
    credentials = collect_credentials(result)
    if command == "register":
        return (f"Registered. Check {guard_display(safe_email(email, email), credentials)} for your 6-character "
                "verification code (valid 10 minutes).")
    if command == "resend-otp":
        return f"New code sent to {guard_display(safe_email(email, email), credentials)} (valid 10 minutes)."
    shown = (lambda value: value) if show_secrets else mask_secret
    lines = []
    if command == "verify":
        organization = result.get("organization") if isinstance(result.get("organization"), dict) else {}
        application = result.get("application") if isinstance(result.get("application"), dict) else {}
        lines.append("Account ready.")
        lines.append(f"Organization UUID: {guard_display(safe_uuid(organization.get('uuid')), credentials)}")
        lines.append(f"Application UUID:  {guard_display(safe_uuid(application.get('uuid')), credentials)}")
    elif command == "login":
        expires = result.get("expires_in")
        expires = expires if isinstance(expires, int) and not isinstance(expires, bool) else "?"
        lines.append(f"Login successful. Access token expires in {expires}s.")
    for env_name, value in credentials_from(result).items():
        lines.append(f"{LABELS[env_name]}: {shown(value)}")
    return "\n".join(lines)


def check_env_destination(path: str) -> str:
    """Absolute destination for --write-env. Refuses symlinks, non-regular files and missing directories."""
    target = os.path.abspath(os.path.expanduser(path))
    try:
        info = os.lstat(target)
    except FileNotFoundError:
        info = None
    if info is not None:
        if stat.S_ISLNK(info.st_mode):
            raise SetupError("--write-env refuses a symlink; pass the real file path.")
        if not stat.S_ISREG(info.st_mode):
            raise SetupError("--write-env needs a regular file.")
    if not os.path.isdir(os.path.dirname(target)):
        raise SetupError("--write-env: the directory does not exist.")
    return target


def _env_literal(name: str, value: str) -> str:
    """KEY=value, unquoted. Values outside [A-Za-z0-9._~+/=-] are refused so no quoting is needed."""
    if not isinstance(value, str) or not ENV_VALUE_RE.fullmatch(value):
        raise SetupError(f"{name} contains characters outside [A-Za-z0-9._~+/=-]; it was not written. "
                         "Create a key in the console instead.")
    return f"{name}={value}"


def _read_existing(target: str) -> str:
    """Contents of the existing destination, opened without following symlinks; '' if absent."""
    try:
        fd = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError:
        return ""
    except OSError:
        raise SetupError("--write-env could not open the destination (a symlink or unreadable file is refused).")
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise SetupError("--write-env needs a regular file.")
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(fd)
    return b"".join(chunks).decode("utf-8")


def write_env(path: str, values: dict) -> None:
    """Create or update an env file with mode 0600, replacing only the given variables.

    The destination is read without following symlinks, the new content goes to a 0600
    temporary file in the same directory, and os.replace swaps it in atomically.
    """
    target = check_env_destination(path)
    new_lines = [_env_literal(name, value) for name, value in values.items()]
    kept = [line for line in _read_existing(target).splitlines()
            if line.split("=", 1)[0].strip().removeprefix("export ").strip() not in values]
    directory = os.path.dirname(target)
    fd, tmp_path = tempfile.mkstemp(prefix=".didit-env-", dir=directory)  # created with mode 0600
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(kept + new_lines) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _post(path: str, payload: dict, ok_statuses: tuple) -> dict:
    """POST to the auth API. Failures raise SetupError with fixed text: no body or exception text."""
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}{path}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except Exception as exc:  # transport failure: report only the exception class
        raise SetupError(f"could not reach the Didit auth API ({type(exc).__name__}).") from None
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = None
    if status in ok_statuses:
        if not isinstance(body, dict):
            raise SetupError(f"HTTP {status} with a response that is not a JSON object.")
        return body
    code = body.get("code") if isinstance(body, dict) else None
    if status == 403 and code == "sso_required":
        raise SetupError("SSO required: this account's organization enforces SSO, so no token or API key "
                         f"is issued here. Sign in at {CONSOLE_URL} through the organization's SSO.")
    message = f"HTTP {status} ({guard_display(safe_error_code(code), collect_credentials(body))})"
    hint = STATUS_HINTS.get(status)
    raise SetupError(f"{message}: {hint}." if hint else f"{message}.")


def register(email: str, password: str) -> dict:
    """201 for a new account; 200 when the email is registered but not verified yet (a new code is sent)."""
    return _post("/programmatic/register/", {"email": email, "password": password, "signup_path": "cli"}, (200, 201))


def verify_email(email: str, code: str) -> dict:
    """Returns access_token, refresh_token, expires_in, organization{uuid,name},
    application{uuid,name,client_id,api_key}; or a second-factor challenge (2fa_required, temp_token)."""
    return _post("/programmatic/verify-email/", {"email": email, "code": code}, (200,))


def resend_otp(email: str, password: str) -> dict:
    """Send a new code to an unverified account (60 s cooldown per email)."""
    return _post("/programmatic/resend-otp/", {"email": email, "password": password}, (200,))


def login(email: str, password: str) -> dict:
    return _post("/programmatic/login/", {"email": email, "password": password}, (200,))


def _secret_input(positional, env_name: str, prompt: str, what: str) -> str:
    """A secret from the deprecated positional argument, the environment, or a no-echo prompt."""
    if positional:
        print(f"Warning: a {what} on the command line is visible in the process list and shell "
              f"history. Set {env_name} or omit it to be prompted.", file=sys.stderr)
        return positional
    value = os.environ.get(env_name)
    if not value and sys.stdin.isatty():
        try:
            value = getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            value = ""
    if not value:
        raise SetupError(f"no {what}. Set {env_name}, or run in a terminal to be prompted.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Didit account setup (programmatic registration)",
                                     allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)

    reg_p = sub.add_parser("register", allow_abbrev=False, help="Register a new account (emails a 6-character code)")
    reg_p.add_argument("email", help="Email address")
    reg_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    secrets_p = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    secrets_p.add_argument("--write-env", metavar="PATH",
                           help="Write the full API key and tokens to this env file (mode 0600)")
    secrets_p.add_argument("--show-secrets", action="store_true",
                           help="Print full credentials to stdout instead of masking them")

    ver_p = sub.add_parser("verify", parents=[secrets_p], allow_abbrev=False,
                           help="Verify the email with the code and get the API key")
    ver_p.add_argument("email", help="Email used during registration")
    ver_p.add_argument("code", nargs="?", help=CODE_HELP)

    resend_p = sub.add_parser("resend-otp", allow_abbrev=False,
                              help="Email a new verification code to an unverified account")
    resend_p.add_argument("email", help="Email used during registration")
    resend_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    log_p = sub.add_parser("login", parents=[secrets_p], allow_abbrev=False,
                           help="Log in to an existing account (Bearer tokens)")
    log_p.add_argument("email", help="Account email")
    log_p.add_argument("password", nargs="?", help=PASSWORD_HELP)
    return parser


def run(args) -> int:
    show_secrets = getattr(args, "show_secrets", False)
    env_path = getattr(args, "write_env", None)
    if env_path:
        check_env_destination(env_path)  # fail before the single-use code or the password is spent

    if args.command == "register":
        result = register(args.email, _secret_input(args.password, "DIDIT_PASSWORD", "Didit password: ", "password"))
    elif args.command == "verify":
        code = _secret_input(args.code, "DIDIT_VERIFICATION_CODE", "Verification code: ", "verification code")
        if not env_path and not show_secrets:
            print("Note: the code works once and the API key will be shown masked. To save it, stop now and "
                  "rerun with --write-env <path>. Otherwise create a key later in the console.", file=sys.stderr)
        result = verify_email(args.email, code)
    elif args.command == "resend-otp":
        result = resend_otp(args.email, _secret_input(args.password, "DIDIT_PASSWORD", "Didit password: ", "password"))
    else:
        result = login(args.email, _secret_input(args.password, "DIDIT_PASSWORD", "Didit password: ", "password"))

    if result.get("2fa_required"):
        print(second_factor_message(result), file=sys.stderr)
        return 1

    if missing_success_fields(args.command, result):
        raise SetupError("unexpected response: the expected fields are missing, so nothing was saved. "
                         f"Check the account at {CONSOLE_URL}.")

    if env_path:
        for name, value in credentials_from(result).items():
            _env_literal(name, value)  # refuse unsupported characters before announcing success

    print(format_result(args.command, result, args.email, show_secrets))

    if args.command in ("verify", "login"):
        values = credentials_from(result)
        if env_path and values:
            try:
                write_env(env_path, values)
            except OSError as exc:
                raise SetupError(f"could not write --write-env ({type(exc).__name__}). Run login --write-env "
                                 "<path> to get new tokens.") from None
            print(f"\nWrote {', '.join(values)} to {env_path} (mode 0600). Keep that file out of version control.")
        elif not show_secrets and values:
            print("\nCredentials are masked. Rerun login with --write-env <path> to save tokens to a file "
                  "readable only by you, or --show-secrets to print them.")
    return 0


def main():
    args = build_parser().parse_args()
    try:
        code = run(args)
    except SetupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
