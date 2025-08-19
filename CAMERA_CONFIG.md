# Camera Configuration Guide - Logitech MX Brio on Jetson Nano

Complete reference for configuring the Logitech MX Brio camera for optimal fabric capture with motion blur elimination.

## Quick Setup for Motion Blur Elimination

```bash
# Set manual exposure mode and ultra-fast shutter
v4l2-ctl -d /dev/video0 --set-ctrl=auto_exposure=1
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=10

# Verify settings applied
v4l2-ctl -d /dev/video0 --get-ctrl=auto_exposure,exposure_time_absolute
```

## Camera Control Discovery

### List All Available Controls
```bash
# Show all camera controls and current values
v4l2-ctl -d /dev/video0 --list-ctrls

# Show only exposure-related controls
v4l2-ctl -d /dev/video0 --list-ctrls | grep exposure

# Show all current settings
v4l2-ctl -d /dev/video0 --all
```

### Camera Device Detection
```bash
# List all video devices
v4l2-ctl --list-devices

# Check camera capabilities
v4l2-ctl -d /dev/video0 --list-formats-ext

# Verify 1080p support
v4l2-ctl -d /dev/video0 --list-formats-ext | grep 1920x1080
```

## Exposure Control (Motion Blur)

### MX Brio Exposure Settings
```bash
# Check current exposure mode
v4l2-ctl -d /dev/video0 --get-ctrl=auto_exposure

# Exposure modes:
# 0 = Auto Mode
# 1 = Manual Mode  
# 2 = Shutter Priority Mode
# 3 = Aperture Priority Mode (default)

# Set manual exposure for motion control
v4l2-ctl -d /dev/video0 --set-ctrl=auto_exposure=1
```

### Shutter Speed Control
```bash
# Exposure time range: 3-2047 (lower = faster shutter)

# Ultra-fast shutter (moving fabric)
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=5

# Very fast shutter
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=10

# Fast shutter  
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=20

# Medium shutter
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=50

# Check current exposure time
v4l2-ctl -d /dev/video0 --get-ctrl=exposure_time_absolute
```

## Image Quality Controls

### Gain Control (Compensate for Fast Shutter)
```bash
# Check gain range
v4l2-ctl -d /dev/video0 --list-ctrls | grep gain

# Set high gain for fast shutter compensation
v4l2-ctl -d /dev/video0 --set-ctrl=gain=255

# Check current gain
v4l2-ctl -d /dev/video0 --get-ctrl=gain
```

### Brightness and Contrast
```bash
# Set brightness (range typically 0-255)
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=180

# Set contrast (range typically 0-255)  
v4l2-ctl -d /dev/video0 --set-ctrl=contrast=200

# Check current values
v4l2-ctl -d /dev/video0 --get-ctrl=brightness,contrast
```

### Sharpness and Saturation
```bash
# Maximum sharpness for fabric texture
v4l2-ctl -d /dev/video0 --set-ctrl=sharpness=255

# Reduced saturation for industrial capture
v4l2-ctl -d /dev/video0 --set-ctrl=saturation=100

# Check current values
v4l2-ctl -d /dev/video0 --get-ctrl=sharpness,saturation
```

## Focus and White Balance

### Manual Focus Control
```bash
# Disable autofocus
v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=0

# Set manual focus (adjust for fabric distance)
v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=30

# Check focus range
v4l2-ctl -d /dev/video0 --list-ctrls | grep focus
```

### White Balance Control
```bash
# Disable auto white balance
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature_auto=0

# Set manual white balance (3000-6500K typical)
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature=4000

# Check white balance controls
v4l2-ctl -d /dev/video0 --list-ctrls | grep white_balance
```

## Complete Fast Fabric Capture Setup

### Optimal Settings for Moving Fabric
```bash
#!/bin/bash
# Complete setup script for motion blur elimination

# Set manual exposure mode
v4l2-ctl -d /dev/video0 --set-ctrl=auto_exposure=1

# Ultra-fast shutter speed
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=10

# High gain to compensate for fast shutter
v4l2-ctl -d /dev/video0 --set-ctrl=gain=255

# Enhanced image quality
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=180
v4l2-ctl -d /dev/video0 --set-ctrl=contrast=200
v4l2-ctl -d /dev/video0 --set-ctrl=sharpness=255
v4l2-ctl -d /dev/video0 --set-ctrl=saturation=100

# Manual focus and white balance
v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=0
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature_auto=0

echo "Camera configured for fast fabric capture"
```

### Verify All Settings
```bash
# Check all critical settings
v4l2-ctl -d /dev/video0 --get-ctrl=auto_exposure,exposure_time_absolute,gain,brightness,contrast,sharpness,saturation,focus_auto,white_balance_temperature_auto
```

## Troubleshooting

### Common Issues

**1. Exposure time inactive**
```bash
# Problem: exposure_time_absolute shows "flags=inactive"
# Solution: Set manual exposure mode first
v4l2-ctl -d /dev/video0 --set-ctrl=auto_exposure=1
```

**2. Settings not persisting**
```bash
# Settings reset when application starts
# Solution: Apply v4l2 settings BEFORE starting capture script
```

**3. Too dark with fast shutter**
```bash
# Increase gain and brightness
v4l2-ctl -d /dev/video0 --set-ctrl=gain=255
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=200

# Or slightly slower shutter
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=20
```

**4. Still motion blur**
```bash
# Try even faster shutter
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=5

# Check if fabric speed can be reduced
# Add more lighting to allow faster shutter
```

### Testing Motion Blur Settings

```bash
# Test sequence for different fabric speeds
for exposure in 5 10 15 20 25 30; do
    echo "Testing exposure: $exposure"
    v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=$exposure
    sleep 2
    # Run capture for a few seconds and check results
done
```

### Save/Restore Settings

```bash
# Save current settings to file
v4l2-ctl -d /dev/video0 --all > camera_settings_backup.txt

# Create settings restoration script
echo "#!/bin/bash" > restore_camera.sh
v4l2-ctl -d /dev/video0 --list-ctrls | grep -E "(exposure|gain|brightness|contrast)" | \
awk '{print "v4l2-ctl -d /dev/video0 --set-ctrl=" $1 "=" $NF}' >> restore_camera.sh
chmod +x restore_camera.sh
```

## Integration with Python Script

The Python script will show current settings after v4l2 configuration:

```bash
# 1. Configure camera with v4l2-ctl
v4l2-ctl -d /dev/video0 --set-ctrl=auto_exposure=1
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_time_absolute=10

# 2. Run Python capture script
python3 capture_fhd.py

# The script will display actual applied settings in logs
```

## Advanced Settings

### Power Line Frequency (Avoid Flicker)
```bash
# Set for 60Hz (US) or 50Hz (EU) to avoid flicker
v4l2-ctl -d /dev/video0 --set-ctrl=power_line_frequency=1  # 50Hz
v4l2-ctl -d /dev/video0 --set-ctrl=power_line_frequency=2  # 60Hz
```

### Backlight Compensation
```bash
# Disable backlight compensation for consistent exposure
v4l2-ctl -d /dev/video0 --set-ctrl=backlight_compensation=0
```

### Zoom and Pan (if supported)
```bash
# Check zoom controls
v4l2-ctl -d /dev/video0 --list-ctrls | grep zoom

# Set zoom level
v4l2-ctl -d /dev/video0 --set-ctrl=zoom_absolute=100
```

## Performance Optimization

### USB Bandwidth (Jetson Nano)
```bash
# Check USB device info
lsusb -v | grep -A 5 -B 5 "MX Brio"

# Monitor USB bandwidth usage
sudo iotop -o -d 1
```

### Memory and CPU Monitoring
```bash
# Monitor system resources during capture
htop

# Check video4linux buffer usage
cat /sys/class/video4linux/video0/dev
```

This configuration guide provides complete control over the MX Brio camera for optimal fabric capture with minimal motion blur.