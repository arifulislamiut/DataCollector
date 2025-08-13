# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataCollector is a Python-based camera capture system that supports both 1080p and 4K image capture with date-wise organization. The system is designed for MX Brio cameras and provides multiple capture modes including interval-based, motion detection, manual, and continuous capture.

## Core Architecture

### Main Components

- **CameraCaptureStorage Class** (`camera_capture_storage.py`): Core capture engine with resolution-aware settings, storage management, and multiple capture modes
- **Date-wise Storage System**: Automatic organization of captured images by date (`YYYY-MM-DD/`)
- **Resolution Support**: Dual-mode system supporting both 1080p (1920x1080) and 4K (3840x2160) capture
- **Motion Detection Engine**: Optimized motion detection with downscaling for 4K performance

### Key Design Patterns

- **Factory Pattern**: Resolution-specific configuration and optimization
- **Strategy Pattern**: Multiple capture modes (interval, motion, manual, all frames)
- **Observer Pattern**: Real-time statistics logging and progress tracking
- **Resource Management**: Automatic cleanup, signal handling, and graceful shutdown

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify camera access (Linux/V4L2)
v4l2-ctl --list-devices
```

### Running the Application
```bash
# Interactive mode with resolution selection
python camera_capture_storage.py

# Direct execution with default 1080p
python3 camera_capture_storage.py
```

### Testing & Debugging
```bash
# Test camera initialization
python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).isOpened() else 'Camera FAILED')"

# Check 4K support
v4l2-ctl -d /dev/video0 --list-formats-ext | grep 3840x2160

# Monitor system performance during capture
htop  # Monitor CPU/memory usage
```

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
├── camera_capture_storage.py    # Main capture system
├── requirements.txt            # Python dependencies  
├── README_ImageCapture.md     # 1080p documentation
├── README_4K_Capture.md      # 4K-specific documentation
├── .gitignore                # Standard Python + media files
└── CLAUDE.md                 # This file
```

## Hardware Requirements

- **Camera**: MX Brio or compatible V4L2 device
- **OS**: Linux with V4L2 support
- **Storage**: Variable based on capture mode and resolution
- **Memory**: Minimal buffering design for low memory usage