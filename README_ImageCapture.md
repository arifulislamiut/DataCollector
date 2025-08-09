# 📸 Camera Image Capture with Date-wise Storage

Capture and store images from your 4K camera organized by date and time.

## 🚀 Quick Start

### Simple Capture (Default: 1 image/second for 30 seconds)
```bash
python quick_image_capture.py
```

### Custom Intervals
```bash
python quick_image_capture.py 0.5    # Every 0.5 seconds for 30 seconds
python quick_image_capture.py 2 60   # Every 2 seconds for 60 seconds
```

### Full-Featured Capture (1080p + 4K Support!)
```bash
python camera_capture_storage.py
# Choose resolution: 1080p or 4K
# All capture modes supported for both resolutions
```

## 📁 Storage Structure

Images are automatically organized by date:
```
captured_images/
├── 2025-08-08/
│   ├── capture_14-30-25-123.jpg
│   ├── capture_14-30-30-456.jpg
│   └── ...
├── 2025-08-09/
│   ├── img_09-15-10-789.jpg
│   └── ...
```

## 🎛️ Capture Modes

### 1. Interval Mode (Recommended)
- Saves images at regular intervals (e.g., every 1 second)
- Good balance of coverage and storage usage
- **Usage**: Save every 5 seconds for monitoring

### 2. Manual Mode
- Save images by pressing spacebar or 's' key
- Full control over when to capture
- **Usage**: Capture specific events or moments

### 3. Motion Detection Mode  
- Automatically saves when motion is detected
- **Customizable sensitivity**: 1000 (very sensitive) to 20000+ (less sensitive)
- **Cooldown period**: Minimum time between captures to prevent spam
- Reduces storage by only capturing when something changes
- **Usage**: Security monitoring, wildlife observation, activity detection

### 4. All Frames Mode ⚠️
- Saves every single frame (25fps = 25 images/second)
- **Warning**: Uses lots of storage space quickly!
- **Usage**: High-frequency analysis or research

## 📊 Image Quality Options

### 1080p Mode
- **Resolution**: 1920x1080 (Full HD)
- **Format**: JPEG with 95% quality
- **Size**: ~0.25MB per image
- **Use**: General monitoring, frequent captures

### 4K Mode
- **Resolution**: 3840x2160 (Ultra HD)  
- **Format**: JPEG with 90% quality (optimized)
- **Size**: ~0.65MB per image (2.6x larger)
- **Use**: High-detail capture, evidence collection

### Both Modes
- **Color**: Full color (BGR format)
- **Preview**: Clean video feed without overlay text
- **4K Preview**: Auto-downscaled to 1080p for performance

## 💾 Storage Estimates

### 1080p Storage Estimates
| Interval | Images/Hour | Storage/Hour | Storage/Day |
|----------|-------------|--------------|-------------|
| 1 second | 3,600 | ~900 MB | ~21 GB |
| 5 seconds | 720 | ~180 MB | ~4.3 GB |
| 10 seconds | 360 | ~90 MB | ~2.1 GB |
| Motion (normal) | Variable | ~50-200 MB | ~1-5 GB |

### 4K Storage Estimates  
| Interval | Images/Hour | Storage/Hour | Storage/Day |
|----------|-------------|--------------|-------------|
| 3 seconds | 1,200 | ~780 MB | ~19 GB |
| 5 seconds | 720 | ~468 MB | ~11 GB |
| 10 seconds | 360 | ~234 MB | ~6 GB |
| Motion (normal) | Variable | ~200-600 MB | ~5-15 GB |

## 🔧 Configuration Options

### Quick Capture Options:
```bash
# Capture every 0.1 seconds (10fps equivalent)
python quick_image_capture.py 0.1

# Capture every 30 seconds for 1 hour
python quick_image_capture.py 30 3600

# Long-term monitoring: every 60 seconds for 24 hours
python quick_image_capture.py 60 86400
```

### Full Script Options:
When running `camera_capture_storage.py`, you'll be prompted for:
- **Storage folder**: Where to save images
- **Save mode**: Interval/Manual/Motion/All frames
- **Save interval**: Time between saves (for interval mode)
- **Preview**: Show live camera feed

## 🎯 Use Cases

### 📹 Time-lapse Photography
```bash
# Capture every 10 seconds for 2 hours
python quick_image_capture.py 10 7200
```

### 🔍 Security Monitoring
```bash
# Motion detection mode with custom sensitivity
python camera_capture_storage.py
# Choose: Motion detection mode
# Set threshold: 3000 (sensitive) or 10000 (less sensitive)
# Set cooldown: 2.0 seconds between captures
```

### 🎯 Motion Detection Testing
```bash
# Test different sensitivity levels with live preview
python motion_test.py
# Shows motion visualization and detection levels
# Choose from 5 preset sensitivity levels or custom
```

### 📊 Process Monitoring
```bash
# Capture every 30 seconds continuously
python quick_image_capture.py 30 999999
```

### 🧪 Research/Analysis
```bash
# High frequency capture for 5 minutes
python quick_image_capture.py 0.2 300
```

## 🛠️ Troubleshooting

### Low FPS (25fps instead of 60fps)
This is a known limitation with your MX Brio on Linux. The image capture still works perfectly at 25fps.

### Storage Full
- Check available disk space
- Use longer intervals (e.g., 10-30 seconds)
- Clean up old captures periodically

### Camera Not Found
```bash
# Check available cameras
v4l2-ctl --list-devices

# Test camera access
python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).isOpened() else 'Camera FAILED')"
```

### Permission Issues
```bash
# Add user to video group (logout/login required)
sudo usermod -a -G video $USER
```

## 📋 File Naming Convention

### Quick Capture: `img_HH-MM-SS-mmm.jpg`
- `img_14-30-25-123.jpg` = Image at 2:30:25.123 PM

### Full Capture: `capture_HH-MM-SS-mmm.jpg`
- `capture_09-15-45-789.jpg` = Capture at 9:15:45.789 AM

## 🎛️ Advanced Usage

### Batch Processing After Capture
```bash
# Convert to video (requires ffmpeg)
ffmpeg -framerate 10 -pattern_type glob -i 'captured_images/2025-08-08/*.jpg' output.mp4

# Create time-lapse with custom speed
ffmpeg -framerate 30 -pattern_type glob -i 'captured_images/2025-08-08/*.jpg' -r 30 timelapse.mp4
```

### Storage Management
```bash
# Find today's images
find captured_images -name "$(date +%Y-%m-%d)" -type d

# Count images per day
find captured_images -name "*.jpg" | cut -d'/' -f2 | sort | uniq -c

# Clean up old images (older than 7 days)
find captured_images -name "*.jpg" -mtime +7 -delete
```

## 🎯 Resolution Comparison

| Feature | 1080p | 4K |
|---------|-------|-----|
| **Resolution** | 1920x1080 | 3840x2160 |
| **Pixels** | 2.1 MP | 8.3 MP (4x more detail) |
| **File Size** | ~0.25 MB | ~0.65 MB (2.6x larger) |
| **Recommended Interval** | 1-2 seconds | 3-5 seconds |
| **Motion Threshold** | 5000 | 15000 |
| **Best For** | General monitoring, frequent captures | High-detail analysis, evidence |
| **Preview Performance** | Full resolution | Auto-downscaled |

## ✅ **Integrated Solution Ready!**

The `camera_capture_storage.py` script now supports **both 1080p and 4K** with:
- ✅ **Resolution selection** at startup
- ✅ **Optimized settings** for each resolution  
- ✅ **Smart defaults** (intervals, thresholds, quality)
- ✅ **Performance optimizations** (4K motion detection, preview scaling)
- ✅ **All capture modes** (Interval, Manual, Motion) for both resolutions

## 🔧 Camera Performance

Your MX Brio camera provides:
- ✅ **Dual resolution support**: 1080p + 4K
- ✅ **MJPG format** (efficient compression)
- ✅ **Stable 25fps** capture rate (both resolutions)
- ✅ **High quality** images (95% for 1080p, 90% for 4K)
- ✅ **Smart optimizations** for each resolution mode

The 25fps limitation is due to Linux UVC driver constraints, but this still provides excellent image capture quality for most applications at both resolutions.