#!/usr/bin/env python3
"""Didit Account Setup - Register, verify, resend the code, and log in programmatically.

Usage:
    python scripts/setup_account.py register <email>
    python scripts/setup_account.py verify <email> <code> [--write-env <path>] [--show-secrets]
    python scripts/setup_account.py resend-otp <email>
    python scripts/setup_account.py login <email> [--write-env <path>] [--show-secrets]

Environment:
    DIDIT_PASSWORD  Optional. The account password for register, resend-otp and login.
                    When it is not set, the script prompts for the password without echo.
    The endpoints themselves are unauthenticated; no API key is needed.

Examples:
    read -rs DIDIT_PASSWORD && export DIDIT_PASSWORD                  # optional
    python scripts/setup_account.py register you@yourdomain.com      # prompts if DIDIT_PASSWORD is unset
    python scripts/setup_account.py verify you@yourdomain.com A3K9F2 --write-env .env
    python scripts/setup_account.py resend-otp you@yourdomain.com
    python scripts/setup_account.py login you@yourdomain.com --write-env .env

Notes:
    - Do not pass the password as a command-line argument. Other local users can read it
      in the process list, and it stays in shell history and agent logs (CWE-214).
      A positional password still works for backward compatibility, but prints a warning.
    - Password: at least 8 characters with an uppercase letter, a lowercase letter,
      a digit and a special character.
    - The 6-character code expires 10 minutes after the most recent code was sent.
    - Output never contains a full API key, access token, refresh token or password: each one
      is shown masked (first 4 and last 4 characters). `--write-env <path>` writes the full
      values to that file (created or updated with mode 0600) as DIDIT_API_KEY,
      DIDIT_ACCESS_TOKEN and DIDIT_REFRESH_TOKEN. `--show-secrets` prints the full response to
      stdout instead; use it only when you mean to, because terminals and agent logs keep it.
"""
import argparse
import getpass
import json
import os
import sys
import tempfile

import requests

AUTH_BASE_URL = "https://apx.didit.me/auth/v2"
PASSWORD_HELP = ("Deprecated: exposes the password in the process list and shell history. "
                 "Omit it and set DIDIT_PASSWORD or enter it at the prompt.")

# Response fields whose values are credentials. They are masked in normal output.
SECRET_FIELDS = frozenset({
    "api_key", "access_token", "refresh_token", "id_token", "password", "client_secret", "secret",
})
# Environment variable written by --write-env for each credential found in the response.
ENV_NAMES = (
    ("DIDIT_API_KEY", ("application", "api_key")),
    ("DIDIT_ACCESS_TOKEN", ("access_token",)),
    ("DIDIT_REFRESH_TOKEN", ("refresh_token",)),
)


def mask_secret(value):
    """First 4 and last 4 characters of a credential; short values are hidden completely."""
    if not isinstance(value, str) or not value:
        return value
    if len(value) < 12:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def redact(value):
    """Deep copy of a response with every credential field masked."""
    if isinstance(value, dict):
        return {key: mask_secret(item) if key.lower() in SECRET_FIELDS and isinstance(item, str) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


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


def write_env(path: str, values: dict) -> None:
    """Create or update an env file with mode 0600, replacing only the given variables."""
    target = os.path.abspath(os.path.expanduser(path))
    kept = []
    if os.path.exists(target):
        with open(target, encoding="utf-8") as handle:
            kept = [line.rstrip("\n") for line in handle
                    if line.split("=", 1)[0].strip().removeprefix("export ").strip() not in values]
    lines = kept + [f'{name}="{value}"' for name, value in values.items()]
    directory = os.path.dirname(target) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".didit-env-", dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        os.replace(tmp_path, target)
        os.chmod(target, 0o600)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def format_result(command: str, result: dict, email: str, show_secrets: bool = False) -> str:
    """Text printed to stdout for one command. Credentials are masked unless show_secrets is True."""
    shown = result if show_secrets else redact(result)
    lines = [json.dumps(shown, indent=2)]
    if command == "register":
        lines.append(f"\n--- Check {email} for your 6-character verification code (valid 10 minutes) ---")
    elif command == "verify":
        organization = shown.get("organization") or {}
        application = shown.get("application") or {}
        lines.append("\n--- Account ready ---")
        lines.append(f"Organization UUID: {organization.get('uuid')}")
        lines.append(f"Application UUID:  {application.get('uuid')}")
        lines.append(f"API key (application.api_key): {application.get('api_key')}")
    elif command == "resend-otp":
        lines.append(f"\n--- New code sent to {email} ---")
    elif command == "login":
        lines.append(f"\n--- Login successful. Access token expires in {shown.get('expires_in', '?')}s ---")
    return "\n".join(lines)


def _post(path: str, payload: dict, ok_statuses: tuple) -> dict:
    response = requests.post(
        f"{AUTH_BASE_URL}{path}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code in ok_statuses:
        return response.json()
    try:
        detail = json.dumps(redact(response.json()))
    except ValueError:
        detail = response.text[:500]
    print(f"Error {response.status_code}: {detail}", file=sys.stderr)
    sys.exit(1)


def register(email: str, password: str) -> dict:
    """201 for a new account; 200 when the email is registered but not verified yet (a new code is sent)."""
    return _post("/programmatic/register/", {"email": email, "password": password, "signup_path": "cli"}, (200, 201))


def verify_email(email: str, code: str) -> dict:
    """Returns access_token, refresh_token, expires_in, organization{uuid,name},
    application{uuid,name,client_id,api_key}."""
    return _post("/programmatic/verify-email/", {"email": email, "code": code}, (200,))


def resend_otp(email: str, password: str) -> dict:
    """Send a new code to an unverified account (60 s cooldown per email)."""
    return _post("/programmatic/resend-otp/", {"email": email, "password": password}, (200,))


def login(email: str, password: str) -> dict:
    return _post("/programmatic/login/", {"email": email, "password": password}, (200,))


def _password(args) -> str:
    """Password from the deprecated positional argument, DIDIT_PASSWORD, or a no-echo prompt."""
    if args.password:
        print("Warning: a password on the command line is visible in the process list and shell "
              "history. Set DIDIT_PASSWORD or omit it to be prompted.", file=sys.stderr)
        return args.password
    password = os.environ.get("DIDIT_PASSWORD")
    if not password and sys.stdin.isatty():
        try:
            password = getpass.getpass("Didit password: ")
        except (EOFError, KeyboardInterrupt):
            password = ""
    if not password:
        print("Error: no password. Set DIDIT_PASSWORD, or run in a terminal to be prompted.", file=sys.stderr)
        sys.exit(1)
    return password


def main():
    parser = argparse.ArgumentParser(description="Didit account setup (programmatic registration)")
    sub = parser.add_subparsers(dest="command", required=True)

    reg_p = sub.add_parser("register", help="Register a new account (emails a 6-character code)")
    reg_p.add_argument("email", help="Email address")
    reg_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    secrets_p = argparse.ArgumentParser(add_help=False)
    secrets_p.add_argument("--write-env", metavar="PATH",
                           help="Write the full API key and tokens to this env file (mode 0600)")
    secrets_p.add_argument("--show-secrets", action="store_true",
                           help="Print full credentials to stdout instead of masking them")

    ver_p = sub.add_parser("verify", parents=[secrets_p], help="Verify the email with the code and get the API key")
    ver_p.add_argument("email", help="Email used during registration")
    ver_p.add_argument("code", help="6-character code from the email")

    resend_p = sub.add_parser("resend-otp", help="Email a new verification code to an unverified account")
    resend_p.add_argument("email", help="Email used during registration")
    resend_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    log_p = sub.add_parser("login", parents=[secrets_p], help="Log in to an existing account (Bearer tokens)")
    log_p.add_argument("email", help="Account email")
    log_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    args = parser.parse_args()
    show_secrets = getattr(args, "show_secrets", False)
    env_path = getattr(args, "write_env", None)

    if args.command == "register":
        result = register(args.email, _password(args))
    elif args.command == "verify":
        result = verify_email(args.email, args.code)
    elif args.command == "resend-otp":
        result = resend_otp(args.email, _password(args))
    else:
        result = login(args.email, _password(args))
        if result.get("2fa_required"):
            print("This account requires a second factor, which the programmatic login cannot complete. "
                  "Sign in at https://business.didit.me instead.", file=sys.stderr)
            sys.exit(1)

    print(format_result(args.command, result, args.email, show_secrets))

    if args.command in ("verify", "login"):
        values = credentials_from(result)
        if env_path and values:
            write_env(env_path, values)
            print(f"\nWrote {', '.join(values)} to {env_path} (mode 0600). Keep that file out of version control.")
        elif not show_secrets and values:
            print("\nCredentials are masked. Rerun with --write-env <path> to save them to a file "
                  "readable only by you, or --show-secrets to print them.")

if __name__ == "__main__":
    main()
