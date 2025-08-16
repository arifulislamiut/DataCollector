# Hardware Setup Guide

This guide describes how to set up the hardware components and configure automatic startup for the Host Controller application in an industrial environment.

## Overview

This system consists of:
- **Input Device**: 8 push buttons connected to an ESP32/NodeMCU
- **Host Controller**: PyQt5 application that receives commands and controls scripts
- **Stable Device Access**: udev rules for consistent device addressing
- **Auto-start**: Desktop application that starts automatically on boot

---

## Hardware Setup

### Input Device Configuration

**Push Button Connections:**
- 8 push buttons connected to GPIO pins: `4, 5, 6, 7, 15, 16, 17, 18`
- **Wiring**: Each button connects to 3.3V when pressed, with external pull-down resistors to GND
- **Serial Communication**: 115200 baud rate via USB

**Button Commands:**
| Pin | Button | Command |
|-----|---------|---------|
| 4   | BTN1   | right   |
| 5   | BTN2   | down    |
| 6   | BTN3   | up      |
| 7   | BTN4   | left    |
| 15  | BTN5   | start   |
| 16  | BTN6   | func1   |
| 17  | BTN7   | stop    |
| 18  | BTN8   | func2   |

---

## Software Setup

### 1. Hardware Device Rules Setup

Creates stable device access using udev rules so your input device always appears as `/dev/input-device` regardless of USB port changes.

```bash
# Make the script executable
chmod +x setup_hardware.sh

# Run the hardware setup (requires sudo)
sudo ./setup_hardware.sh /dev/ttyUSB0 input-device

# Or for dry-run to see what it would do:
sudo ./setup_hardware.sh /dev/ttyUSB0 input-device --dry-run
```

**What this does:**
- ✅ Identifies your device's unique USB vendor/product ID or serial number
- ✅ Creates udev rule in `/etc/udev/rules.d/99-input-device.rules`
- ✅ Creates stable symlink `/dev/input-device` pointing to actual device
- ✅ Sets proper permissions for device access
- ✅ Reloads udev rules automatically

**Verification:**
```bash
# Check if symlink was created
ls -l /dev/input-device

# See where it points
readlink -f /dev/input-device

# Test if device is accessible
cat /dev/input-device  # Press Ctrl+C to stop
```

---

### 2. Application Auto-start Setup

Sets up the Host Controller to start automatically when you log into the desktop environment.

```bash
# Make the script executable
chmod +x setup_desktop_autostart.sh

# Run the auto-start setup (no sudo needed)
./setup_desktop_autostart.sh
```

**What this does:**
- ✅ Creates desktop autostart entry (`~/.config/autostart/host-controller.desktop`)
- ✅ Creates startup script with virtual environment support
- ✅ Sets up process monitoring and auto-restart (watchdog)
- ✅ Prevents multiple instances from running
- ✅ Configures comprehensive logging
- ✅ Optimized for industrial reliability

**Features:**
- 🏭 **Industrial Grade**: Automatic restart if application crashes
- 🔄 **Reliable Startup**: Starts every time you log into desktop
- 📊 **Full Logging**: All events logged for troubleshooting
- ⚙️ **Easy Management**: Simple commands for control
- 🔧 **Hardware Ready**: Auto-selects `/dev/input-device`

---

## Usage

### Starting the System

1. **Boot your computer**
2. **Log into desktop environment**
3. **Host Controller GUI appears automatically** (after ~5 seconds)
4. **Device `/dev/input-device` is pre-selected**
5. **Press buttons on input device** - commands appear in GUI immediately

### Manual Control

```bash
# Test the startup script manually
./start_host_controller_desktop.sh

# Stop the application
pkill -f host_controller.py

# View application logs
tail -f ~/host_controller.log

# View startup logs
tail -f ~/host_controller_startup.log

# Remove auto-start (if needed)
rm ~/.config/autostart/host-controller.desktop
```

---

## Troubleshooting

### Device Not Found
```bash
# Check if device is connected
ls /dev/ttyUSB* /dev/ttyACM*

# Check udev rule
cat /etc/udev/rules.d/99-input-device.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=add

# Or unplug/replug device
```

### Application Won't Start
```bash
# Check startup logs
tail -20 ~/host_controller_startup.log

# Check if virtual environment exists
ls -la venv/

# Test Python dependencies
source venv/bin/activate
python -c "import PyQt5, serial, cv2; print('All dependencies OK')"
```

### Baud Rate Issues (Garbled Text)
- Ensure Arduino code uses `Serial.begin(115200)`
- Host Controller is configured for 115200 baud
- Both must match exactly

---

## Industrial Environment Benefits

✅ **Automatic Recovery**: Watchdog restarts application if it crashes  
✅ **Consistent Hardware Access**: Device always available as `/dev/input-device`  
✅ **Boot-to-Ready**: System ready for use immediately after login  
✅ **No Manual Intervention**: Fully automated startup process  
✅ **Full Monitoring**: Complete logging of all system events  
✅ **Production Ready**: Designed for 24/7 industrial operation  

---

## File Structure

```
DataCollector/
├── setup_hardware.sh              # udev rules setup
├── setup_desktop_autostart.sh     # auto-start configuration  
├── host_controller.py             # main GUI application
├── start_host_controller_desktop.sh  # startup script (auto-generated)
├── venv/                          # Python virtual environment
└── requirements.txt               # Python dependencies
```

## System Files Created

- `/etc/udev/rules.d/99-input-device.rules` - Device access rule
- `~/.config/autostart/host-controller.desktop` - Desktop autostart entry
- `~/host_controller.log` - Application logs
- `~/host_controller_startup.log` - Startup logs
- `~/host_controller.pid` - Process ID file
- `~/host_controller_watchdog.sh` - Monitoring script

This setup provides enterprise-grade reliability for industrial applications requiring consistent hardware access and automatic startup capabilities.