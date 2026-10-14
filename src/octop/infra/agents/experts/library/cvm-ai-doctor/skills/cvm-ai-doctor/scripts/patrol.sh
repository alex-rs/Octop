#!/usr/bin/env bash
# ==============================================================================
# CVM Doctor Patrol — Periodic Lightweight Patrol
# ==============================================================================
# Purpose: run quick_scan.sh, parse the output, and store structured JSONL locally
# Storage: ~/.lightclaw/stats/cvm-doctor.jsonl (shared with log_stats.sh)
# Usage:
#   bash scripts/patrol.sh --up [seconds]  # One-shot start: daemon + Dashboard
#   bash scripts/patrol.sh --down          # Stop everything at once
#   bash scripts/patrol.sh                 # Run one patrol
#   bash scripts/patrol.sh --daemon 300    # Daemon mode, every 300 seconds
#   bash scripts/patrol.sh --status        # Show status
#   bash scripts/patrol.sh --stop          # Stop the daemon
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATS_DIR="${HOME}/.lightclaw/stats"
PATROL_DIR="${HOME}/.lightclaw/patrol"
HISTORY_FILE="${STATS_DIR}/cvm-doctor.jsonl"
PID_FILE="${PATROL_DIR}/patrol.pid"
LOG_FILE="${PATROL_DIR}/patrol.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Ensure the directories exist
mkdir -p "$STATS_DIR" "$PATROL_DIR"

# ── Helper functions ───────────────────────────────────────────

log_msg() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $*" >> "$LOG_FILE"
}

# Keep the most recent N days of data (7 days by default); old data is archived to a .old.gz backup
# Strategy: filter on the ts field (ISO8601); records past the retention window are written to the compressed backup and then removed
rotate_history() {
    local retention_days="${PATROL_RETENTION_DAYS:-7}"
    [ ! -f "$HISTORY_FILE" ] && return 0

    # Compute the cutoff timestamp (UTC)
    local cutoff
    if [ "$(uname)" = "Darwin" ]; then
        cutoff=$(date -u -v-"${retention_days}"d +"%Y-%m-%dT%H:%M:%SZ")
    else
        cutoff=$(date -u -d "${retention_days} days ago" +"%Y-%m-%dT%H:%M:%SZ")
    fi

    # Only run when old data exists, to avoid unnecessary I/O
    local old_count
    old_count=$(awk -v cut="$cutoff" '
        { if (match($0, /"ts":"[^"]*"/)) {
            ts = substr($0, RSTART+6, RLENGTH-7);
            if (ts < cut) count++
        } }
        END { print count+0 }
    ' "$HISTORY_FILE")

    if [ "$old_count" -eq 0 ]; then
        return 0
    fi

    local tmp_new="${HISTORY_FILE}.new.$$"
    local tmp_old="${HISTORY_FILE}.old.$$"

    awk -v cut="$cutoff" -v new="$tmp_new" -v old="$tmp_old" '
        {
            if (match($0, /"ts":"[^"]*"/)) {
                ts = substr($0, RSTART+6, RLENGTH-7);
                if (ts >= cut) print > new; else print > old;
            }
        }
    ' "$HISTORY_FILE"

    # Archive the old data (append to the gz backup)
    if [ -s "$tmp_old" ]; then
        gzip -c "$tmp_old" >> "${STATS_DIR}/cvm-doctor.old.jsonl.gz" 2>/dev/null || true
    fi

    # Replace the main file
    mv "$tmp_new" "$HISTORY_FILE" 2>/dev/null
    rm -f "$tmp_old"

    log_msg "Cleanup complete: archived ${old_count} old records (last ${retention_days} days retained)"
}

# Parse quick_scan.sh output and extract each component's status
parse_quick_scan() {
    local output="$1"
    local cpu_status="skipped" mem_status="skipped" disk_status="skipped" net_status="skipped"
    local cpu_detail="" mem_detail="" disk_detail="" net_detail=""

    # Extract CPU
    local in_cpu=false in_mem=false in_disk=false in_net=false
    while IFS= read -r line; do
        case "$line" in
            "--- CPU CHECK ---")    in_cpu=true;  in_mem=false; in_disk=false; in_net=false ;;
            "--- MEMORY CHECK ---") in_cpu=false; in_mem=true;  in_disk=false; in_net=false ;;
            "--- DISK CHECK ---")   in_cpu=false; in_mem=false; in_disk=true;  in_net=false ;;
            "--- NETWORK CHECK ---") in_cpu=false; in_mem=false; in_disk=false; in_net=true ;;
            "=== QUICK CHECK COMPLETE ===") break ;;
        esac

        if [[ "$line" == Status:* ]]; then
            local status
            status=$(echo "$line" | sed 's/Status: //' | tr '[:upper:]' '[:lower:]')
            if $in_cpu; then cpu_status="$status"; fi
            if $in_mem; then mem_status="$status"; fi
            if $in_disk; then disk_status="$status"; fi
            if $in_net; then net_status="$status"; fi
        fi

        if [[ "$line" == Reason:* ]]; then
            local reason
            reason=$(echo "$line" | sed 's/Reason: //')
            if $in_cpu; then cpu_detail="$reason"; fi
            if $in_mem; then mem_detail="$reason"; fi
            if $in_disk; then disk_detail="$reason"; fi
            if $in_net; then net_detail="$reason"; fi
        fi

        # Extract numeric metrics
        if $in_cpu && [[ "$line" == "CPU Cores:"* ]]; then
            cpu_detail="cores=$(echo "$line" | awk '{print $NF}') $cpu_detail"
        fi
        if $in_cpu && [[ "$line" == "Run Queue:"* ]]; then
            cpu_detail="queue=$(echo "$line" | awk '{print $NF}') $cpu_detail"
        fi
        if $in_mem && [[ "$line" == "Swap Used:"* ]]; then
            mem_detail="swap=$(echo "$line" | awk '{print $NF}') $mem_detail"
        fi
        if $in_disk && [[ "$line" == "I/O Wait:"* ]]; then
            disk_detail="iowait=$(echo "$line" | awk '{print $NF}') $disk_detail"
        fi
        if $in_net && [[ "$line" == "Total Drops:"* ]]; then
            net_detail="drops=$(echo "$line" | awk '{print $NF}') $net_detail"
        fi
    done <<< "$output"

    # Compute the overall severity and issue count
    local issues=0 severity="ok"
    for s in "$cpu_status" "$mem_status" "$disk_status" "$net_status"; do
        case "$s" in
            critical) issues=$((issues+1)); severity="critical" ;;
            warning)  issues=$((issues+1)); [ "$severity" != "critical" ] && severity="warning" ;;
        esac
    done

    # Get host information
    local hostname_val
    hostname_val=$(hostname 2>/dev/null || echo "unknown")
    local os_type
    os_type=$(uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]' || echo "unknown")
    local uptime_val
    if [ "$os_type" = "darwin" ]; then
        uptime_val=$(uptime | awk '{print $3,$4}' | sed 's/,//')
    else
        uptime_val=$(uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | sed 's/,//')
    fi

    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u)
    local ts_local
    ts_local=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date)

    # Clean the detail fields (trim leading/trailing whitespace)
    cpu_detail=$(echo "$cpu_detail" | sed 's/^ *//;s/ *$//')
    mem_detail=$(echo "$mem_detail" | sed 's/^ *//;s/ *$//')
    disk_detail=$(echo "$disk_detail" | sed 's/^ *//;s/ *$//')
    net_detail=$(echo "$net_detail" | sed 's/^ *//;s/ *$//')

    # Emit the JSON record (same schema as log_stats.sh, plus detail)
    printf '{"ts":"%s","ts_local":"%s","mode":"quick","scenario":"health_check","hostname":"%s","os":"%s","uptime":"%s","duration_s":%d,"components":{"cpu":{"status":"%s","detail":"%s"},"memory":{"status":"%s","detail":"%s"},"disk":{"status":"%s","detail":"%s"},"network":{"status":"%s","detail":"%s"}},"issues_found":%d,"severity":"%s","trigger":"patrol"}\n' \
        "$ts" "$ts_local" "$hostname_val" "$os_type" "$uptime_val" \
        "$SECONDS" \
        "$cpu_status" "$cpu_detail" \
        "$mem_status" "$mem_detail" \
        "$disk_status" "$disk_detail" \
        "$net_status" "$net_detail" \
        "$issues" "$severity"
}

# Run one patrol
run_patrol() {
    SECONDS=0
    local quick_scan="${SCRIPT_DIR}/quick_scan.sh"

    if [ ! -f "$quick_scan" ]; then
        printf "${RED}[ERR]${NC} quick_scan.sh not found: %s\n" "$quick_scan" >&2
        return 1
    fi

    # Run quick_scan (set trigger=patrol so log_stats.sh does not double-write)
    local output
    output=$(CVM_DOCTOR_TRIGGER=patrol bash "$quick_scan" 2>&1)
    local exit_code=$?

    if [ $exit_code -ne 0 ] && [ -z "$output" ]; then
        printf "${RED}[ERR]${NC} quick_scan.sh failed (exit=%d)\n" "$exit_code" >&2
        return 1
    fi

    # Parse and store
    local record
    record=$(parse_quick_scan "$output")

    echo "$record" >> "$HISTORY_FILE"
    log_msg "Patrol complete: $(echo "$record" | grep -o '"severity":"[^"]*"')"

    # Rotate after every patrol (only does work when old data exists)
    rotate_history

    # Also trim the log file (keep the last 1000 lines)
    if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE" | tr -d ' ')" -gt 2000 ]; then
        tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi

    # Brief output
    local severity
    severity=$(echo "$record" | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)
    local issues
    issues=$(echo "$record" | grep -o '"issues_found":[0-9]*' | cut -d: -f2)

    case "$severity" in
        ok)       printf "${GREEN}✅ Patrol OK${NC} — no issues (%ds)\n" "$SECONDS" ;;
        warning)  printf "${YELLOW}⚠️  Warnings found${NC} — %d component issues (%ds)\n" "$issues" "$SECONDS" ;;
        critical) printf "${RED}❌ Critical issues found${NC} — %d component issues (%ds)\n" "$issues" "$SECONDS" ;;
    esac
}

# ── Daemon mode ──────────────────────────────────────────

start_daemon() {
    local interval=$1

    # Check whether a daemon is already running
    if [ -f "$PID_FILE" ]; then
        local old_pid
        old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            printf "${YELLOW}[WARN]${NC} Patrol daemon already running (PID=%s)\n" "$old_pid"
            printf "       Stop command: bash %s/patrol.sh --stop\n" "$SCRIPT_DIR"
            return 1
        fi
    fi

    printf "${CYAN}🚀 Starting patrol daemon${NC}\n"
    printf "   Interval: %d seconds\n" "$interval"
    printf "   Data:     %s\n" "$HISTORY_FILE"
    printf "   Log:      %s\n" "$LOG_FILE"
    printf "   PID file: %s\n" "$PID_FILE"
    echo ""

    # Start in the background
    (
        echo $$ > "$PID_FILE"
        log_msg "Daemon started (PID=$$, interval=${interval}s)"

        trap 'log_msg "Daemon received stop signal"; rm -f "$PID_FILE"; exit 0' SIGTERM SIGINT

        while true; do
            run_patrol >> "$LOG_FILE" 2>&1
            sleep "$interval"
        done
    ) &

    local daemon_pid=$!
    echo "$daemon_pid" > "$PID_FILE"

    printf "${GREEN}✅ Patrol daemon started${NC} (PID=%d)\n" "$daemon_pid"
    printf "   Stop command: bash scripts/patrol.sh --stop\n"
    printf "   Show status:  bash scripts/patrol.sh --status\n"
}

stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        printf "${YELLOW}[WARN]${NC} No patrol daemon is running\n"
        return 0
    fi

    local pid
    pid=$(cat "$PID_FILE")

    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        rm -f "$PID_FILE"
        log_msg "Daemon stopped (PID=$pid)"
        printf "${GREEN}✅ Patrol daemon stopped${NC} (PID=%d)\n" "$pid"
    else
        rm -f "$PID_FILE"
        printf "${YELLOW}[WARN]${NC} Patrol daemon PID=%d no longer exists; removed the stale PID file\n" "$pid"
    fi
}

show_status() {
    printf "${BOLD}${CYAN}CVM Doctor Patrol Status${NC}\n"
    printf "────────────────────────────────────\n"

    # Daemon status
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            printf "  Daemon: ${GREEN}running${NC} (PID=%d)\n" "$pid"
        else
            printf "  Daemon: ${RED}stopped${NC} (stale PID file)\n"
        fi
    else
        printf "  Daemon: ${DIM}not running${NC}\n"
    fi

    # Data file status
    if [ -f "$HISTORY_FILE" ]; then
        local total_records
        total_records=$(wc -l < "$HISTORY_FILE" | tr -d ' ')
        local file_size
        file_size=$(du -h "$HISTORY_FILE" | awk '{print $1}')
        local last_ts
        last_ts=$(tail -1 "$HISTORY_FILE" | grep -o '"ts_local":"[^"]*"' | cut -d'"' -f4)
        local last_severity
        last_severity=$(tail -1 "$HISTORY_FILE" | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)

        printf "  Data file: %s\n" "$HISTORY_FILE"
        printf "  Total records: ${BOLD}%s${NC}\n" "$total_records"
        printf "  File size: %s\n" "$file_size"
        printf "  Last patrol: %s\n" "$last_ts"
        printf "  Last status: "
        case "$last_severity" in
            ok)       printf "${GREEN}ok${NC}\n" ;;
            warning)  printf "${YELLOW}warning${NC}\n" ;;
            critical) printf "${RED}critical${NC}\n" ;;
            *)        printf "${DIM}unknown${NC}\n" ;;
        esac
    else
        printf "  Data file: ${DIM}no data yet${NC}\n"
    fi

    echo ""
    printf "  Dashboard: file://%s/docs/patrol-dashboard.html\n" "$(cd "$SCRIPT_DIR/.." && pwd)"
}

# ── One-shot start/stop ──────────────────────────────────────────

SERVER_PID_FILE="${PATROL_DIR}/server.pid"
SERVER_PORT="${PATROL_PORT:-8765}"

start_all() {
    local interval="${1:-300}"

    # 1. Start the patrol daemon
    start_daemon "$interval"
    echo ""

    # 2. Start the Dashboard server
    local server_script="${SCRIPT_DIR}/patrol_server.py"
    if [ ! -f "$server_script" ]; then
        printf "${YELLOW}[WARN]${NC} patrol_server.py not found; skipping Dashboard startup\n"
        return 0
    fi

    # Check whether the port is in use
    if lsof -ti ":$SERVER_PORT" >/dev/null 2>&1; then
        local existing_pid
        existing_pid=$(lsof -ti ":$SERVER_PORT" | head -1)
        printf "${YELLOW}[WARN]${NC} Port %s is already used by PID=%s; skipping server startup\n" "$SERVER_PORT" "$existing_pid"
        echo "$existing_pid" > "$SERVER_PID_FILE"
    else
        nohup python3 "$server_script" --port "$SERVER_PORT" > "${PATROL_DIR}/server.log" 2>&1 &
        local server_pid=$!
        echo "$server_pid" > "$SERVER_PID_FILE"
        sleep 1
        printf "${GREEN}✅ Dashboard server started${NC} (PID=%d)\n" "$server_pid"
    fi

    echo ""
    printf "${BOLD}${CYAN}🌐 Dashboard: http://localhost:%s/docs/patrol-dashboard.html${NC}\n" "$SERVER_PORT"
    echo ""
    printf "  Stop everything: bash scripts/patrol.sh --down\n"
}

stop_all() {
    # 1. Stop the daemon
    stop_daemon

    # 2. Stop the server
    if [ -f "$SERVER_PID_FILE" ]; then
        local sp
        sp=$(cat "$SERVER_PID_FILE")
        if kill -0 "$sp" 2>/dev/null; then
            kill "$sp" 2>/dev/null
            printf "${GREEN}✅ Dashboard server stopped${NC} (PID=%d)\n" "$sp"
        fi
        rm -f "$SERVER_PID_FILE"
    fi
}

# ── Main logic ────────────────────────────────────────────

case "${1:-}" in
    --daemon)
        interval="${2:-300}"
        start_daemon "$interval"
        ;;
    --up)
        # One-shot start: daemon + Dashboard server
        interval="${2:-300}"
        start_all "$interval"
        ;;
    --down)
        stop_all
        ;;
    --stop)
        stop_daemon
        ;;
    --status)
        show_status
        ;;
    --rotate)
        rotate_history
        echo "Cleanup complete"
        ;;
    --help|-h)
        echo "CVM Doctor Patrol — Periodic Lightweight Patrol"
        echo ""
        echo "One-shot start/stop (recommended):"
        echo "  bash scripts/patrol.sh --up [seconds]  # Start the daemon + Dashboard"
        echo "  bash scripts/patrol.sh --down          # Stop everything"
        echo ""
        echo "Individual commands:"
        echo "  bash scripts/patrol.sh                 # Run one patrol"
        echo "  bash scripts/patrol.sh --daemon 300    # Start daemon mode only"
        echo "  bash scripts/patrol.sh --stop          # Stop the daemon"
        echo "  bash scripts/patrol.sh --status        # Show status"
        echo "  bash scripts/patrol.sh --rotate        # Manual cleanup (keep 7 days)"
        echo ""
        echo "Data storage: ~/.lightclaw/stats/cvm-doctor.jsonl (shared with stats)"
        echo "Retention: last 7 days (configurable via the PATROL_RETENTION_DAYS environment variable)"
        echo "Dashboard: http://localhost:8765/docs/patrol-dashboard.html"
        ;;
    *)
        run_patrol
        ;;
esac
