#!/bin/bash

# Industrial Desktop Auto-start Setup
# Creates desktop autostart for reliable GUI application startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Industrial Desktop Auto-start Setup${NC}"
echo "===================================="

# Get script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_CONTROLLER_PATH="$SCRIPT_DIR/host_controller.py"

# Check if host_controller.py exists
if [ ! -f "$HOST_CONTROLLER_PATH" ]; then
    echo -e "${RED}Error: host_controller.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Find virtual environment
VENV_PATH=""
for venv_name in "venv" ".venv" "env" ".env"; do
    if [ -d "$SCRIPT_DIR/$venv_name" ]; then
        VENV_PATH="$SCRIPT_DIR/$venv_name"
        echo -e "${GREEN}Found virtual environment: $VENV_PATH${NC}"
        break
    fi
done

# Create autostart directory
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create desktop entry for autostart
DESKTOP_FILE="$AUTOSTART_DIR/host-controller.desktop"
echo "Creating desktop autostart entry: $DESKTOP_FILE"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Host Controller
Comment=Industrial Host Controller for device monitoring and script execution
Exec=$SCRIPT_DIR/start_host_controller_desktop.sh
Icon=applications-system
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=System;
EOF

# Create the desktop startup script
DESKTOP_SCRIPT="$SCRIPT_DIR/start_host_controller_desktop.sh"
echo "Creating desktop startup script: $DESKTOP_SCRIPT"

cat > "$DESKTOP_SCRIPT" << EOF
#!/bin/bash

# Host Controller Desktop Startup Script
# Runs when user logs into desktop environment

# Logging function
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S'): \$1" >> "\$HOME/host_controller_startup.log"
}

log_message "Host Controller desktop startup initiated"

# Wait a bit for desktop to fully load
sleep 5

# Change to script directory
cd "$SCRIPT_DIR"

# Activate virtual environment if available
if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    log_message "Activating virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
    PYTHON_CMD="$VENV_PATH/bin/python"
else
    PYTHON_CMD="python3"
fi

# Check if already running
if pgrep -f "host_controller.py" > /dev/null; then
    log_message "Host Controller already running, exiting"
    exit 0
fi

# Start Host Controller
log_message "Starting Host Controller with \$PYTHON_CMD"
"\$PYTHON_CMD" "$HOST_CONTROLLER_PATH" >> "\$HOME/host_controller.log" 2>&1 &
PID=\$!

# Save PID for monitoring
echo \$PID > "\$HOME/host_controller.pid"
log_message "Host Controller started with PID: \$PID"

# Create a simple watchdog script
cat > "\$HOME/host_controller_watchdog.sh" << 'WATCHDOG_EOF'
#!/bin/bash
while true; do
    if [ -f "\$HOME/host_controller.pid" ]; then
        PID=\$(cat "\$HOME/host_controller.pid")
        if ! kill -0 "\$PID" 2>/dev/null; then
            echo "\$(date '+%Y-%m-%d %H:%M:%S'): Host Controller died, restarting..." >> "\$HOME/host_controller_startup.log"
            cd "$SCRIPT_DIR"
            if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
                source "$VENV_PATH/bin/activate"
                PYTHON_CMD="$VENV_PATH/bin/python"
            else
                PYTHON_CMD="python3"
            fi
            "\$PYTHON_CMD" "$HOST_CONTROLLER_PATH" >> "\$HOME/host_controller.log" 2>&1 &
            echo \$! > "\$HOME/host_controller.pid"
        fi
    fi
    sleep 30
done
WATCHDOG_EOF

chmod +x "\$HOME/host_controller_watchdog.sh"

# Start watchdog in background
nohup "\$HOME/host_controller_watchdog.sh" >/dev/null 2>&1 &

log_message "Host Controller startup complete with watchdog"
EOF

chmod +x "$DESKTOP_SCRIPT"
echo -e "${GREEN}✓${NC} Desktop startup script created"

# Disable the systemd service if it exists
if systemctl is-enabled host-controller >/dev/null 2>&1; then
    echo "Disabling systemd service in favor of desktop autostart..."
    sudo systemctl disable host-controller >/dev/null 2>&1 || true
    sudo systemctl stop host-controller >/dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Systemd service disabled"
fi

echo ""
echo -e "${GREEN}Industrial Desktop Auto-start Setup Complete!${NC}"
echo "================================================="
echo "• Host Controller will start when you log into desktop"
echo "• Desktop entry: $DESKTOP_FILE"
echo "• Startup script: $DESKTOP_SCRIPT"
echo "• Logs: ~/host_controller.log"
echo "• Startup logs: ~/host_controller_startup.log"
if [ -n "$VENV_PATH" ]; then
    echo "• Virtual environment: $VENV_PATH"
fi
echo ""
echo -e "${YELLOW}Features:${NC}"
echo "• ✓ Automatic restart if application crashes (watchdog)"
echo "• ✓ Prevents multiple instances"
echo "• ✓ Starts with desktop environment"
echo "• ✓ Full logging and monitoring"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo "• Test now: $DESKTOP_SCRIPT"
echo "• Stop: pkill -f host_controller.py"
echo "• View logs: tail -f ~/host_controller.log"
echo "• View startup logs: tail -f ~/host_controller_startup.log"
echo "• Remove autostart: rm $DESKTOP_FILE"
echo ""
echo -e "${GREEN}Perfect for industrial environments!${NC}"
echo "The application will reliably start every time you boot and log in."
