#!/usr/bin/env python3
"""
A4 auth operation log diagnostic script
Read and decrypt huisheng_auth.log, then show the latest record for each API category.
Encryption is identical to auth.py: sha256(device_token + aiScene), falling back to sha256(aiScene)
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path

AUTH_KEY = "meituan-c-user-auth"
LOG_FILE = Path(tempfile.gettempdir()) / "huisheng" / "huisheng_auth.log"
TOKEN_FILE = (
    Path(
        os.environ.get("OCTOP_AUTH_DIR")
        or Path.home() / ".workbuddy" / "credentials" / "meituan-living-deals-assistant"
    )
    / "token.json"
)
CONFIG_FILE = Path(__file__).parent / "config.json"


def _load_ai_scene() -> str:
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f).get("aiScene", "")
    except Exception:
        return ""


def _load_device_token() -> str:
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return json.load(f).get(AUTH_KEY, {}).get("device_token", "")
    except Exception:
        return ""


def decrypt(line: str, device_token: str, ai_scene: str) -> dict:
    """Decrypt one log line; the key is identical to _xor_encrypt in auth.py"""
    flag, hex_data = line.split(":", 1)
    seed = device_token + ai_scene if flag == "1" and device_token else ai_scene
    key = hashlib.sha256(seed.encode()).digest()
    raw = bytes(int(hex_data[i : i + 2], 16) ^ key[i // 2 % 32] for i in range(0, len(hex_data), 2))
    return json.loads(raw.decode("utf-8"))


def main():
    if not LOG_FILE.exists():
        print("Auth log does not exist; no operations recorded yet")
        return

    lines = [ln for ln in LOG_FILE.read_text(encoding="utf-8").strip().splitlines() if ln.strip()]
    if not lines:
        print("Auth log is empty")
        return

    ai_scene = _load_ai_scene()
    if not ai_scene:
        print(
            "Warning: cannot read aiScene, unable to decrypt the log (config.json missing or aiScene empty)"
        )
        return

    device_token = _load_device_token()

    actions = ["token-verify", "send-sms", "verify"]
    latest = {}
    for line in lines:
        try:
            # Plaintext line (written when ai_scene is empty; kept for compatibility with old data)
            if ":" not in line[:2]:
                entry = json.loads(line)
            else:
                entry = decrypt(line, device_token, ai_scene)
            a = entry.get("action", "")
            if a in actions:
                latest[a] = entry
        except Exception:
            pass

    for a in actions:
        if a in latest:
            e = latest[a]
            result = e.get("result", {})
            success = result.get("success", "-")
            code = result.get("code", "")
            error = result.get("error", "")
            req = e.get("request", {})
            resp = e.get("response", {})
            http_status = resp.get("http_status", "-") if isinstance(resp, dict) else "-"
            parts = [
                f"[{a}]",
                f"time={e.get('time', '-')}",
                f"phone={req.get('phone_masked', e.get('phone_masked', '-'))}",
                f"success={success}",
            ]
            if code != "":
                parts.append(f"code={code}")
            if error:
                parts.append(f"error={error}")
            if http_status != "-":
                parts.append(f"http_status={http_status}")
            print("  ".join(parts))
        else:
            print(f"[{a}] no records yet")


if __name__ == "__main__":
    main()
