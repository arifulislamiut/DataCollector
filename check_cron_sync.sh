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
