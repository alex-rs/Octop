#!/usr/bin/env python3
"""
Local QR code generation fallback module
When the Meituan server-side getQrCodeImage API is unavailable/fails, generate the QR code locally with the qrcode library.

Output JSON:
  { ok: true, type: "image", imageUrl: "data:image/png;base64,..." }
  { ok: true, type: "ascii", ascii: "<ASCII-art QR code>" }
  { ok: false, error: "..." }

Usage:
  python qr_local.py <url> [--ascii]
"""

import base64
import io
import json
import sys


def generate_data_uri(url: str) -> dict:
    import qrcode

    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"ok": True, "type": "image", "imageUrl": "data:image/png;base64," + b64}


def generate_ascii(url: str) -> dict:
    import qrcode

    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=True)
    return {"ok": True, "type": "ascii", "ascii": buf.getvalue().rstrip("\n")}


def main():
    if len(sys.argv) < 2 or not sys.argv[1]:
        print(json.dumps({"ok": False, "error": "MISSING_URL"}))
        sys.exit(1)
    url = sys.argv[1]
    use_ascii = "--ascii" in sys.argv[2:]

    try:
        result = generate_ascii(url) if use_ascii else generate_data_uri(url)
    except ImportError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "QRCODE_LIB_MISSING",
                    "message": "qrcode library not installed. Run: pip install qrcode",
                }
            )
        )
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": "GENERATE_FAILED", "message": str(e)}))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
