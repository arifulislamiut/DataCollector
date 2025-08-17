# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataCollector is a comprehensive camera capture and data collection system that combines image capture capabilities with industrial control interfaces. It supports both 1080p and 4K image capture with date-wise organization, features an industrial-grade PyQt5 GUI for device monitoring, and includes automated cloud synchronization with Google Drive.

## Core Architecture

### Main Components

- **CameraCaptureStorage Class** (`camera_capture_storage.py`): Core capture engine with resolution-aware settings, storage management, and multiple capture modes
- **Host Controller GUI** (`host_controller.py`): PyQt5-based industrial interface for device monitoring and script execution with auto-discovery of COM/TTY devices
- **Hardware Integration**: ESP32/NodeMCU support with 8-button industrial input (GPIO pins 4,5,6,7,15,16,17,18) via serial communication at 115200 baud
- **Date-wise Storage System**: Automatic organization of captured images by date (`YYYY-MM-DD/`) with session-based MP4 video generation
- **Resolution Support**: Dual-mode system supporting both 1080p (1920x1080) and 4K (3840x2160) capture
- **Motion Detection Engine**: Optimized motion detection with downscaling for 4K performance
- **Cloud Synchronization**: Automated Google Drive sync using rclone with crontab scheduling and monitoring

### Key Design Patterns

- **Factory Pattern**: Resolution-specific configuration and optimization
- **Strategy Pattern**: Multiple capture modes (interval, motion, manual, all frames)
- **Observer Pattern**: Real-time statistics logging and progress tracking, device monitoring threads
- **Resource Management**: Automatic cleanup, signal handling, and graceful shutdown
- **Industrial Reliability**: Watchdog processes, automatic restart, udev rules for stable device access
- **Multi-threaded Architecture**: Separate threads for device monitoring, serial communication, and GUI responsiveness

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies for industrial setup
sudo apt install v4l-utils rclone

# Verify camera access (Linux/V4L2)
v4l2-ctl --list-devices
```

### Running Applications

#### Camera Capture System
```bash
# Interactive mode with resolution selection
python camera_capture_storage.py

# Direct execution with default 1080p
python3 camera_capture_storage.py

# Legacy capture scripts
python capture.py          # Basic capture
python capture_fhd.py     # Full HD capture
```

#### Host Controller (Industrial GUI)
```bash
# Manual execution
python host_controller.py

# Set up automatic startup on desktop login
./setup_desktop_autostart.sh

# Manual startup script
./start_host_controller_desktop.sh
```

#### Cloud Synchronization
```bash
# Set up automated Google Drive sync
./setup_crontab.sh

# Manual sync to Google Drive
./sync_cron.sh

# Check sync status
./check_cron_sync.sh

# View sync logs
tail -f sync_cron.log
```

### Testing & Debugging
```bash
# Test camera initialization
python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).isOpened() else 'Camera FAILED')"

# Check 4K support
v4l2-ctl -d /dev/video0 --list-formats-ext | grep 3840x2160

# Test Host Controller with mock device
python test_host_controller_mock_device.py

# Monitor system performance during capture
htop  # Monitor CPU/memory usage

# Check device availability for Host Controller
ls /dev/ttyUSB* /dev/ttyACM* /dev/pts/*

# Test serial communication (GPIO button inputs)
cat /dev/input-device  # Press Ctrl+C to stop

# Verify rclone Google Drive configuration
rclone about gdrive:
```

### Hardware Setup Commands
```bash
# Set up stable device access via udev rules
sudo ./setup_hardware.sh /dev/ttyUSB0 input-device

# Set up automatic startup for Host Controller
./setup_desktop_autostart.sh

# Set up systemd service (alternative to desktop autostart)  
sudo ./setup_systemd_service.sh
```

## Industrial Control Architecture

### Host Controller System
- **GUI Framework**: PyQt5 with threaded device monitoring and real-time updates
- **Device Auto-Discovery**: Automatic scanning of `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/pts/*` devices
- **Serial Communication**: 115200 baud rate with configurable settings
- **Command Processing**: Real-time processing of 8-button GPIO inputs from ESP32/NodeMCU
- **Script Integration**: Dynamic Python script loading and execution from GUI
- **Industrial Features**: Process monitoring, auto-restart, logging, PID file management

### Button Command Mapping
```
GPIO Pin → Button → Command
4        → BTN1   → right  
5        → BTN2   → down
6        → BTN3   → up
7        → BTN4   → left
15       → BTN5   → start
16       → BTN6   → func1
17       → BTN7   → stop
18       → BTN8   → func2
```

### Hardware Reliability Features
- **udev Rules**: Stable device addressing via `/dev/input-device` symlink
- **Watchdog Process**: Automatic application restart on crashes
- **Desktop Integration**: Auto-start on login via `~/.config/autostart/`
- **Logging System**: Comprehensive logging to `~/host_controller.log` and `~/host_controller_startup.log`

## Cloud Synchronization Architecture

### Rclone Integration
- **Google Drive Sync**: Automated upload of capture sessions using rclone
- **Crontab Scheduling**: Configurable sync intervals (5, 10, 15, 30 minutes, hourly)
- **Incremental Sync**: Only uploads new/changed files with checksum verification
- **Lock File Management**: Prevents multiple sync processes running simultaneously
- **Monitoring**: Real-time sync status and Google Drive storage statistics

### Sync Infrastructure
- **Lock Files**: `/tmp/datacollector_cron_sync.lock` for process coordination
- **Logging**: Timestamped sync logs in `sync_cron.log`
- **Error Recovery**: Automatic retry with exponential backoff
- **Storage Management**: Automated cleanup and rotation of old files

## Resolution-Specific Architecture

### 1080p Mode
- **Target Settings**: 1920x1080, 95% JPEG quality, ~0.25MB per image
- **Optimizations**: Full-resolution motion detection, 1-2s intervals
- **Storage Path**: `captured_images/`

### 4K Mode  
- **Target Settings**: 3840x2160, 90% JPEG quality, ~0.65MB per image
- **Optimizations**: Downscaled motion detection (960x540), preview downscaling, 3-5s intervals
- **Storage Path**: `captured_images_4k/`
- **Performance Features**: Motion detection uses 1/4 scale frames, preview automatically downscaled

## Capture Mode Architecture

### Interval Mode
- Time-based capture with configurable intervals
- Resolution-aware defaults (1s for 1080p, 3s for 4K)

### Motion Detection Mode
- Adaptive thresholds based on resolution (5000 for 1080p, 15000 for 4K)
- Cooldown periods to prevent spam detection
- Performance optimization through frame downscaling for 4K

### Manual Mode
- User-controlled capture via spacebar/s key
- Real-time preview with keyboard controls

### All Frames Mode
- Continuous capture at full frame rate (25fps)
- High storage usage warning system

## Technical Specifications

### Camera Configuration
- **Backend**: OpenCV V4L2 for Linux camera access
- **Format**: MJPG codec for optimal compression and frame rate
- **Buffer**: Minimal (1 frame) for low latency
- **Frame Rate**: Target 60fps (actual 25fps due to driver limitations)

### Performance Characteristics
- **1080p**: ~25fps, 0.25MB per image, full-resolution processing
- **4K**: ~25fps, 0.65MB per image, optimized processing with downscaling
- **Motion Detection**: Real-time with threshold-based sensitivity

### Storage Management
- **Organization**: Date-based folders (`YYYY-MM-DD/`)
- **Naming**: Timestamp-based with millisecond precision
- **Formats**: High-quality JPEG with resolution-optimized compression

## Common Development Tasks

### Adding New Capture Modes
1. Extend the capture loop in `capture_and_store()` method
2. Add mode configuration in `main()` function
3. Update resolution-specific optimizations if needed

### Modifying Resolution Settings  
1. Update resolution configurations in `__init__()` method
2. Adjust quality, thresholds, and intervals for new resolution
3. Test camera capability validation

### Performance Optimization
1. Monitor frame rates via built-in logging system
2. Adjust buffer sizes and codec settings in `initialize_camera()`
3. Optimize preview and motion detection downscaling ratios

## File Structure

```
DataCollector/
├── Core Applications
│   ├── camera_capture_storage.py        # Main capture system
│   ├── host_controller.py              # Industrial GUI controller
│   ├── capture.py                      # Basic capture script
│   └── capture_fhd.py                  # Full HD capture script
├── Hardware & Setup Scripts
│   ├── setup_hardware.sh               # udev rules for stable device access
│   ├── setup_desktop_autostart.sh      # Auto-start configuration
│   ├── setup_systemd_service.sh        # Systemd service setup
│   ├── setup_crontab.sh               # Automated sync configuration
│   └── start_host_controller_desktop.sh # GUI startup script
├── Cloud Synchronization
│   ├── sync_cron.sh                    # Main sync script for crontab
│   ├── check_cron_sync.sh              # Sync status monitoring
│   └── rotate_logs.sh                  # Log rotation management
├── Testing & Development
│   └── test_host_controller_mock_device.py # Mock device testing
├── Documentation
│   ├── CLAUDE.md                       # This file - development guide
│   ├── README_4K_Capture.md           # 4K-specific documentation
│   ├── RCLONE_SETUP.md                # Google Drive sync setup
│   └── readme_hardware.md             # Hardware setup guide
├── Configuration
│   └── requirements.txt                # Python dependencies
└── Data Storage
    └── collection/                     # Captured images and videos
        └── YYYY-MM-DD-HH-MM/          # Session-based folders
            ├── 1080p_HH-MM-SS-mmm.jpg # Timestamped images
            └── session_YYYY-MM-DD_HH-MM-SS.mp4 # Session videos
```

## Hardware Requirements

### Camera System
- **Camera**: MX Brio or compatible V4L2 device
- **OS**: Linux with V4L2 support (tested on Ubuntu/Debian)
- **Storage**: Variable based on capture mode and resolution (4K requires ~3x more storage than 1080p)
- **Memory**: Minimal buffering design for low memory usage

### Industrial Control System  
- **Microcontroller**: ESP32 or NodeMCU with 8 GPIO push buttons
- **GPIO Pins**: 4,5,6,7,15,16,17,18 with external pull-down resistors
- **Serial Interface**: USB connection supporting 115200 baud rate
- **Host System**: Linux with PyQt5 support and serial device access

### Cloud Synchronization
- **Network**: Internet connection for Google Drive sync
- **Storage**: Google Drive account with sufficient space for image/video storage
- **Tools**: rclone configured with Google Drive OAuth credentials

### System Dependencies
```bash
# Required Python packages
opencv-python>=4.5.0
numpy>=1.19.0  
PyQt5>=5.15.0
pyserial>=3.5

# Required system packages
v4l-utils      # Video4Linux utilities
rclone         # Cloud synchronization
```