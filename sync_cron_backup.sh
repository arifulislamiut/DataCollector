#!/bin/bash

# DataCollector Cron Sync Script
# Optimized for frequent crontab execution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION_DIR="$SCRIPT_DIR/collection"
LOG_FILE="$SCRIPT_DIR/sync_cron.log"
LOCK_FILE="/tmp/datacollector_cron_sync.lock"

# Quick log function (timestamp + message)
log() {
    echo "[$(date '+%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if already running (with timeout cleanup)
if [ -f "$LOCK_FILE" ]; then
    # Check if process is actually running
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        log "SKIP: Sync already running (PID: $PID)"
        exit 0
    else
        # Stale lock file, remove it
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Quick checks
[ ! -d "$COLLECTION_DIR" ] && { log "ERROR: Collection dir missing"; exit 1; }

# Count files to sync (for logging)
FILE_COUNT=$(find "$COLLECTION_DIR" -type f -newer "$LOCK_FILE" 2>/dev/null | wc -l)

log "Starting sync (checking $FILE_COUNT potential files)"

# Perform incremental sync with optimized settings (ORIGINAL VERSION)
rclone copy "$COLLECTION_DIR" gdrive:DataCollector/collection \
    --update \
    --fast-list \
    --transfers 3 \
    --checkers 6 \
    --contimeout 45s \
    --timeout 300s \
    --retries 2 \
    --low-level-retries 3 \
    --max-age 7d \
    --log-level ERROR \
    --stats 0 \
    2>>"$LOG_FILE"

SYNC_EXIT_CODE=$?

if [ $SYNC_EXIT_CODE -eq 0 ]; then
    log "✅ Sync completed successfully"
else
    log "❌ Sync failed (exit code: $SYNC_EXIT_CODE)"
fi

# Keep log file manageable (last 200 lines)
if [ -f "$LOG_FILE" ] && [ $(wc -l < "$LOG_FILE") -gt 200 ]; then
    tail -n 200 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

exit $SYNC_EXIT_CODE
