#!/usr/bin/env bash
# ==============================================================================
# CVM Doctor Patrol — Start the local Dashboard service
# ==============================================================================
# Purpose: start a simple HTTP server so the Dashboard can load the local JSONL data
# Usage:
#   bash scripts/serve_dashboard.sh          # Start the service and open the browser
#   bash scripts/serve_dashboard.sh --port 9090  # Custom port
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${2:-8765}"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --port) shift; PORT="$1"; shift ;;
    esac
done

echo ""
printf "${BOLD}${CYAN}CVM Doctor Patrol Dashboard${NC}\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
echo ""
printf "  URL:  ${GREEN}http://localhost:${PORT}/docs/patrol-dashboard.html${NC}\n"
printf "  Data: ~/.lightclaw/stats/cvm-doctor.jsonl\n"
echo ""
printf "  ${BOLD}Press Ctrl+C to stop the service${NC}\n"
echo ""

# Open the browser (macOS / Linux)
if [ "$(uname -s)" = "Darwin" ]; then
    (sleep 1 && open "http://localhost:${PORT}/docs/patrol-dashboard.html") &
elif command -v xdg-open &>/dev/null; then
    (sleep 1 && xdg-open "http://localhost:${PORT}/docs/patrol-dashboard.html") &
fi

# Start the HTTP service
cd "$PROJECT_DIR"
if command -v python3 &>/dev/null; then
    python3 -m http.server "$PORT"
elif command -v python &>/dev/null; then
    python -m http.server "$PORT"
else
    echo "[ERR] Python not found; cannot start the HTTP service"
    echo "      Please install Python or open the file manually: file://${PROJECT_DIR}/docs/patrol-dashboard.html"
    exit 1
fi
