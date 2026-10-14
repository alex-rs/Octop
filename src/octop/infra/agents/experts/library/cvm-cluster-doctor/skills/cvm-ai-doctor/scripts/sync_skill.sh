#!/usr/bin/env bash
# sync_skill.sh — sync the cvm-ai-doctor core files to a target directory
# Excluded: docs/, _*-prefixed directories, hidden files/directories (.git, .venv, .workbuddy, etc.), generated-images/
# Usage:
#   ./scripts/sync_skill.sh                        # Sync to the default target
#   ./scripts/sync_skill.sh /path/to/target        # Sync to the given target
#   ./scripts/sync_skill.sh --dry-run               # Preview without actually copying
#   ./scripts/sync_skill.sh --dry-run /path/to/target

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_TARGET="$HOME/vstation/finnie/src/lightclaw/agent/skills/cvm-ai-doctor"

# ── Argument parsing ──────────────────────────────────────────
DRY_RUN=false
TARGET=""

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        *)         TARGET="$arg" ;;
    esac
done

TARGET="${TARGET:-$DEFAULT_TARGET}"

# ── Colors ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { printf "${CYAN}[INFO]${NC}  %s\n" "$*"; }
ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
err()   { printf "${RED}[ERR]${NC}   %s\n" "$*" >&2; }

# ── Check the source directory ────────────────────────────────────────
if [ ! -d "$SRC_DIR/.git" ]; then
    err "Source directory is not a git repository: $SRC_DIR"
    exit 1
fi

# ── Collect git version information ────────────────────────────────
cd "$SRC_DIR"
GIT_COMMIT=$(git rev-parse HEAD)
GIT_SHORT=$(git rev-parse --short HEAD)
GIT_AUTHOR=$(git log -1 --format='%an')
GIT_DATE=$(git log -1 --format='%ai')
GIT_SUBJECT=$(git log -1 --format='%s')
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GIT_DIRTY=$(git diff --quiet && git diff --cached --quiet && echo "clean" || echo "dirty")
GIT_COMMIT_COUNT=$(git rev-list --count HEAD)
SYNC_TIME=$(date '+%Y-%m-%d %H:%M:%S %z')

# ── Print the sync summary ──────────────────────────────────────
echo ""
info "cvm-ai-doctor skill sync tool"
echo "  Source:  $SRC_DIR"
echo "  Target:  $TARGET"
echo "  Branch:  $GIT_BRANCH"
echo "  Commit:  $GIT_SHORT ($GIT_SUBJECT)"
echo "  Status:  $GIT_DIRTY"
if $DRY_RUN; then
    warn "DRY-RUN mode — preview only, nothing is copied"
fi
echo ""

# ── rsync exclusion rules ────────────────────────────────────
# docs/          — development docs, not part of the skill release
# _*/            — archive/backup directories
# .*/            — hidden files/directories (.git, .venv, .workbuddy, .DS_Store)
# generated-images/ — AI-generated images, not part of the skill
# version.ini    — generated on the target side, not copied from the source
# AUDIT-*.txt    — development audit files, not part of the skill release
# AUDIT-*.md     — development audit reports, not part of the skill release
RSYNC_EXCLUDES=(
    --exclude='docs/'
    --exclude='_*/'
    --exclude='.*'
    --exclude='generated-images/'
    --exclude='version.ini'
    --exclude='AUDIT-*.txt'
    --exclude='AUDIT-*.md'
)

# ── Run the sync ──────────────────────────────────────────
if $DRY_RUN; then
    info "The following files will be synced:"
    rsync -avn --delete "${RSYNC_EXCLUDES[@]}" "$SRC_DIR/" "$TARGET/" 2>/dev/null \
        | grep -v '^\.' | grep -v '^$' | grep -v 'sent\|total\|sending' | head -50
    echo ""
    info "The above is a preview; drop --dry-run to actually run it"
    exit 0
fi

# Create the target directory
mkdir -p "$TARGET"

# rsync sync: mirror mode (--delete removes extra files on the target)
rsync -av --delete "${RSYNC_EXCLUDES[@]}" "$SRC_DIR/" "$TARGET/"

# ── Generate version.ini ─────────────────────────────────
cat > "$TARGET/version.ini" << EOF
[version]
commit       = $GIT_COMMIT
short        = $GIT_SHORT
branch       = $GIT_BRANCH
author       = $GIT_AUTHOR
date         = $GIT_DATE
subject      = $GIT_SUBJECT
commit_count = $GIT_COMMIT_COUNT
tree_status  = $GIT_DIRTY

[sync]
synced_at    = $SYNC_TIME
EOF

# ── Done ──────────────────────────────────────────────
echo ""
ok "Sync complete!"
echo ""
info "version.ini contents:"
cat "$TARGET/version.ini"
echo ""

# Remind the user if the worktree has uncommitted changes
if [ "$GIT_DIRTY" = "dirty" ]; then
    echo ""
    warn "The worktree has uncommitted changes; the synced files are the actual files on disk (including uncommitted modifications)"
    warn "tree_status=dirty in version.ini records this"
fi
