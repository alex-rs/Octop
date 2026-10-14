#!/usr/bin/env python3
"""
huisheng-coupon-tool auth module
Manages device_token (the uuid parameter used when ordering). Token validity is managed by the pt-passport CLI.

Usage examples:
  python auth.py get-device-token
  python auth.py logout
  python auth.py clear-device-token
"""

import argparse
import contextlib
import hashlib
import json
import random
import time
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────
AUTH_KEY = "meituan-c-user-auth"

# pt-passport client ID
CLIENT_ID = "c6f50b5a1e2f4e2bb00a3e2f58df3ced"


def _resolve_auth_file() -> Path:
    """
    Resolve the storage path across platforms, in priority order:
    1. The WORKBUDDY_AUTH_FILE environment variable (injected by run.js, highest priority)
    2. The OCTOP_AUTH_DIR environment variable (Octop multi-Agent isolation directory)
    3. ~/.workbuddy/credentials/meituan-living-deals-assistant/token.json
    """
    import os

    env_path = os.environ.get("WORKBUDDY_AUTH_FILE")
    if env_path:
        return Path(env_path)

    octop_dir = os.environ.get("OCTOP_AUTH_DIR")
    if octop_dir:
        return Path(octop_dir) / "token.json"

    return (
        Path.home() / ".workbuddy" / "credentials" / "meituan-living-deals-assistant" / "token.json"
    )


AUTH_FILE = _resolve_auth_file()


# ── Device ID generation ────────────────────────────────────────────────────────


def generate_device_token(seed: str) -> str:
    """
    Generate a unique device identifier (device_token).
    Algorithm: MD5(seed + millisecond timestamp + random integer 0~1000)
    device_token is bound to the device and is never overwritten once generated.
    """
    ts_ms = int(time.time() * 1000)
    rand_int = random.randint(0, 1000)
    raw = f"{seed}{ts_ms}{rand_int}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ── Storage operations ──────────────────────────────────────────────────────────


def load_auth() -> dict:
    if AUTH_FILE.exists():
        with open(AUTH_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_auth(data: dict):
    import os
    import stat

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with contextlib.suppress(OSError):
        os.chmod(AUTH_FILE, stat.S_IRUSR | stat.S_IWUSR)


def get_token_data() -> dict:
    return load_auth().get(AUTH_KEY, {})


def save_token_data(token_data: dict):
    auth = load_auth()
    auth[AUTH_KEY] = token_data
    save_auth(auth)


def _ensure_device_token(token_data: dict) -> str:
    """Ensure device_token exists; generate and persist it when missing, and return device_token"""
    dt = token_data.get("device_token", "")
    if not dt:
        dt = generate_device_token("huisheng")
        token_data["device_token"] = dt
        save_token_data(token_data)
    return dt


# ── Command: get-device-token ───────────────────────────────────────────


def cmd_get_device_token():
    """Get device_token, generating it automatically when missing"""
    token_data = get_token_data()
    device_token = _ensure_device_token(token_data)
    print(json.dumps({"success": True, "device_token": device_token}, ensure_ascii=False))


# ── Command: logout ─────────────────────────────────────────────────────


def cmd_logout():
    """Log out: clear the pt-passport CLI cache, keep device_token"""
    import subprocess

    # Clear the token cached locally by the pt-passport CLI
    cli_cleared = False
    import os

    env = os.environ.copy()
    # Clear NODE_OPTIONS: pt-passport is a node CLI, so avoid host-injected options polluting output or raising errors
    env["NODE_OPTIONS"] = ""
    env["PT_PASSPORT_AUTH_FILE"] = str(AUTH_FILE.parent / "pt_passport_auth.json")
    try:
        result = subprocess.run(
            ["pt-passport", "logout", "--client_id", CLIENT_ID],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        cli_cleared = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass  # CLI missing or timed out; ignore

    token_data = get_token_data()
    device_token = token_data.get("device_token", "")

    print(
        json.dumps(
            {
                "success": True,
                "message": "Logged out; you will need to authorize again next time",
                "device_token_preserved": bool(device_token),
                "cli_cache_cleared": cli_cleared,
            },
            ensure_ascii=False,
        )
    )


# ── Command: clear-device-token ─────────────────────────────────────────


def cmd_clear_device_token():
    """Clear the device identifier; call only when the user explicitly asks"""
    import subprocess

    token_data = get_token_data()
    had_device_token = bool(token_data.get("device_token"))

    # Clear device_token
    token_data["device_token"] = ""
    save_token_data(token_data)

    # Also clear the pt-passport CLI cache
    import os

    env = os.environ.copy()
    # Clear NODE_OPTIONS: pt-passport is a node CLI, so avoid host-injected options polluting output or raising errors
    env["NODE_OPTIONS"] = ""
    with contextlib.suppress(FileNotFoundError, subprocess.TimeoutExpired, OSError):
        subprocess.run(
            ["pt-passport", "logout", "--client_id", CLIENT_ID],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

    print(
        json.dumps(
            {
                "success": True,
                "message": "Device identifier cleared; a new device_token will be generated on the next login",
                "device_token_cleared": had_device_token,
            },
            ensure_ascii=False,
        )
    )


# ── Entry point ─────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="huisheng-coupon-tool auth module")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "get-device-token", help="Get/generate device_token (required for ordering)"
    )
    subparsers.add_parser(
        "logout", help="Log out and clear the pt-passport CLI cache (keeps device_token)"
    )
    subparsers.add_parser(
        "clear-device-token",
        help="Clear the device identifier; call only when the user explicitly asks",
    )

    args = parser.parse_args()

    if args.command == "get-device-token":
        cmd_get_device_token()
    elif args.command == "logout":
        cmd_logout()
    elif args.command == "clear-device-token":
        cmd_clear_device_token()


if __name__ == "__main__":
    main()
