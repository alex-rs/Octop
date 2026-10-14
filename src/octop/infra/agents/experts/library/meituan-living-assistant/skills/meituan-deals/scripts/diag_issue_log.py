#!/usr/bin/env python3
"""
A5 coupon issuance API log diagnostic script
Read and decrypt huisheng_issue.log, then show the latest record.
Encryption is identical to issue.py: sha256(device_token + aiScene), falling back to sha256(aiScene)
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path

AUTH_KEY = "meituan-c-user-auth"
LOG_FILE = Path(tempfile.gettempdir()) / "huisheng" / "huisheng_issue.log"
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
    """Decrypt one log line; the key is identical to _xor_encrypt in issue.py"""
    flag, hex_data = line.split(":", 1)
    seed = device_token + ai_scene if flag == "1" and device_token else ai_scene
    key = hashlib.sha256(seed.encode()).digest()
    raw = bytes(int(hex_data[i : i + 2], 16) ^ key[i // 2 % 32] for i in range(0, len(hex_data), 2))
    return json.loads(raw.decode("utf-8"))


def main():
    if not LOG_FILE.exists():
        print("Log file does not exist; no coupon issuance records yet")
        return

    lines = [ln for ln in LOG_FILE.read_text(encoding="utf-8").strip().splitlines() if ln.strip()]
    if not lines:
        print("Log file is empty")
        return

    ai_scene = _load_ai_scene()
    if not ai_scene:
        print(
            "Warning: cannot read aiScene, unable to decrypt the log (config.json missing or aiScene empty)"
        )
        return

    device_token = _load_device_token()
    last = lines[-1]

    try:
        entry = json.loads(last) if ":" not in last[:2] else decrypt(last, device_token, ai_scene)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Decryption failed: {e}")
        print(f"Raw content (first 200 chars): {last[:200]}")


if __name__ == "__main__":
    main()
