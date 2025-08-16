#!/bin/bash

# Host Controller Desktop Startup Script
# Runs when user logs into desktop environment

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$HOME/host_controller_startup.log"
}

log_message "Host Controller desktop startup initiated"

# Wait a bit for desktop to fully load
sleep 5

# Change to script directory
cd "/home/groot/krnltech/DataCollector"

# Activate virtual environment if available
if [ -n "/home/groot/krnltech/DataCollector/venv" ] && [ -f "/home/groot/krnltech/DataCollector/venv/bin/activate" ]; then
    log_message "Activating virtual environment: /home/groot/krnltech/DataCollector/venv"
    source "/home/groot/krnltech/DataCollector/venv/bin/activate"
    PYTHON_CMD="/home/groot/krnltech/DataCollector/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Check if already running
if pgrep -f "host_controller.py" > /dev/null; then
    log_message "Host Controller already running, exiting"
    exit 0
fi

# Start Host Controller
log_message "Starting Host Controller with $PYTHON_CMD"
"$PYTHON_CMD" "/home/groot/krnltech/DataCollector/host_controller.py" >> "$HOME/host_controller.log" 2>&1 &
PID=$!

# Save PID for monitoring
echo $PID > "$HOME/host_controller.pid"
log_message "Host Controller started with PID: $PID"

# Create a simple watchdog script
cat > "$HOME/host_controller_watchdog.sh" << 'WATCHDOG_EOF'
#!/bin/bash
while true; do
    if [ -f "$HOME/host_controller.pid" ]; then
        PID=$(cat "$HOME/host_controller.pid")
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "$(date '+%Y-%m-%d %H:%M:%S'): Host Controller died, restarting..." >> "$HOME/host_controller_startup.log"
            cd "/home/groot/krnltech/DataCollector"
            if [ -n "/home/groot/krnltech/DataCollector/venv" ] && [ -f "/home/groot/krnltech/DataCollector/venv/bin/activate" ]; then
                source "/home/groot/krnltech/DataCollector/venv/bin/activate"
                PYTHON_CMD="/home/groot/krnltech/DataCollector/venv/bin/python"
            else
                PYTHON_CMD="python3"
            fi
            "$PYTHON_CMD" "/home/groot/krnltech/DataCollector/host_controller.py" >> "$HOME/host_controller.log" 2>&1 &
            echo $! > "$HOME/host_controller.pid"
        fi
    fi
    sleep 30
done
WATCHDOG_EOF

chmod +x "$HOME/host_controller_watchdog.sh"

# Start watchdog in background
nohup "$HOME/host_controller_watchdog.sh" >/dev/null 2>&1 &

log_message "Host Controller startup complete with watchdog"
