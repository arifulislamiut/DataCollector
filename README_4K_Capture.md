# 📸 4K Camera Capture with Date-wise Storage

Capture stunning 4K (3840x2160) images from your MX Brio camera with optimized storage and performance.

## 🚀 Quick Start

### Simple 4K Capture (Default: 1 image every 3 seconds)
```bash
python quick_4k_capture.py
```

### Custom 4K Intervals
```bash
python quick_4k_capture.py 2      # Every 2 seconds for 60 seconds
python quick_4k_capture.py 5 120  # Every 5 seconds for 2 minutes
```

### Full-Featured 4K Capture
```bash
python camera_capture_4k.py
```

## ⚠️ 4K Storage Requirements

4K images are **significantly larger** than 1080p:
- **4K Image**: ~0.6-0.7 MB (actual tested size)
- **1080p Image**: ~0.25 MB 
- **Size Ratio**: 4K is ~3x larger per image

## 📁 4K Storage Structure

```
captured_images_4k/
├── 2025-08-08/
│   ├── 4K_14-30-25-123.jpg
│   ├── 4K_14-30-30-456.jpg
│   └── ...
├── 2025-08-09/
│   ├── 4K_09-15-10-789.jpg
│   └── ...
```

## 🎛️ 4K Capture Modes

### 1. Interval Mode (Recommended for 4K)
- **Suggested intervals**: 2-5 seconds (vs 1 second for 1080p)
- Balances quality with storage usage
- **Usage**: Time-lapse, monitoring with high detail

### 2. Manual Mode
- Save 4K images on demand (spacebar/s key)
- **Usage**: Capture specific high-quality moments

### 3. Motion Detection Mode
- **Optimized for 4K**: Higher motion thresholds
- **Smart processing**: Uses downscaled frames for motion detection
- **Usage**: Security with ultra-high quality evidence

## 🔧 4K Technical Specifications

### Camera Settings
- **Resolution**: 3840x2160 (4K UHD)
- **Format**: MJPG (required for higher FPS)
- **FPS**: Up to 30fps (25fps actual due to driver limitations)
- **Quality**: 90% JPEG (optimized for 4K file sizes)

### Performance Optimizations
- **Buffer Size**: Minimal (1 frame) for low latency
- **Preview**: Disabled by default for performance
- **Motion Detection**: Downscaled to 960x540 for processing
- **Storage**: Efficient JPEG compression

## 💾 4K Storage Estimates

| Interval | Images/Hour | Storage/Hour | Storage/Day |
|----------|-------------|--------------|-------------|
| 2 seconds | 1,800 | ~1.2 GB | ~29 GB |
| 3 seconds | 1,200 | ~800 MB | ~19 GB |
| 5 seconds | 720 | ~480 MB | ~12 GB |
| 10 seconds | 360 | ~240 MB | ~6 GB |
| Motion (normal) | Variable | ~200-600 MB | ~5-15 GB |

## 🎯 4K Use Cases

### 📹 High-Quality Time-lapse
```bash
# 4K time-lapse: Every 10 seconds for 4 hours
python quick_4k_capture.py 10 14400
```

### 🔍 Ultra-High Resolution Security
```bash
# 4K motion detection with optimized settings
python camera_capture_4k.py
# Choose: Motion detection
# Threshold: 15000 (4K optimized)
```

### 🎨 Photography/Art Documentation
```bash
# Manual 4K capture with preview
python camera_capture_4k.py
# Choose: Manual mode
# Preview: Yes (for composition)
```

### 📊 Detailed Process Monitoring
```bash
# 4K capture every 30 seconds
python quick_4k_capture.py 30 3600
```

## ⚡ Performance Comparison

### 1080p vs 4K Comparison
| Aspect | 1080p | 4K |
|--------|-------|-----|
| Resolution | 1920x1080 | 3840x2160 |
| Pixels | 2.1 MP | 8.3 MP (4x more) |
| File Size | ~0.25 MB | ~0.65 MB (3x larger) |
| FPS | 25 fps | 25 fps (same) |
| Processing | Fast | Moderate |
| Storage/Day (5s interval) | ~4 GB | ~12 GB |

### When to Use Each:
- **1080p**: General monitoring, frequent captures, limited storage
- **4K**: Detailed analysis, evidence collection, high-quality documentation

## 🛠️ 4K Configuration Options

### Quick 4K Capture Options:
```bash
# High frequency 4K (every 1 second for 5 minutes)
python quick_4k_capture.py 1 300

# Long-term 4K monitoring (every 60 seconds for 24 hours)  
python quick_4k_capture.py 60 86400

# Balanced 4K (every 3 seconds for 2 hours)
python quick_4k_capture.py 3 7200
```

### Full 4K Script Options:
- **Storage folder**: Custom 4K storage location
- **Save modes**: Interval (2-5s recommended), Manual, Motion
- **Motion sensitivity**: 10000-25000 (higher than 1080p)
- **Preview**: Optional (impacts performance)

## 🔧 4K Troubleshooting

### 4K Not Available
```bash
# Check 4K support
v4l2-ctl -d /dev/video0 --list-formats-ext | grep 3840x2160
```
Should show:
```
Size: Discrete 3840x2160
    Interval: Discrete 0.033s (30.000 fps)
```

### Performance Issues
- **Disable preview** for maximum performance
- **Increase intervals** (3-5 seconds recommended)
- **Use motion detection** to reduce unnecessary captures
- **Monitor disk space** - 4K uses 3x more storage

### Storage Management
```bash
# Check 4K storage usage
du -h captured_images_4k/

# Clean old 4K images (older than 3 days)
find captured_images_4k -name "*.jpg" -mtime +3 -delete

# Convert 4K to video
ffmpeg -framerate 10 -pattern_type glob -i 'captured_images_4k/2025-08-08/*.jpg' -s 3840x2160 4k_timelapse.mp4
```

## 🎬 4K Post-Processing

### Create 4K Time-lapse Video
```bash
# 4K time-lapse at 24fps
ffmpeg -framerate 24 -pattern_type glob -i 'captured_images_4k/2025-08-08/*.jpg' \
       -c:v libx264 -pix_fmt yuv420p -s 3840x2160 output_4k.mp4

# 4K time-lapse with high quality
ffmpeg -framerate 30 -pattern_type glob -i 'captured_images_4k/2025-08-08/*.jpg' \
       -c:v libx264 -crf 18 -pix_fmt yuv420p -s 3840x2160 output_4k_hq.mp4
```

### Downscale for Sharing
```bash
# Convert 4K images to 1080p for sharing
for file in captured_images_4k/2025-08-08/*.jpg; do
    ffmpeg -i "$file" -s 1920x1080 "1080p_$(basename "$file")"
done
```

## 📊 Tested Performance

### Your MX Brio 4K Results:
- ✅ **4K Resolution**: 3840x2160 confirmed
- ✅ **Frame Rate**: 25fps (stable)
- ✅ **File Size**: 0.6-0.7 MB per image (efficient compression)
- ✅ **Format**: MJPG (optimal for 4K)
- ✅ **Quality**: Excellent detail and clarity

### Storage Efficiency:
- **Better than expected**: ~0.65 MB actual vs ~4 MB estimated
- **Compression**: Excellent JPEG efficiency at 90% quality
- **Practical**: Viable for extended monitoring periods

## 🎯 4K Recommendations

1. **Start with 5-second intervals** to test storage impact
2. **Disable preview** for maximum performance
3. **Monitor disk space** regularly
4. **Use motion detection** for efficient storage
5. **Plan for 3x storage** compared to 1080p
6. **Consider hybrid approach**: 4K for key moments, 1080p for continuous monitoring

Your MX Brio delivers excellent 4K quality at practical file sizes!