#!/bin/bash

# DataCollector Crontab Setup Script
# Sets up automatic Google Drive sync using crontab

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync_cron.sh"

echo "=== DataCollector Crontab Setup ==="
echo

# Check if rclone is working
if ! rclone listremotes | grep -q "gdrive:"; then
    echo "❌ ERROR: googlepiz remote not found"
    echo "Please configure rclone first: rclone config"
    exit 1
fi

echo "✅ Rclone remote 'gdrive:' detected"

# Test basic connection
if ! rclone lsd gdrive: --max-depth 1 >/dev/null 2>&1; then
    echo "❌ ERROR: Cannot connect to Google Drive"
    echo "Try: rclone config reconnect gdrive:"
    exit 1
fi

echo "✅ Google Drive connection working"

# Create optimized sync script for cron
cat > "$SYNC_SCRIPT" << 'EOF'
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

# Perform incremental sync with optimized settings
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
EOF

chmod +x "$SYNC_SCRIPT"
echo "✅ Created sync script: sync_cron.sh"

# Test the sync script
echo
echo "Testing sync script..."
if "$SYNC_SCRIPT"; then
    echo "✅ Test sync successful"
else
    echo "❌ Test sync failed - please check configuration"
    exit 1
fi

echo
echo "=== Crontab Setup Options ==="
echo
echo "Choose your sync frequency:"
echo "1) Every 5 minutes  (*/5 * * * *)"
echo "2) Every 10 minutes (*/10 * * * *)"
echo "3) Every 15 minutes (*/15 * * * *)"
echo "4) Every 30 minutes (*/30 * * * *)"
echo "5) Every hour       (0 * * * *)"
echo "6) Custom schedule"
echo

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        CRON_SCHEDULE="*/5 * * * *"
        DESCRIPTION="every 5 minutes"
        ;;
    2)
        CRON_SCHEDULE="*/10 * * * *"
        DESCRIPTION="every 10 minutes"
        ;;
    3)
        CRON_SCHEDULE="*/15 * * * *"
        DESCRIPTION="every 15 minutes"
        ;;
    4)
        CRON_SCHEDULE="*/30 * * * *"
        DESCRIPTION="every 30 minutes"
        ;;
    5)
        CRON_SCHEDULE="0 * * * *"
        DESCRIPTION="every hour"
        ;;
    6)
        echo "Enter custom cron schedule (e.g., '0 8,12,18 * * *' for 8am, 12pm, 6pm):"
        read -p "Schedule: " CRON_SCHEDULE
        DESCRIPTION="custom schedule: $CRON_SCHEDULE"
        ;;
    *)
        echo "Invalid choice. Using default: every 15 minutes"
        CRON_SCHEDULE="*/15 * * * *"
        DESCRIPTION="every 15 minutes"
        ;;
esac

echo
echo "Setting up crontab to run $DESCRIPTION..."

# Backup existing crontab
if crontab -l >/dev/null 2>&1; then
    crontab -l > "$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    echo "✅ Backed up existing crontab"
fi

# Add new crontab entry
(crontab -l 2>/dev/null; echo "# DataCollector Google Drive sync - $DESCRIPTION") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $SYNC_SCRIPT >/dev/null 2>&1") | crontab -

echo "✅ Crontab configured successfully!"

echo
echo "=== Setup Complete ==="
echo
echo "📅 Schedule: $DESCRIPTION"
echo "📁 Sync script: $SYNC_SCRIPT"
echo "📊 Log file: sync_cron.log"
echo
echo "📋 Management Commands:"
echo "   • View crontab:    crontab -l"
echo "   • Edit crontab:    crontab -e"
echo "   • Check logs:      tail -f sync_cron.log"
echo "   • Manual sync:     ./sync_cron.sh"
echo "   • Remove cron:     crontab -e (delete DataCollector lines)"
echo

# Create monitoring script
cat > "$SCRIPT_DIR/check_cron_sync.sh" << 'EOF'
#!/bin/bash

echo "=== DataCollector Cron Sync Status ==="
echo "Current time: $(date)"
echo

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "sync_cron.sh"; then
    echo "✅ Crontab entry active:"
    crontab -l | grep -A1 -B1 "DataCollector\|sync_cron.sh"
else
    echo "❌ No crontab entry found"
fi

echo

# Check if sync is currently running
if [ -f "/tmp/datacollector_cron_sync.lock" ]; then
    PID=$(cat /tmp/datacollector_cron_sync.lock)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 Sync currently RUNNING (PID: $PID)"
    else
        echo "⚠️  Stale lock file detected"
    fi
else
    echo "⏸️  Sync not currently running"
fi

echo

# Show recent sync activity
if [ -f "sync_cron.log" ]; then
    echo "📋 Recent sync activity (last 10 entries):"
    tail -n 10 sync_cron.log
    echo
    
    # Show sync frequency
    RECENT_SYNCS=$(grep -c "Starting sync" sync_cron.log)
    echo "📊 Total syncs logged: $RECENT_SYNCS"
else
    echo "📋 No sync log found yet (sync hasn't run)"
fi

echo

# Check collection status
if [ -d "collection" ]; then
    FILES=$(find collection -type f | wc -l)
    SIZE=$(du -sh collection 2>/dev/null | cut -f1)
    echo "📁 Local collection: $FILES files, $SIZE"
else
    echo "📁 No collection folder found"
fi

echo
echo "=== End Status ==="
EOF

chmod +x "$SCRIPT_DIR/check_cron_sync.sh"

echo "💡 Created status checker: check_cron_sync.sh"
echo
echo "🚀 Your collection will now sync to Google Drive $DESCRIPTION!"
echo "   Next sync will occur within the scheduled interval."
echo "   Check status anytime with: ./check_cron_sync.sh"

# Show current status
echo
echo "Current status:"
"$SCRIPT_DIR/check_cron_sync.sh"