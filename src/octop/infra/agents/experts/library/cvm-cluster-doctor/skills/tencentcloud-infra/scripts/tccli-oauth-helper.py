#!/usr/bin/env python3
"""
tccli OAuth login helper

Solves the problem that tccli auth login --browser no cannot accept a verification code in non-interactive environments.

Usage:
  # Step 1: generate the authorization link
  python3 tccli-oauth-helper.py --get-url

  # Step 2: after the user opens the link and logs in, get the base64 verification code, then:
  python3 tccli-oauth-helper.py --code "<verification code>"

  # Or do it in one step (if you already have the verification code):
  python3 tccli-oauth-helper.py --code "eyJhY2Nlc3NUb2tlbi..."

  # Check credential status:
  python3 tccli-oauth-helper.py --status
"""

import argparse
import base64
import contextlib
import json
import os
import random
import string
import sys
import time
from urllib.parse import urlencode

# Try to dynamically import the constants from tccli
try:
    from tccli.oauth import _API_ENDPOINT, _APP_ID, _AUTH_URL, _DEFAULT_LANG, _REDIRECT_URL, _SITE
except (ImportError, AttributeError):
    # Use fallback defaults when tccli is not installed or the version is incompatible
    _APP_ID = 100038427476
    _AUTH_URL = "https://cloud.tencent.com/open/authorize"
    _REDIRECT_URL = "https://cli.cloud.tencent.com/oauth"
    _SITE = "cn"
    _DEFAULT_LANG = "zh-CN"
    _API_ENDPOINT = "https://cli.cloud.tencent.com"

# State file path
_STATE_FILE = os.path.expanduser("~/.tccli/.oauth_state")


def get_temp_cred(access_token, site):
    """Get temporary credentials (copied from tccli/oauth.py)"""
    import uuid

    import requests

    api_endpoint = _API_ENDPOINT + "/get_temp_cred"
    body = {
        "TraceId": str(uuid.uuid4()),
        "AccessToken": access_token,
        "Site": site,
    }
    http_response = requests.post(api_endpoint, json=body, verify=True)
    resp = http_response.json()

    if "Error" in resp:
        raise ValueError(f"get_temp_key: {json.dumps(resp)}")

    return {
        "secretId": resp["SecretId"],
        "secretKey": resp["SecretKey"],
        "token": resp["Token"],
        "expiresAt": resp["ExpiresAt"],
    }


def cred_path_of_profile(profile):
    """Credential file path"""
    return os.path.join(os.path.expanduser("~"), ".tccli", profile + ".credential")


def save_credential(token, new_cred, profile):
    """Save credentials (copied from tccli/oauth.py)"""
    cred_path = cred_path_of_profile(profile)

    # Make sure the directory exists
    os.makedirs(os.path.dirname(cred_path), exist_ok=True)

    cred = {
        "type": "oauth",
        "secretId": new_cred["secretId"],
        "secretKey": new_cred["secretKey"],
        "token": new_cred["token"],
        "expiresAt": new_cred["expiresAt"],
        "oauth": {
            "openId": token["openId"],
            "accessToken": token["accessToken"],
            "expiresAt": token["expiresAt"],
            "refreshToken": token["refreshToken"],
            "site": token["site"],
        },
    }
    with open(cred_path, "w") as cred_file:
        json.dump(cred, cred_file, indent=4)


def generate_state():
    """Generate a random state"""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(10))


def save_state(state):
    """Save the state to a file"""
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w") as f:
        json.dump({"state": state, "timestamp": time.time()}, f)


def load_state():
    """Load the state from a file"""
    try:
        with open(_STATE_FILE) as f:
            data = json.load(f)
            # Check whether it has expired (10 minutes)
            if time.time() - data.get("timestamp", 0) > 600:
                return None
            return data.get("state")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def clear_state():
    """Remove the state file"""
    with contextlib.suppress(FileNotFoundError):
        os.remove(_STATE_FILE)


def get_auth_url(state, language=_DEFAULT_LANG):
    """Build the authorization URL"""
    redirect_params = {
        "browser": "no",
        "lang": language,
        "site": _SITE,
    }
    redirect_query = urlencode(redirect_params)
    redirect_url = _REDIRECT_URL + "?" + redirect_query

    url_params = {
        "scope": "login",
        "app_id": _APP_ID,
        "redirect_url": redirect_url,
        "state": state,
    }
    url_query = urlencode(url_params)
    auth_url = _AUTH_URL + "?" + url_query

    # Replace "_" in the URL with "%5F" so that Markdown parsers do not
    # misread it as an italic marker (some clients' markdownToPlainText
    # swallow underscores).
    # "%5F" is a valid URL encoding of "_", HTTP servers decode it
    # automatically, and the behavior is exactly equivalent.
    auth_url = auth_url.replace("_", "%5F")

    return auth_url


def do_get_url(args):
    """Generate the authorization link"""
    state = generate_state()
    save_state(state)

    auth_url = get_auth_url(state)

    print("━" * 60)
    print("🔐 Tencent Cloud OAuth authorization login")
    print("━" * 60)
    print()
    print("Please open the following link in your browser to complete the login:")
    print()
    print(auth_url)
    print()
    print("━" * 60)
    print("After logging in, the page shows a base64-encoded verification code.")
    print("Copy that verification code, then run the following command to complete the login:")
    print()
    print('  python3 tccli-oauth-helper.py --code "<verification code>"')
    print()
    print("Or send it to the AI assistant and let it complete the login for you.")
    print("━" * 60)
    print()
    print(f"📌 State: {state} (valid for 10 minutes)")

    return 0


def do_login_with_code(args):
    """Complete the login with the verification code"""
    code = args.code.strip()
    profile = args.profile or "default"

    # Try to load the saved state
    saved_state = load_state()

    try:
        # Decode the verification code
        token_json = base64.b64decode(code)
        token = json.loads(token_json)
    except Exception as e:
        print(f"❌ Failed to parse the verification code: {e}")
        print()
        print("Make sure you copied the complete base64 verification code string.")
        return 1

    # Verify the state (if one was saved)
    token_state = token.get("state")
    if saved_state and token_state != saved_state:
        print("⚠️  Warning: state mismatch")
        print(f"   expected: {saved_state}")
        print(f"   actual: {token_state}")
        print()
        print("An old authorization link may have been used. Continuing to try...")

    try:
        # Get temporary credentials
        print("🔄 Obtaining temporary credentials...")
        cred = get_temp_cred(token["accessToken"], token.get("site", _SITE))

        # Save the credentials
        save_credential(token, cred, profile)
        clear_state()

        cred_path = cred_path_of_profile(profile)

        print()
        print("━" * 60)
        print("✅ OAuth login successful!")
        print("━" * 60)
        print(f"📌 Profile: {profile}")
        print(f"📌 Credential path: {cred_path}")
        print(
            f"📌 Expiration time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cred['expiresAt']))}"
        )
        print("━" * 60)
        print()
        print("You can now use tccli, for example:")
        print("  tccli cvm DescribeInstances --region ap-guangzhou")
        print()

        return 0

    except Exception as e:
        print(f"❌ Login failed: {e}")
        return 1


def do_status(args):
    """Check credential status"""
    profile = args.profile or "default"
    cred_path = cred_path_of_profile(profile)

    print("━" * 60)
    print("🔍 tccli credential status check")
    print("━" * 60)
    print(f"📌 Profile: {profile}")
    print(f"📌 Credential path: {cred_path}")
    print()

    if not os.path.exists(cred_path):
        print("❌ Credential file does not exist")
        print()
        print("Please run the OAuth login first:")
        print("  python3 tccli-oauth-helper.py --get-url")
        return 1

    try:
        with open(cred_path) as f:
            cred = json.load(f)

        cred_type = cred.get("type", "unknown")
        print(f"📌 Credential type: {cred_type}")

        if cred_type == "oauth":
            expires_at = cred.get("expiresAt", 0)
            now = time.time()

            if expires_at > now:
                remaining = expires_at - now
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                print(
                    f"📌 Expiration time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}"
                )
                print(f"📌 Time remaining: {hours} hours {minutes} minutes")
                print()
                print("✅ credential valid")
            else:
                print(
                    f"📌 Expiration time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}"
                )
                print()
                print("❌ Credential has expired; log in again")
                print()
                print("Please run: python3 tccli-oauth-helper.py --get-url")
                return 1
        else:
            # API key mode
            secret_id = cred.get("secretId", "")
            if secret_id:
                print(f"📌 SecretId: {secret_id[:8]}...{secret_id[-4:]}")
                print()
                print("✅ Using API key credentials")
            else:
                print("❌ Malformed credential file")
                return 1

    except Exception as e:
        print(f"❌ Failed to read the credentials: {e}")
        return 1

    print("━" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="tccli OAuth login helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate the authorization link
  python3 tccli-oauth-helper.py --get-url

  # Complete the login with the verification code
  python3 tccli-oauth-helper.py --code "eyJhY2Nlc3NUb2tlbi..."

  # Check credential status
  python3 tccli-oauth-helper.py --status

  # Use a specific profile
  python3 tccli-oauth-helper.py --code "<verification code>" --profile myprofile
""",
    )

    parser.add_argument(
        "--get-url", action="store_true", help="Generate the OAuth authorization link"
    )
    parser.add_argument(
        "--code", type=str, help="base64-encoded verification code used to complete the login"
    )
    parser.add_argument("--status", action="store_true", help="Check the current credential status")
    parser.add_argument(
        "--profile", type=str, default="default", help="Profile name (default: default)"
    )

    args = parser.parse_args()

    if args.get_url:
        return do_get_url(args)
    elif args.code:
        return do_login_with_code(args)
    elif args.status:
        return do_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
