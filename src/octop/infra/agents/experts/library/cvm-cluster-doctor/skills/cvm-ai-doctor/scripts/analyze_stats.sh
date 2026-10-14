#!/usr/bin/env bash
# ==============================================================================
# CVM Doctor Stats Analyzer
# ==============================================================================
# Analyze the cvm-doctor-stats.jsonl diagnostic statistics log
#
# Usage:
#   ./scripts/analyze_stats.sh                  # Analyze all data
#   ./scripts/analyze_stats.sh --today          # Today only
#   ./scripts/analyze_stats.sh --last 7d        # Last 7 days
#   ./scripts/analyze_stats.sh --last 30d       # Last 30 days
#   ./scripts/analyze_stats.sh --file /path/x   # Use a specific file
#   ./scripts/analyze_stats.sh --json           # Emit raw JSON (for programmatic consumption)
# ==============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
STATS_FILE="${HOME}/.lightclaw/stats/cvm-doctor.jsonl"

# ── Colors ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Dependency check ──────────────────────────────────────────
if ! command -v jq &>/dev/null; then
    printf "${RED}[ERR]${NC} jq is required, please install it first: brew install jq / apt install jq\n" >&2
    exit 1
fi

# ── Argument parsing ──────────────────────────────────────────
TIME_FILTER=""
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --today)
            TIME_FILTER=$(date -u +"%Y-%m-%d")
            shift ;;
        --last)
            shift
            DAYS="${1%d}"  # strip the d suffix
            if [[ "$(uname)" == "Darwin" ]]; then
                TIME_FILTER=$(date -u -v-${DAYS}d +"%Y-%m-%dT%H:%M:%SZ")
            else
                TIME_FILTER=$(date -u -d "${DAYS} days ago" +"%Y-%m-%dT%H:%M:%SZ")
            fi
            shift ;;
        --file)
            shift; STATS_FILE="$1"; shift ;;
        --json)
            JSON_OUTPUT=true; shift ;;
        *)
            printf "${RED}[ERR]${NC} Unknown argument: $1\n" >&2; exit 1 ;;
    esac
done

# ── Check file ──────────────────────────────────────────
if [ ! -f "$STATS_FILE" ]; then
    printf "${RED}[ERR]${NC} Stats file does not exist: $STATS_FILE\n" >&2
    printf "${DIM}Hint: it is generated automatically after one diagnostic run${NC}\n" >&2
    exit 1
fi

TOTAL_LINES=$(wc -l < "$STATS_FILE" | tr -d ' ')
if [ "$TOTAL_LINES" -eq 0 ]; then
    printf "${RED}[ERR]${NC} Stats file is empty\n" >&2
    exit 1
fi

# ── Build the jq filter ───────────────────────────────────
if [ -n "$TIME_FILTER" ]; then
    # For a date prefix (--today) use startswith; for a timestamp (--last) use >=
    if [[ "$TIME_FILTER" == *T* ]]; then
        JQ_FILTER="select(.ts >= \"$TIME_FILTER\")"
    else
        JQ_FILTER="select(.ts | startswith(\"$TIME_FILTER\"))"
    fi
else
    JQ_FILTER="."
fi

# Collect the filtered data into an array
FILTERED=$(jq -s "[.[] | $JQ_FILTER]" "$STATS_FILE")
COUNT=$(echo "$FILTERED" | jq 'length')

if [ "$COUNT" -eq 0 ]; then
    printf "${YELLOW}[WARN]${NC} No data in the specified time range\n"
    exit 0
fi

# ── JSON output mode ─────────────────────────────────────
if $JSON_OUTPUT; then
    echo "$FILTERED" | jq '{
        total: length,
        by_mode: (group_by(.mode) | map({key: .[0].mode, value: length}) | from_entries),
        by_severity: (group_by(.severity) | map({key: .[0].severity, value: length}) | from_entries),
        by_trigger: (group_by(.trigger) | map({key: .[0].trigger, value: length}) | from_entries),
        by_os: (group_by(.os) | map({key: .[0].os, value: length}) | from_entries),
        issues_found: [.[] | select(.issues_found > 0)] | length,
        issue_rate_pct: (([.[] | select(.issues_found > 0)] | length) * 100 / length),
        avg_duration_s: ([.[] | .duration_s] | add / length | . * 10 | round / 10),
        component_issues: (
            [.[] | .components | to_entries[] |
             .value as $v | (if ($v | type) == "object" then $v.status else $v end) as $st |
             select($st != "ok" and $st != "skipped")]
            | group_by(.key) | map({key: .[0].key, value: length}) | from_entries
        ),
        top_scenarios: (
            group_by(.scenario) | map({scenario: .[0].scenario, count: length})
            | sort_by(-.count) | .[0:5]
        ),
        time_range: {
            earliest: (sort_by(.ts) | first.ts),
            latest: (sort_by(.ts) | last.ts)
        }
    }'
    exit 0
fi

# ── Visual output ────────────────────────────────────────

# Helper: percentage bar
bar() {
    local pct=$1 width=20
    local filled=$(( pct * width / 100 ))
    local empty=$(( width - filled ))
    printf "["
    printf "%0.s█" $(seq 1 $filled 2>/dev/null) || true
    printf "%0.s░" $(seq 1 $empty 2>/dev/null) || true
    printf "] %d%%" "$pct"
}

# Helper: severity color
sev_color() {
    case "$1" in
        critical) printf "$RED" ;;
        warning)  printf "$YELLOW" ;;
        ok)       printf "$GREEN" ;;
        *)        printf "$NC" ;;
    esac
}

echo ""
printf "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}\n"
printf "${BOLD}${CYAN}  CVM Doctor Diagnostic Statistics Report${NC}\n"
printf "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}\n"

# ── 1. Overview ──────────────────────────────────────────
EARLIEST=$(echo "$FILTERED" | jq -r 'sort_by(.ts) | first.ts')
LATEST=$(echo "$FILTERED" | jq -r 'sort_by(.ts) | last.ts')
ISSUES=$(echo "$FILTERED" | jq '[.[] | select(.issues_found > 0)] | length')
AVG_DUR=$(echo "$FILTERED" | jq '[.[] | .duration_s] | add / length | . * 10 | round / 10')

echo ""
printf "${BOLD}  📊 Overview${NC}\n"
printf "  ─────────────────────────────────\n"
printf "  Total runs:    ${BOLD}%s${NC}\n" "$COUNT"
printf "  Issues found:  ${BOLD}%s${NC}" "$ISSUES"
if [ "$COUNT" -gt 0 ]; then
    RATE=$(echo "$FILTERED" | jq '([.[] | select(.issues_found > 0)] | length) * 100 / length | round')
    printf "  (issue rate %s%%)" "$RATE"
fi
echo ""
printf "  Avg duration:  ${BOLD}%s s${NC}\n" "$AVG_DUR"
printf "  Time range:    %s\n" "$EARLIEST"
printf "                 ~ %s\n" "$LATEST"

# ── 2. Distribution by mode ────────────────────────────────────
echo ""
printf "${BOLD}  🔍 Diagnostic mode${NC}\n"
printf "  ─────────────────────────────────\n"
echo "$FILTERED" | jq -r '
    group_by(.mode) | map({mode: .[0].mode, count: length})
    | sort_by(-.count)[] | "\(.mode) \(.count)"
' | while read mode cnt; do
    pct=$(( cnt * 100 / COUNT ))
    printf "  %-14s %4d  %s\n" "$mode" "$cnt" "$(bar $pct)"
done

# ── 3. Severity distribution ──────────────────────────────────
echo ""
printf "${BOLD}  🚦 Severity${NC}\n"
printf "  ─────────────────────────────────\n"
for sev in ok warning critical; do
    cnt=$(echo "$FILTERED" | jq "[.[] | select(.severity == \"$sev\")] | length")
    pct=$(( cnt * 100 / COUNT ))
    color=$(sev_color "$sev")
    printf "  ${color}%-14s${NC} %4d  %s\n" "$sev" "$cnt" "$(bar $pct)"
done

# ── 4. Component issue distribution ──────────────────────────────────
echo ""
printf "${BOLD}  🔧 Component issue statistics${NC}${DIM} (excluding ok and skipped)${NC}\n"
printf "  ─────────────────────────────────\n"
COMP_DATA=$(echo "$FILTERED" | jq -r '
    [.[] | .components | to_entries[] |
     .value as $v | (if ($v | type) == "object" then $v.status else $v end) as $st |
     select($st != "ok" and $st != "skipped") | {key, value: $st}]
    | group_by(.key) | map({component: .[0].key, total: length,
        warning: [.[] | select(.value == "warning")] | length,
        critical: [.[] | select(.value == "critical")] | length})
    | sort_by(-.total)[] | "\(.component) \(.total) \(.warning) \(.critical)"
')

if [ -z "$COMP_DATA" ]; then
    printf "  ${GREEN}✔ No component issues in any diagnostic${NC}\n"
else
    printf "  ${DIM}%-14s %6s %8s %8s${NC}\n" "Component" "Issues" "warning" "critical"
    echo "$COMP_DATA" | while read comp total warn crit; do
        printf "  %-14s %6d  ${YELLOW}%5d W${NC}  ${RED}%5d C${NC}\n" "$comp" "$total" "$warn" "$crit"
    done
fi

# ── 5. Trigger ──────────────────────────────────────
echo ""
printf "${BOLD}  ⚡ Trigger${NC}\n"
printf "  ─────────────────────────────────\n"
echo "$FILTERED" | jq -r '
    group_by(.trigger) | map({trigger: .[0].trigger, count: length})
    | sort_by(-.count)[] | "\(.trigger) \(.count)"
' | while read trig cnt; do
    pct=$(( cnt * 100 / COUNT ))
    printf "  %-14s %4d  %s\n" "$trig" "$cnt" "$(bar $pct)"
done

# ── 6. Top scenarios ──────────────────────────────────────
echo ""
printf "${BOLD}  📋 Top scenarios${NC}\n"
printf "  ─────────────────────────────────\n"
echo "$FILTERED" | jq -r '
    group_by(.scenario) | map({scenario: .[0].scenario, count: length})
    | sort_by(-.count) | .[0:10][] | "\(.scenario) \(.count)"
' | while read scenario cnt; do
    pct=$(( cnt * 100 / COUNT ))
    printf "  %-24s %4d  %s\n" "$scenario" "$cnt" "$(bar $pct)"
done

# ── 7. Daily trend (days with data in the last 7 days)────────
echo ""
printf "${BOLD}  📈 Daily trend${NC}${DIM} (with data in the last 7 days)${NC}\n"
printf "  ─────────────────────────────────\n"
echo "$FILTERED" | jq -r '
    [.[] | .date = (.ts | split("T")[0])]
    | group_by(.date) | map({
        date: .[0].date,
        total: length,
        issues: [.[] | select(.issues_found > 0)] | length
    }) | sort_by(.date) | .[-7:][]
    | "\(.date) \(.total) \(.issues)"
' | while read date total issues; do
    ok_cnt=$(( total - issues ))
    printf "  %s  runs %3d  " "$date" "$total"
    printf "${GREEN}✔ %d${NC}  " "$ok_cnt"
    if [ "$issues" -gt 0 ]; then
        printf "${RED}✘ %d${NC}" "$issues"
    else
        printf "✘ 0"
    fi
    echo ""
done

# ── 8. OS distribution ───────────────────────────────────────
OS_COUNT=$(echo "$FILTERED" | jq '[.[] | .os] | unique | length')
if [ "$OS_COUNT" -gt 1 ]; then
    echo ""
    printf "${BOLD}  💻 OS distribution${NC}\n"
    printf "  ─────────────────────────────────\n"
    echo "$FILTERED" | jq -r '
        group_by(.os) | map({os: .[0].os, count: length})
        | sort_by(-.count)[] | "\(.os) \(.count)"
    ' | while read os cnt; do
        pct=$(( cnt * 100 / COUNT ))
        printf "  %-14s %4d  %s\n" "$os" "$cnt" "$(bar $pct)"
    done
fi

echo ""
printf "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}\n"
printf "${DIM}  Data source: %s (%s records)${NC}\n" "$STATS_FILE" "$COUNT"
printf "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}\n"
echo ""
