#!/usr/bin/env python3
"""
CVM Doctor Patrol Server
========================
Lightweight HTTP service:
  - Static file serving (docs/, scripts/, etc.)
  - /api/patrol-data  → returns the JSONL file contents directly (JSON array)
  - /api/patrol-summary → returns an aggregated summary

Usage:
  python3 scripts/patrol_server.py              # default port 8765
  python3 scripts/patrol_server.py --port 9090  # custom port
"""

import argparse
import contextlib
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PATROL_FILE = Path.home() / ".lightclaw" / "stats" / "cvm-doctor.jsonl"


class PatrolHandler(SimpleHTTPRequestHandler):
    """Extend static file serving with API endpoints"""

    def do_GET(self):
        if self.path == "/api/patrol-data":
            self._serve_patrol_data()
        elif self.path == "/api/patrol-summary":
            self._serve_patrol_summary()
        elif self.path == "/api/health":
            self._json_response(
                {"status": "ok", "patrol_file": str(PATROL_FILE), "exists": PATROL_FILE.exists()}
            )
        else:
            super().do_GET()

    def _read_jsonl(self):
        records = []
        if PATROL_FILE.exists():
            with open(PATROL_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        with contextlib.suppress(json.JSONDecodeError):
                            records.append(json.loads(line))
        return records

    def _serve_patrol_data(self):
        """Return all patrol records (JSON array)"""
        records = self._read_jsonl()
        self._json_response(records)

    def _serve_patrol_summary(self):
        """Return the aggregated summary"""
        records = self._read_jsonl()
        total = len(records)
        if total == 0:
            self._json_response({"total": 0, "message": "no data"})
            return

        ok = sum(1 for r in records if r.get("severity") == "ok")
        warn = sum(1 for r in records if r.get("severity") == "warning")
        crit = sum(1 for r in records if r.get("severity") == "critical")

        comp_issues = {"cpu": 0, "memory": 0, "disk": 0, "network": 0}
        for r in records:
            comps = r.get("components", {})
            for c in comp_issues:
                s = (
                    comps.get(c, {}).get("status", "ok")
                    if isinstance(comps.get(c), dict)
                    else comps.get(c, "ok")
                )
                if s not in ("ok", "skipped"):
                    comp_issues[c] += 1

        self._json_response(
            {
                "total": total,
                "ok": ok,
                "warning": warn,
                "critical": crit,
                "health_rate": round(ok / total * 100, 1),
                "component_issues": comp_issues,
                "latest": records[-1] if records else None,
                "earliest_ts": records[0].get("ts") if records else None,
                "latest_ts": records[-1].get("ts") if records else None,
            }
        )

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silence API requests; only print non-API ones
        if "/api/" not in (args[0] if args else ""):
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description="CVM Doctor Patrol Server")
    parser.add_argument("--port", type=int, default=8765, help="Listening port (default 8765)")
    args = parser.parse_args()

    # Switch to the project root directory
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    server = HTTPServer(("0.0.0.0", args.port), PatrolHandler)

    print("\033[1;36mCVM Doctor Patrol Server\033[0m")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Dashboard:  \033[32mhttp://localhost:{args.port}/docs/patrol-dashboard.html\033[0m")
    print(f"  API:        http://localhost:{args.port}/api/patrol-data")
    print(f"  Data file:  {PATROL_FILE}")
    print(f"  Directory:  {project_root}")
    print("")
    print("  \033[1mCtrl+C to stop\033[0m")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        server.server_close()


if __name__ == "__main__":
    main()
