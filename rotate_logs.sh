#!/bin/bash
# Log rotation script for Host Controller

LOG_FILE="$HOME/host_controller.log"
STARTUP_LOG="$HOME/host_controller_startup.log"

# Rotate main log if it's larger than 10MB
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
    touch "$LOG_FILE"
    echo "$(date): Log rotated" >> "$LOG_FILE"
fi

# Keep only last 100 lines of startup log
if [ -f "$STARTUP_LOG" ]; then
    tail -n 100 "$STARTUP_LOG" > "${STARTUP_LOG}.tmp"
    mv "${STARTUP_LOG}.tmp" "$STARTUP_LOG"
fi
