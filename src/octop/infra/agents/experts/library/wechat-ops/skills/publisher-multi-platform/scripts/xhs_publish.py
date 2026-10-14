#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx>=0.27.0",
#     "playwright>=1.40.0",
# ]
# ///
"""
XHS (social content platform/RedNote) Publisher — Publish content to Xiaohongshu

Based on ClawHub hi-yu/xhs skill v1.2.5 concept, implemented as a
standalone browser-automation publisher for the personal multi-platform
publishing workflow.

Usage:
    python3 xhs_publish.py <command> [options]

Commands:
    login           Login to Xiaohongshu (scan QR code)
    publish         Publish a note from Markdown file
    publish-text    Publish a text-only note
    check           Check login status and environment
    adapt           Adapt a Markdown article for XHS style (preview)

Environment:
    XHS_COOKIE_FILE     Path to cookie file (default: ~/.xhs-cookies.json)
    GEMINI_API_KEY      Gemini API key for AI cover generation (optional)
    IMG_API_KEY         Image generation API key (optional)
    HUNYUAN_API_KEY     Hunyuan API key for AI cover generation (optional)
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

XHS_BASE_URL = "https://www.xiaohongshu.com"
XHS_CREATOR_URL = "https://creator.xiaohongshu.com"
XHS_PUBLISH_URL = f"{XHS_CREATOR_URL}/publish/publish"
COOKIE_FILE = os.environ.get("XHS_COOKIE_FILE", os.path.expanduser("~/.xhs-cookies.json"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check_playwright_installed() -> bool:
    """Check if playwright and its browsers are installed."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401

        return True
    except ImportError:
        return False


def ensure_playwright():
    """Ensure playwright is installed and browsers are ready."""
    if not check_playwright_installed():
        print("Error: playwright is required. Install with:", file=sys.stderr)
        print("  pip install playwright", file=sys.stderr)
        print("  playwright install chromium", file=sys.stderr)
        sys.exit(1)


def save_cookies(cookies: list, path: str = COOKIE_FILE):
    """Save browser cookies to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    os.chmod(path, 0o600)
    print(f"  💾 Cookies saved to: {path}")


def load_cookies(path: str = COOKIE_FILE) -> list | None:
    """Load browser cookies from file."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def parse_frontmatter(md_path: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from a Markdown file."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    fm = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")

    return fm, match.group(2)


def md_to_xhs_text(md_body: str, title: str = "") -> str:
    """
    Convert Markdown body to XHS-friendly plain text.

    XHS notes are short-form, emoji-rich, and use hashtags.
    This strips Markdown syntax and adapts the format.
    """
    text = md_body

    # Remove images (will be handled separately)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Convert headers to bold text with emoji
    text = re.sub(r"^#{1,3}\s+(.+)$", r"📌 \1", text, flags=re.MULTILINE)
    text = re.sub(r"^#{4,6}\s+(.+)$", r"▪️ \1", text, flags=re.MULTILINE)

    # Convert bold
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)

    # Convert italic
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Convert inline code
    text = re.sub(r"`(.+?)`", r"「\1」", text)

    # Convert code blocks to simplified text
    text = re.sub(r"```[\w]*\n(.*?)```", r"💻 Code snippet:\n\1", text, flags=re.DOTALL)

    # Convert unordered lists
    text = re.sub(r"^[\-\*]\s+", "• ", text, flags=re.MULTILINE)

    # Convert ordered lists
    text = re.sub(r"^\d+\.\s+", "• ", text, flags=re.MULTILINE)

    # Convert links to text
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)

    # Convert blockquotes
    text = re.sub(r"^>\s*(.+)$", r"💬 \1", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim
    text = text.strip()

    # Prepend title if provided
    if title:
        text = f"{title}\n\n{text}"

    # Truncate to XHS limit (~1000 chars recommended, max ~2000)
    if len(text) > 1800:
        text = text[:1800] + "\n\n... 👆 See the Official Account article for the full content"

    return text


def extract_images_from_md(md_path: str) -> list[str]:
    """Extract image paths/URLs from Markdown file."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    images = re.findall(r"!\[.*?\]\((.+?)\)", content)

    # Also check frontmatter cover
    fm, _ = parse_frontmatter(md_path)
    cover = fm.get("cover", "")
    if cover and cover not in images:
        images.insert(0, cover)

    # Resolve relative paths
    md_dir = Path(md_path).parent
    resolved = []
    for img in images:
        if img.startswith(("http://", "https://")):
            resolved.append(img)
        else:
            abs_path = str(md_dir / img)
            if os.path.isfile(abs_path):
                resolved.append(abs_path)

    return resolved


def extract_hashtags(md_body: str, fm: dict) -> list[str]:
    """Extract or generate hashtags from content."""
    tags = []

    # Check frontmatter for tags/hashtags
    for key in ("tags", "hashtags", "xhs_tags"):
        val = fm.get(key, "")
        if val:
            tags.extend([t.strip().strip("#") for t in val.split(",")])

    # Auto-extract existing hashtags from body
    body_tags = re.findall(r"#(\w+)", md_body)
    tags.extend(body_tags)

    # Deduplicate
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)

    return unique[:10]  # XHS max ~10 tags


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_login(args):
    """Login to Xiaohongshu via QR code scan."""
    ensure_playwright()
    from playwright.sync_api import sync_playwright

    print("🔐 Launching the browser to log in to the social content platform...")
    print("   Scan the QR code with the social content platform app to log in\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        page.goto(f"{XHS_BASE_URL}/explore")
        page.wait_for_timeout(2000)

        # Wait for user to complete login
        print("⏳ Waiting for login to complete...")
        print("   The page redirects automatically once login succeeds.")
        print("   Press any key when done (or wait 120 seconds for the automatic timeout)...\n")

        try:
            # Wait for the page to show logged-in state
            # (e.g., user avatar or profile icon appears)
            page.wait_for_selector(
                'a[href*="/user/profile"], .user-avatar, .side-bar-user',
                timeout=120000,
            )
            print("✅ Login detected!")
        except Exception:
            print("⚠️  Login state not detected, saving the current cookies...")

        # Save cookies
        cookies = context.cookies()
        save_cookies(cookies)

        browser.close()

    print("\n✅ Login complete! Cookies saved.")
    print(f"   Cookie file: {COOKIE_FILE}")


def cmd_publish(args):
    """Publish a note from Markdown file to XHS."""
    ensure_playwright()
    from playwright.sync_api import sync_playwright

    md_file = args.file
    if not os.path.isfile(md_file):
        print(f"Error: File not found: {md_file}", file=sys.stderr)
        sys.exit(1)

    # Parse content
    fm, body = parse_frontmatter(md_file)
    title = fm.get("title", Path(md_file).stem)
    xhs_text = md_to_xhs_text(body, title)
    images = extract_images_from_md(md_file)
    hashtags = extract_hashtags(body, fm)

    # Load cookies
    cookies = load_cookies()
    if not cookies:
        print("❌ No login information found. Run the login command first:", file=sys.stderr)
        print(f"   python3 {__file__} login", file=sys.stderr)
        sys.exit(1)

    print("\n📱 Preparing to publish a social content platform note:")
    print(f"  Title: {title}")
    print(f"  Images: {len(images)}")
    print(f"  Tags: {', '.join('#' + t for t in hashtags) if hashtags else '(none)'}")
    print(f"  Body preview: {xhs_text[:100]}...")
    print()

    if not images:
        print("⚠️  A social content platform note should contain at least one image.")
        print("   Add a cover field to the frontmatter, or add images to the body.")
        if not args.force:
            print("   Use --force to skip this check.")
            sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )

        # Restore cookies
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            # Navigate to publish page
            print("  🌐 Opening the publish page...")
            page.goto(XHS_PUBLISH_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            # Check if we're logged in
            if "login" in page.url.lower() or "sign" in page.url.lower():
                print("  ❌ Cookie has expired, please log in again:", file=sys.stderr)
                print(f"     python3 {__file__} login", file=sys.stderr)
                browser.close()
                sys.exit(1)

            # Upload images
            if images:
                print(f"  🖼️  Uploading {len(images)} images...")
                file_input = page.locator('input[type="file"]').first
                for idx, img_path in enumerate(images):
                    if img_path.startswith(("http://", "https://")):
                        # Download remote image first
                        print(f"    ⬇️  Downloading remote image {idx + 1}...")
                        resp = httpx.get(img_path, timeout=30, follow_redirects=True)
                        if resp.status_code == 200:
                            import tempfile

                            ext = (
                                ".jpg" if "jpeg" in resp.headers.get("content-type", "") else ".png"
                            )
                            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                                tmp.write(resp.content)
                            img_path = tmp.name
                        else:
                            print(f"    ⚠️  Download failed, skipping: {img_path}")
                            continue

                    file_input.set_input_files(img_path)
                    page.wait_for_timeout(2000)
                    print(f"    ✅ Image {idx + 1}/{len(images)} uploaded")

                page.wait_for_timeout(3000)

            # Fill in title
            print("  📝 Filling in the title...")
            title_input = page.locator(
                '[placeholder*="标题"], .c-input_inner, input[name="title"]'
            ).first
            if title_input.is_visible():
                title_input.fill(title[:20])  # XHS title max 20 chars

            # Fill in content
            print("  📝 Filling in the body...")

            # Append hashtags
            text_with_tags = xhs_text
            if hashtags:
                tag_str = " ".join(f"#{t}" for t in hashtags)
                text_with_tags = f"{xhs_text}\n\n{tag_str}"

            content_area = page.locator(
                '[contenteditable="true"], .ql-editor, textarea[placeholder*="正文"]'
            ).first
            if content_area.is_visible():
                content_area.click()
                content_area.fill(text_with_tags)

            page.wait_for_timeout(2000)

            # Click publish button
            if not args.draft:
                print("  📤 Publishing...")
                publish_btn = page.locator(
                    'button:has-text("发布"), .publishBtn, button.css-k2sopx'
                ).first
                if publish_btn.is_visible():
                    publish_btn.click()
                    page.wait_for_timeout(5000)
                    print("  ✅ Note published!")
                else:
                    print("  ⚠️  Publish button not found, please click publish manually.")
                    page.wait_for_timeout(30000)
            else:
                print("  📋 Draft mode: content is filled in, please review and publish manually.")
                print("     The browser closes automatically in 30 seconds...")
                page.wait_for_timeout(30000)

        except Exception as e:
            print(f"  ❌ Error during publishing: {e}", file=sys.stderr)
            if not args.headless:
                print("  The browser stays open, please complete the operation manually...")
                page.wait_for_timeout(60000)
        finally:
            # Update cookies
            new_cookies = context.cookies()
            save_cookies(new_cookies)
            browser.close()


def cmd_adapt(args):
    """Preview how a Markdown article would look as XHS note."""
    md_file = args.file
    if not os.path.isfile(md_file):
        print(f"Error: File not found: {md_file}", file=sys.stderr)
        sys.exit(1)

    fm, body = parse_frontmatter(md_file)
    title = fm.get("title", Path(md_file).stem)
    xhs_text = md_to_xhs_text(body, title)
    images = extract_images_from_md(md_file)
    hashtags = extract_hashtags(body, fm)

    print("=" * 60)
    print("📱 Social content platform note preview")
    print("=" * 60)
    print(f"\n📌 Title: {title[:20]}")
    print(f"🖼️  Images: {len(images)}")
    if images:
        for i, img in enumerate(images[:5]):
            print(f"   {i + 1}. {img}")
        if len(images) > 5:
            print(f"   ... and {len(images) - 5} more")

    print(f"\n📝 Body ({len(xhs_text)} characters):\n")
    print(xhs_text)

    if hashtags:
        print(f"\n🏷️  Tags: {' '.join('#' + t for t in hashtags)}")

    print("\n" + "=" * 60)
    print(f"Characters: {len(xhs_text)}/1800  |  Images: {len(images)}")

    if len(xhs_text) > 1800:
        print(
            "⚠️  The body is too long and will be truncated when published. Trim the content or split it into multiple notes."
        )
    if not images:
        print("⚠️  No images. A social content platform note should contain at least one image.")


def cmd_check(args):
    """Check XHS publishing environment."""
    print("🔍 Social content platform publishing environment check\n")

    # 1. Playwright
    pw_ok = check_playwright_installed()
    status = "✅" if pw_ok else "❌"
    print(f"  {status} playwright: {'installed' if pw_ok else 'NOT installed'}")
    if not pw_ok:
        print("      Install: pip install playwright && playwright install chromium")

    # 2. Cookie file
    cookies = load_cookies()
    status = "✅" if cookies else "❌"
    print(
        f"  {status} Login status: {'logged in (cookies present)' if cookies else 'not logged in'}"
    )
    if cookies:
        print(f"      Cookie file: {COOKIE_FILE}")
        # Check cookie freshness
        mtime = os.path.getmtime(COOKIE_FILE)
        age_hours = (time.time() - mtime) / 3600
        if age_hours > 24:
            print(
                f"      ⚠️  Cookie is older than {int(age_hours)} hours, you may need to log in again"
            )
        else:
            print(f"      Last updated: {int(age_hours)} hours ago")

    # 3. AI cover generation API keys (optional)
    gemini = os.environ.get("GEMINI_API_KEY")
    img_api = os.environ.get("IMG_API_KEY")
    hunyuan = os.environ.get("HUNYUAN_API_KEY")

    if gemini or img_api or hunyuan:
        print("  ✅ AI cover generation: configured")
        if gemini:
            print("      GEMINI_API_KEY: ***set***")
        if img_api:
            print("      IMG_API_KEY: ***set***")
        if hunyuan:
            print("      HUNYUAN_API_KEY: ***set***")
    else:
        print("  ℹ️  AI cover generation: not configured (optional)")
        print(
            "      Configure any API key to enable it: GEMINI_API_KEY / IMG_API_KEY / HUNYUAN_API_KEY"
        )

    print()
    if not cookies:
        print("💡 Next step: run the login command to log in")
        print(f"   python3 {__file__} login")


def cmd_publish_text(args):
    """Publish a text-only note (no Markdown file needed)."""
    ensure_playwright()

    title = args.title
    text = args.text
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]

    cookies = load_cookies()
    if not cookies:
        print("❌ No login information found. Run the login command first:", file=sys.stderr)
        sys.exit(1)

    full_text = text
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
        full_text = f"{text}\n\n{tag_str}"

    print("\n📱 Preparing to publish a social content platform text-only note:")
    print(f"  Title: {title}")
    print(f"  Body: {full_text[:100]}...")
    print()

    # Use same browser automation logic as cmd_publish
    print(
        "ℹ️  A text-only note needs at least one image. Add images manually in the browser, then publish."
    )


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="xhs_publish",
        description="XHS Publisher — Publish content to Xiaohongshu (social content platform)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # login
    p = sub.add_parser("login", help="Login to XHS (scan QR code)")
    p.set_defaults(func=cmd_login)

    # publish
    p = sub.add_parser("publish", help="Publish Markdown file as XHS note")
    p.add_argument("file", help="Markdown file to publish")
    p.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    p.add_argument("--draft", action="store_true", help="Fill content but don't click publish")
    p.add_argument("--force", action="store_true", help="Skip image check")
    p.set_defaults(func=cmd_publish)

    # publish-text
    p = sub.add_parser("publish-text", help="Publish a text-only note")
    p.add_argument("--title", required=True, help="Note title")
    p.add_argument("--text", required=True, help="Note text content")
    p.add_argument("--tags", help="Comma-separated tags")
    p.set_defaults(func=cmd_publish_text)

    # adapt
    p = sub.add_parser("adapt", help="Preview Markdown adapted for XHS format")
    p.add_argument("file", help="Markdown file to preview")
    p.set_defaults(func=cmd_adapt)

    # check
    p = sub.add_parser("check", help="Check XHS publishing environment")
    p.set_defaults(func=cmd_check)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
