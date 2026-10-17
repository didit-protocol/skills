#!/usr/bin/env python3
"""Didit Account Setup - Register, verify, resend the code, and log in programmatically.

Usage:
    python scripts/setup_account.py register <email>
    python scripts/setup_account.py verify <email> <code>
    python scripts/setup_account.py resend-otp <email>
    python scripts/setup_account.py login <email>

Environment:
    DIDIT_PASSWORD  Optional. The account password for register, resend-otp and login.
                    When it is not set, the script prompts for the password without echo.
    The endpoints themselves are unauthenticated; no API key is needed.

Examples:
    read -rs DIDIT_PASSWORD && export DIDIT_PASSWORD                  # optional
    python scripts/setup_account.py register you@yourdomain.com      # prompts if DIDIT_PASSWORD is unset
    python scripts/setup_account.py verify you@yourdomain.com A3K9F2
    python scripts/setup_account.py resend-otp you@yourdomain.com
    python scripts/setup_account.py login you@yourdomain.com

Notes:
    - Do not pass the password as a command-line argument. Other local users can read it
      in the process list, and it stays in shell history and agent logs (CWE-214).
      A positional password still works for backward compatibility, but prints a warning.
    - Password: at least 8 characters with an uppercase letter, a lowercase letter,
      a digit and a special character.
    - The 6-character code expires 10 minutes after the most recent code was sent.
    - `verify` prints the new application's api_key (use it as DIDIT_API_KEY).
"""
import argparse
import getpass
import json
import os
import sys

import requests

AUTH_BASE_URL = "https://apx.didit.me/auth/v2"
PASSWORD_HELP = ("Deprecated: exposes the password in the process list and shell history. "
                 "Omit it and set DIDIT_PASSWORD or enter it at the prompt.")


def _post(path: str, payload: dict, ok_statuses: tuple) -> dict:
    response = requests.post(
        f"{AUTH_BASE_URL}{path}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code in ok_statuses:
        return response.json()
    print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
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

    ver_p = sub.add_parser("verify", help="Verify the email with the code and get the API key")
    ver_p.add_argument("email", help="Email used during registration")
    ver_p.add_argument("code", help="6-character code from the email")

    resend_p = sub.add_parser("resend-otp", help="Email a new verification code to an unverified account")
    resend_p.add_argument("email", help="Email used during registration")
    resend_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    log_p = sub.add_parser("login", help="Log in to an existing account (Bearer tokens)")
    log_p.add_argument("email", help="Account email")
    log_p.add_argument("password", nargs="?", help=PASSWORD_HELP)

    args = parser.parse_args()

    if args.command == "register":
        result = register(args.email, _password(args))
        print(json.dumps(result, indent=2))
        print(f"\n--- Check {args.email} for your 6-character verification code (valid 10 minutes) ---")

    elif args.command == "verify":
        result = verify_email(args.email, args.code)
        print(json.dumps(result, indent=2))
        organization = result.get("organization") or {}
        application = result.get("application") or {}
        api_key = application.get("api_key", "")
        print("\n--- Account ready ---")
        print(f"Organization UUID: {organization.get('uuid')}")
        print(f"Application UUID:  {application.get('uuid')}")
        print(f"API key (application.api_key): {api_key}")
        print("\nSet it in your environment:")
        print(f'  export DIDIT_API_KEY="{api_key}"')

    elif args.command == "resend-otp":
        result = resend_otp(args.email, _password(args))
        print(json.dumps(result, indent=2))
        print(f"\n--- New code sent to {args.email} ---")

    elif args.command == "login":
        result = login(args.email, _password(args))
        if result.get("2fa_required"):
            print("This account requires a second factor, which the programmatic login cannot complete. "
                  "Sign in at https://business.didit.me instead.", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
        print(f"\n--- Login successful. Access token expires in {result.get('expires_in', '?')}s ---")


if __name__ == "__main__":
    main()
