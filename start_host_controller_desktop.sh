#!/bin/bash

# Host Controller Desktop Startup Script - Terminal Mode
# Opens a terminal window and runs the application in it

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$HOME/host_controller_startup.log"
}

log_message "Host Controller desktop startup initiated (Terminal Mode)"

# Wait a bit for desktop to fully load
sleep 10

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

# Detect available terminal emulator
TERMINAL=""
if command -v gnome-terminal >/dev/null 2>&1; then
    TERMINAL="gnome-terminal"
elif command -v konsole >/dev/null 2>&1; then
    TERMINAL="konsole"
elif command -v xfce4-terminal >/dev/null 2>&1; then
    TERMINAL="xfce4-terminal"
elif command -v xterm >/dev/null 2>&1; then
    TERMINAL="xterm"
else
    log_message "ERROR: No terminal emulator found"
    exit 1
fi

log_message "Using terminal: $TERMINAL"

# Create a script to run inside the terminal
TERMINAL_SCRIPT="/tmp/host_controller_terminal.sh"
cat > "$TERMINAL_SCRIPT" << 'TERMINAL_EOF'
#!/bin/bash

echo "======================================"
echo "    Host Controller Terminal Mode     "
echo "======================================"
echo "Starting Host Controller..."
echo "Press Ctrl+C to stop"
echo "======================================"

# Change to script directory
cd "/home/groot/krnltech/DataCollector"

# Activate virtual environment if available
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "venv/bin/activate"
    PYTHON_CMD="venv/bin/python"
else
    echo "Using system Python..."
    PYTHON_CMD="python3"
fi

# Clean up any leftover files
rm -f "$HOME/host_controller.pid" "$HOME/host_controller_watchdog.sh"

echo "Starting application..."
echo "------------------------"

# Run Host Controller in foreground (visible in terminal)
"$PYTHON_CMD" "host_controller.py"

echo "Host Controller stopped."
read -p "Press Enter to close terminal..."
TERMINAL_EOF

chmod +x "$TERMINAL_SCRIPT"

# Launch terminal with the script based on terminal type
case "$TERMINAL" in
    "gnome-terminal")
        gnome-terminal --title="Host Controller" --geometry=120x30 -- bash -c "$TERMINAL_SCRIPT"
        ;;
    "konsole")
        konsole --title "Host Controller" -e bash -c "$TERMINAL_SCRIPT"
        ;;
    "xfce4-terminal")
        xfce4-terminal --title="Host Controller" --geometry=120x30 -e "bash -c '$TERMINAL_SCRIPT'"
        ;;
    "xterm")
        xterm -title "Host Controller" -geometry 120x30 -e bash -c "$TERMINAL_SCRIPT"
        ;;
esac

log_message "Terminal launched with Host Controller"
