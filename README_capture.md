# Motion Capture with Video Recording

A Python camera capture system that automatically detects motion, captures high-resolution images, and records continuous video sessions.

## Features

### Core Functionality
- **Automatic Resolution Detection**: Tries 4K (3840x2160) first, falls back to 1080p (1920x1080) if unavailable
- **Motion Detection**: 50,000 pixel change threshold with 1-second cooldown
- **Dual Output**: Motion-triggered images + continuous session video recording
- **Intelligent Preview**: Auto-detects screen resolution and displays scaled live preview

### Smart Capabilities
- **Screen Detection**: Automatically detects display environment and adjusts preview accordingly
- **Headless Support**: Runs without preview on servers/headless systems
- **Graceful Fallback**: Handles camera limitations and system constraints automatically
- **Session Management**: Organized storage with timestamped folders

## Quick Start

```bash
# Install dependencies
pip install opencv-python

# Run capture (no configuration needed)
python capture.py
```

The script starts immediately with optimal settings - no user input required.

## System Requirements

### Hardware
- **Camera**: USB camera compatible with V4L2 (tested with MX Brio)
- **Storage**: Variable based on session length and resolution
- **Memory**: Minimal buffering design for low memory usage

### Software
- **OS**: Linux with V4L2 support
- **Python**: 3.6+
- **Dependencies**: OpenCV (`cv2`), standard library modules

### Optional (for preview)
- **Display**: X11 or Wayland desktop environment
- **Tools**: `xrandr` or `xdpyinfo` for screen detection

## Configuration

All settings are optimized and hardcoded - no configuration files needed:

```python
# Motion Detection
MOTION_THRESHOLD = 50000     # Pixel changes required
MOTION_COOLDOWN = 1.0       # Seconds between captures

# Video Quality
4K_JPEG_QUALITY = 90        # 90% for ~0.65MB per image  
1080P_JPEG_QUALITY = 95     # 95% for ~0.25MB per image

# Storage
BASE_PATH = "collection/"   # Output directory
FOLDER_FORMAT = "YYYY-MM-DD-HH-MM"  # Session folders
```

## Output Structure

```
collection/
├── 2024-01-15-14-30/          # Session folder (YYYY-MM-DD-HH-MM)
│   ├── 4K_14-31-25-123.jpg    # Motion-triggered images
│   ├── 4K_14-31-28-456.jpg
│   ├── 4K_14-31-31-789.jpg
│   └── session_2024-01-15_14-30-25.mp4  # Complete session video
└── 2024-01-15-16-45/
    ├── 1080p_16-46-12-234.jpg # 1080p fallback mode
    ├── 1080p_16-46-15-567.jpg
    └── session_2024-01-15_16-45-30.mp4
```

## Usage Examples

### Basic Usage
```bash
# Start capture with auto-detection
python capture.py

# Output:
# 🎥 4K Motion Capture with Video Recording
# ✅ 4K Camera initialized successfully:
# 📺 Screen detected: 1920x1080
# Starting 4K motion capture with video recording...
```

### Headless Server Usage
```bash
# On server without display
DISPLAY= python capture.py

# Output:
# 🎥 4K Motion Capture with Video Recording  
# ✅ 4K Camera initialized successfully:
# No display environment detected - preview disabled
# Starting 4K motion capture with video recording...
```

## Camera Resolution Modes

### 4K Mode (Preferred)
- **Resolution**: 3840x2160 pixels
- **File Size**: ~0.65MB per image
- **JPEG Quality**: 90%
- **Video**: H.264 MP4 at 25fps
- **Motion Detection**: Downscaled to 960x540 for performance

### 1080p Mode (Fallback)
- **Resolution**: 1920x1080 pixels  
- **File Size**: ~0.25MB per image
- **JPEG Quality**: 95%
- **Video**: H.264 MP4 at 25fps
- **Motion Detection**: Downscaled to 480x270 for performance

## Preview Window Controls

When a screen is detected, a preview window appears:

- **Window**: "Motion Capture Preview"
- **Title Bar**: Shows resolution and capture count
- **Scaling**: Automatically fits 80% of screen resolution
- **Controls**: Press `q` to quit, `Ctrl+C` to stop

## Performance Characteristics

### Resource Usage
- **CPU**: Optimized motion detection with downscaling
- **Memory**: Minimal buffering (1 frame buffer)
- **Storage Rate**:
  - 4K: ~0.65MB per motion capture + ~2-5MB/min video
  - 1080p: ~0.25MB per motion capture + ~1-2MB/min video

### Frame Rates
- **Target**: 25fps (camera dependent)
- **Typical**: 20-25fps on modern systems
- **Motion Processing**: Real-time at full frame rate

## Troubleshooting

### Camera Issues
```bash
# Check camera availability
v4l2-ctl --list-devices

# Test camera access
python -c "import cv2; print('OK' if cv2.VideoCapture(0).isOpened() else 'FAIL')"

# Check supported formats
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Check camera permissions
ls -la /dev/video*
```

### No Preview Window
- Check `DISPLAY` environment variable
- Install `xrandr`: `sudo apt install x11-xserver-utils`  
- Install `xdpyinfo`: `sudo apt install x11-utils`

### Storage Issues
- Ensure write permissions in current directory
- Monitor disk space (sessions can generate significant data)
- Consider storage cleanup for long-running captures

## Session Statistics

Each session ends with a comprehensive summary:

```
============================================================
SESSION SUMMARY:
  Duration: 125.3 seconds
  Total frames: 3,132
  Motion captures: 15
  Average FPS: 25.0
  Session folder: /path/to/collection/2024-01-15-14-30
  Video file: session_2024-01-15_14-30-25.mp4 (245.7 MB)
  Image storage: ~9.8 MB
============================================================
```

## Integration Examples

### Cron Job (Automated Capture)
```bash
# Capture every hour for 30 minutes
0 * * * * timeout 1800 /usr/bin/python3 /path/to/capture.py
```

### Systemd Service
```ini
[Unit]
Description=Motion Capture Service
After=graphical-session.target

[Service]
Type=simple
User=camera
WorkingDirectory=/home/camera/capture
ExecStart=/usr/bin/python3 capture.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Advanced Features

### Signal Handling
- **Ctrl+C**: Graceful shutdown with statistics
- **SIGTERM**: Clean resource cleanup
- **Window Close**: Stop capture via preview window

### Logging
- Real-time statistics every 5 seconds
- Motion detection events with timestamps
- Performance metrics (FPS, file sizes)
- Error handling with detailed messages

### Optimization Features
- **Minimal Buffer**: 1-frame buffer for low latency
- **Efficient Scaling**: INTER_AREA interpolation for downscaling
- **Smart Thresholds**: Resolution-aware motion sensitivity
- **Resource Management**: Automatic cleanup on exit

## File Naming Convention

### Images
- **Format**: `{RESOLUTION}_{HH-MM-SS-mmm}.jpg`
- **Examples**: 
  - `4K_14-30-25-123.jpg`
  - `1080p_16-45-32-456.jpg`

### Videos  
- **Format**: `session_{YYYY-MM-DD}_{HH-MM-SS}.mp4`
- **Example**: `session_2024-01-15_14-30-25.mp4`

### Folders
- **Format**: `{YYYY-MM-DD-HH-MM}`
- **Example**: `2024-01-15-14-30`

## Security Considerations

- Script runs with minimal privileges
- No network connections or external dependencies
- Local file system access only
- Camera access requires appropriate permissions
- Safe signal handling prevents data corruption

## Known Limitations

- V4L2 backend required (Linux only)
- Single camera support (camera index 0)
- H.264 codec dependency for video recording
- Preview requires X11/Wayland desktop environment

## Version History

- **v1.0**: Initial release with 4K/1080p support and motion detection
- **v1.1**: Added intelligent preview with screen detection
- **v1.2**: Fixed multiple window issue and improved preview scaling

## Support

For issues or questions:
1. Check troubleshooting section above
2. Verify camera compatibility with V4L2
3. Test with minimal setup: `python -c "import cv2; cv2.VideoCapture(0).read()"`
4. Review session logs for error details