#!/usr/bin/env python3
"""
1080p Motion Capture with Video Recording
Captures 1080p images on motion detection and records complete session video
"""

import cv2
import time
import threading
import signal
import sys
import os
from datetime import datetime
from collections import deque
import logging
import subprocess
import re

class MotionCapture1080p:
    def __init__(self):
        # Fixed configuration - no user input
        self.camera_index = 0
        self.target_width, self.target_height = 1920, 1080  # 1080p resolution
        self.width, self.height = 1920, 1080
        self.resolution_name = "1080p"
        self.jpeg_quality = 95
        self.motion_threshold = 1000  # 1k pixel changes for high sensitivity
        self.motion_cooldown = 1.0  # 1 second minimum delay for faster response
        self.base_storage_path = "collection"
        
        # Camera and capture state
        self.cap = None
        self.running = False
        self.frame_times = deque(maxlen=60)
        self.frame_count = 0
        self.saved_images = 0
        self.start_time = None
        
        # Video recording
        self.video_writer = None
        self.session_folder = None
        self.video_filename = None
        
        # Motion detection
        self.last_motion_save = 0
        self.prev_frame = None
        
        # Preview settings
        self.show_preview = False
        self.preview_width = 0
        self.preview_height = 0
        self.screen_detected = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Create storage structure
        self.create_session_folder()
        
        # Initialize screen detection and preview
        self.detect_screen()
    
    def signal_handler(self, sig, frame):
        self.logger.info("Stopping capture...")
        self.stop_capture()
        sys.exit(0)
    
    def create_session_folder(self):
        """Create session folder with timestamp"""
        try:
            # Create base collection folder
            if not os.path.exists(self.base_storage_path):
                os.makedirs(self.base_storage_path)
            
            # Create session subfolder: yyyy-mm-dd-hh-mm
            session_timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
            self.session_folder = os.path.join(self.base_storage_path, session_timestamp)
            
            if not os.path.exists(self.session_folder):
                os.makedirs(self.session_folder)
                self.logger.info(f"Created session folder: {self.session_folder}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create session folder: {e}")
            return False
    
    def detect_screen(self):
        """Detect screen resolution and enable preview if screen available"""
        try:
            # Check if DISPLAY environment variable is set (X11/Wayland)
            display_env = os.environ.get('DISPLAY')
            if not display_env:
                self.logger.info("No display environment detected - preview disabled")
                return
            
            # Try to get screen resolution using xrandr (X11)
            try:
                result = subprocess.run(['xrandr', '--current'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse primary display resolution
                    for line in result.stdout.split('\n'):
                        if ' connected primary ' in line or ' connected ' in line:
                            # Look for resolution pattern like "1920x1080"
                            match = re.search(r'(\d+)x(\d+)\+\d+\+\d+', line)
                            if match:
                                self.preview_width = int(match.group(1))
                                self.preview_height = int(match.group(2))
                                self.screen_detected = True
                                self.show_preview = True
                                break
                    
                    if self.screen_detected:
                        self.logger.info(f"📺 Screen detected: {self.preview_width}x{self.preview_height}")
                        self.logger.info("  Preview enabled - press 'q' to quit preview")
                        return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback: Try with xdpyinfo (X11)
            try:
                result = subprocess.run(['xdpyinfo'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Look for dimensions line
                    for line in result.stdout.split('\n'):
                        if 'dimensions:' in line:
                            match = re.search(r'(\d+)x(\d+) pixels', line)
                            if match:
                                self.preview_width = int(match.group(1))
                                self.preview_height = int(match.group(2))
                                self.screen_detected = True
                                self.show_preview = True
                                self.logger.info(f"📺 Screen detected: {self.preview_width}x{self.preview_height}")
                                self.logger.info("  Preview enabled - press 'q' to quit preview")
                                return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback: Use default preview size if we have a display but can't detect resolution
            if display_env:
                self.preview_width = 1920
                self.preview_height = 1080
                self.screen_detected = True
                self.show_preview = True
                self.logger.info("📺 Display detected, using default preview size: 1920x1080")
                self.logger.info("  Preview enabled - press 'q' to quit preview")
            else:
                self.logger.info("No screen detected - preview disabled")
                
        except Exception as e:
            self.logger.warning(f"Screen detection failed: {e}")
            self.logger.info("Preview disabled")
    
    def configure_v4l2_settings(self):
        """Configure camera using v4l2-ctl for precise control"""
        try:
            device = f"/dev/video{self.camera_index}"
            self.logger.info(f"🔧 Configuring MX Brio via v4l2-ctl on {device}")
            
            # Dictionary of v4l2 settings for balanced fabric capture (motion blur vs brightness)
            v4l2_settings = {
                'auto_exposure': 1,              # Manual exposure mode
                'exposure_time_absolute': 5,    # Balanced shutter (faster than default, brighter than 5)
                'gain': 255,                     # Maximum gain for fast shutter
                'brightness': 220,               # High brightness compensation
                'contrast': 200,                 # Maximum contrast for fabric patterns
                'sharpness': 255,               # Maximum sharpness for texture detail
                'saturation': 100,              # Reduced saturation for motion clarity
                'focus_automatic_continuous': 0, # Manual focus
                'focus_absolute': 40,            # Medium focus distance
                'white_balance_automatic': 1,    # Manual white balance
                'white_balance_temperature': 4500, # Neutral white balance (daylight balanced)
                'power_line_frequency': 2,       # 60Hz (avoid flicker)
                'backlight_compensation': 0      # Disable backlight compensation
            }
            
            # Apply each setting
            for setting, value in v4l2_settings.items():
                try:
                    cmd = ['v4l2-ctl', '-d', device, '--set-ctrl', f'{setting}={value}']
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        self.logger.info(f"  ✅ {setting}: {value}")
                    else:
                        self.logger.warning(f"  ⚠️  {setting}: {value} - {result.stderr.strip()}")
                        
                except subprocess.TimeoutExpired:
                    self.logger.error(f"  ❌ {setting}: timeout")
                except FileNotFoundError:
                    self.logger.error("v4l2-ctl not found - install with: sudo apt install v4l-utils")
                    return False
                except Exception as e:
                    self.logger.error(f"  ❌ {setting}: {e}")
            
            # Verify critical settings were applied
            self.verify_v4l2_settings(device)
            return True
            
        except Exception as e:
            self.logger.error(f"V4L2 configuration failed: {e}")
            return False
    
    def verify_v4l2_settings(self, device):
        """Verify critical v4l2 settings were applied"""
        try:
            critical_settings = ['auto_exposure', 'exposure_time_absolute', 'gain']
            
            cmd = ['v4l2-ctl', '-d', device, '--get-ctrl'] + [','.join(critical_settings)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.logger.info("🔍 V4L2 Settings Verification:")
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        self.logger.info(f"  {line.strip()}")
            
        except Exception as e:
            self.logger.warning(f"V4L2 verification failed: {e}")

    def log_all_camera_settings(self):
        """Log all camera settings for verification"""
        try:
            self.logger.info("📋 CURRENT CAMERA SETTINGS:")
            
            # Core settings
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            # Image quality settings
            exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            gain = self.cap.get(cv2.CAP_PROP_GAIN)
            brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
            contrast = self.cap.get(cv2.CAP_PROP_CONTRAST)
            sharpness = self.cap.get(cv2.CAP_PROP_SHARPNESS)
            saturation = self.cap.get(cv2.CAP_PROP_SATURATION)
            
            # Control settings
            autofocus = self.cap.get(cv2.CAP_PROP_AUTOFOCUS)
            auto_wb = self.cap.get(cv2.CAP_PROP_AUTO_WB)
            buffer_size = self.cap.get(cv2.CAP_PROP_BUFFERSIZE)
            
            self.logger.info(f"  Resolution: {width}x{height}")
            self.logger.info(f"  FPS: {fps}")
            self.logger.info(f"  Format: {fourcc_str}")
            self.logger.info(f"  Buffer Size: {buffer_size}")
            self.logger.info("  --- MOTION BLUR SETTINGS ---")
            self.logger.info(f"  Exposure: {exposure} (lower = faster shutter)")
            self.logger.info(f"  Gain: {gain}")
            self.logger.info(f"  Brightness: {brightness}")
            self.logger.info(f"  Contrast: {contrast}")
            self.logger.info(f"  Sharpness: {sharpness}")
            self.logger.info(f"  Saturation: {saturation}")
            self.logger.info("  --- CONTROL SETTINGS ---")
            self.logger.info(f"  Autofocus: {autofocus} (0=manual, 1=auto)")
            self.logger.info(f"  Auto White Balance: {auto_wb} (0=manual, 1=auto)")
            
            # Calculate approximate shutter speed from exposure
            if exposure != -1:  # -1 means auto
                approx_shutter = 1.0 / (2 ** abs(exposure))
                self.logger.info(f"  Estimated shutter speed: ~1/{int(1/approx_shutter)}s")
            
        except Exception as e:
            self.logger.error(f"Failed to read camera settings: {e}")
    
    def get_image_filename(self):
        """Generate timestamped filename for image"""
        timestamp = datetime.now().strftime("%H-%M-%S-%f")[:-3]  # Include milliseconds
        return f"{self.resolution_name}_{timestamp}.jpg"
    
    def save_frame(self, frame):
        """Save frame to session folder"""
        try:
            filename = self.get_image_filename()
            filepath = os.path.join(self.session_folder, filename)
            
            # Save image with high quality
            success = cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            
            if success:
                self.saved_images += 1
                # Get file size for logging
                file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                self.logger.info(f"Motion detected - Saved {self.resolution_name}: {filename} ({file_size:.1f} MB)")
                return True
            else:
                self.logger.error(f"Failed to save image: {filepath}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return False
    
    def initialize_camera(self):
        """Initialize camera with 1080p resolution and anti-ghosting settings"""
        try:
            # Configure camera using v4l2-ctl first for precise control
            if not self.configure_v4l2_settings():
                self.logger.warning("V4L2 configuration failed, using OpenCV settings only")
            
            # Use V4L2 backend for best performance
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Jetson Nano optimizations (only non-conflicting settings)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for low latency
            
            # Set 1080p resolution and format
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
            self.cap.set(cv2.CAP_PROP_FPS, 60)  # Higher FPS for sharper motion capture
            
            # NOTE: Image quality settings (exposure, gain, brightness, etc.) are controlled via v4l2-ctl
            # OpenCV settings would override the precise v4l2 configuration
            self.logger.info("📋 Using v4l2-ctl settings for image quality (not OpenCV overrides)")
            
            # Verify actual settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            actual_exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            actual_gain = self.cap.get(cv2.CAP_PROP_GAIN)
            fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            # Update instance variables
            self.width, self.height = actual_width, actual_height
            
            # Log final settings
            self.logger.info("✅ 1080p Camera initialized for ultra-fast fabric capture (horizontal motion):")
            self.logger.info(f"  Resolution: {actual_width}x{actual_height} ({self.resolution_name})")
            self.logger.info(f"  FPS: {actual_fps}")
            self.logger.info(f"  Format: {fourcc_str}")
            self.logger.info(f"  Exposure: {actual_exposure} (fast shutter for sharp motion)")
            self.logger.info(f"  Gain: {actual_gain} (compensates for fast exposure)")
            self.logger.info(f"  JPEG Quality: {self.jpeg_quality}%")
            self.logger.info(f"  Motion threshold: {self.motion_threshold} pixels")
            self.logger.info(f"  Motion cooldown: {self.motion_cooldown}s")
            self.logger.info(f"  Session folder: {self.session_folder}")
            
            # Display all current camera settings for verification
            self.log_all_camera_settings()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            return False
    
    def initialize_video_writer(self):
        """Initialize video writer for session recording"""
        try:
            session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.video_filename = os.path.join(self.session_folder, f"session_{session_timestamp}.mp4")
            
            # Use H.264 codec for good compression and compatibility
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Create video writer with 1080p resolution at 25fps
            self.video_writer = cv2.VideoWriter(
                self.video_filename,
                fourcc,
                25.0,  # FPS
                (self.width, self.height)
            )
            
            if self.video_writer.isOpened():
                self.logger.info(f"Video recording initialized: {os.path.basename(self.video_filename)}")
                return True
            else:
                self.logger.error("Failed to initialize video writer")
                return False
                
        except Exception as e:
            self.logger.error(f"Video writer initialization error: {e}")
            return False
    
    def detect_motion(self, frame):
        """Detect motion using full resolution processing for 1080p"""
        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            return False
        
        # For 1080p, use full resolution for motion detection
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference with higher sensitivity
        diff = cv2.absdiff(gray, prev_gray)
        motion_pixels = cv2.countNonZero(cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)[1])  # Lower threshold for more sensitivity
        
        # Update previous frame
        self.prev_frame = frame.copy()
        
        return motion_pixels > self.motion_threshold
    
    def scale_frame_for_preview(self, frame):
        """Scale frame to fit screen resolution maintaining aspect ratio"""
        if not self.show_preview:
            return frame
            
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate scaling to fit within screen resolution
        # Leave some margin for window decorations (80% of screen)
        max_width = int(self.preview_width * 0.8)
        max_height = int(self.preview_height * 0.8)
        
        # Calculate scale factors
        scale_width = max_width / frame_width
        scale_height = max_height / frame_height
        
        # Use the smaller scale factor to maintain aspect ratio
        scale = min(scale_width, scale_height, 1.0)  # Don't upscale
        
        # Calculate new dimensions
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        # Resize the frame
        if scale < 1.0:
            preview_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            preview_frame = frame.copy()
        
        return preview_frame
    
    def calculate_fps(self):
        """Calculate current FPS"""
        if len(self.frame_times) < 2:
            return 0.0
        time_span = self.frame_times[-1] - self.frame_times[0]
        return (len(self.frame_times) - 1) / time_span if time_span > 0 else 0.0
    
    def log_stats(self):
        """Log statistics periodically"""
        while self.running:
            time.sleep(5)  # Log every 5 seconds
            if self.frame_count > 0:
                current_fps = self.calculate_fps()
                elapsed = time.time() - self.start_time if self.start_time else 0
                
                self.logger.info(f"{self.resolution_name} Capture - Frames: {self.frame_count:5d} | "
                               f"FPS: {current_fps:4.1f} | "
                               f"Motion saves: {self.saved_images:4d} | "
                               f"Runtime: {elapsed:.0f}s")
    
    def capture_and_record(self):
        """Main capture loop with motion detection and video recording"""
        if not self.initialize_camera():
            return False
        
        if not self.initialize_video_writer():
            return False
        
        self.running = True
        self.start_time = time.time()
        
        self.logger.info(f"Starting {self.resolution_name} motion capture with video recording...")
        self.logger.info("Press Ctrl+C to stop")
        
        # Start logging thread
        log_thread = threading.Thread(target=self.log_stats, daemon=True)
        log_thread.start()
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.error("Failed to capture frame")
                    break
                
                current_time = time.time()
                self.frame_times.append(current_time)
                self.frame_count += 1
                
                # Write frame to video (every frame)
                if self.video_writer:
                    self.video_writer.write(frame)
                
                # Always check for motion to maintain algorithm state
                motion_detected = self.detect_motion(frame)
                
                # Only save if motion detected and cooldown period has passed
                if motion_detected and (current_time - self.last_motion_save >= self.motion_cooldown):
                    self.save_frame(frame)
                    self.last_motion_save = current_time
                
                # Display preview if screen detected
                if self.show_preview:
                    # Scale frame to fit screen resolution
                    preview_frame = self.scale_frame_for_preview(frame)
                    
                    # Use static window name to prevent multiple windows
                    window_name = "Motion Capture Preview"
                    cv2.imshow(window_name, preview_frame)
                    
                    # Update window title with capture count (if possible)
                    try:
                        cv2.setWindowTitle(window_name, f"{self.resolution_name} Motion Capture - {self.saved_images} captures")
                    except:
                        pass  # Ignore if setWindowTitle not available
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        self.logger.info("Preview window closed - stopping capture")
                        break
        
        except Exception as e:
            self.logger.error(f"Capture error: {e}")
        
        finally:
            self.stop_capture()
        
        return True
    
    def stop_capture(self):
        """Stop capture and cleanup"""
        self.running = False
        
        # Release camera
        if self.cap:
            self.cap.release()
        
        # Close video writer
        if self.video_writer:
            self.video_writer.release()
            self.logger.info(f"Video saved: {os.path.basename(self.video_filename)}")
        
        cv2.destroyAllWindows()
        
        # Final statistics
        if self.frame_count > 0:
            elapsed = time.time() - self.start_time if self.start_time else 0
            avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            self.logger.info("=" * 60)
            self.logger.info("SESSION SUMMARY:")
            self.logger.info(f"  Duration: {elapsed:.1f} seconds")
            self.logger.info(f"  Total frames: {self.frame_count}")
            self.logger.info(f"  Motion captures: {self.saved_images}")
            self.logger.info(f"  Average FPS: {avg_fps:.1f}")
            self.logger.info(f"  Session folder: {os.path.abspath(self.session_folder)}")
            
            if self.video_filename and os.path.exists(self.video_filename):
                video_size = os.path.getsize(self.video_filename) / (1024 * 1024)  # MB
                self.logger.info(f"  Video file: {os.path.basename(self.video_filename)} ({video_size:.1f} MB)")
            
            # Calculate image storage
            if self.saved_images > 0:
                # Resolution-aware storage estimation
                avg_image_size = 0.25  # MB per image for 1080p
                estimated_image_storage = self.saved_images * avg_image_size
                self.logger.info(f"  Image storage: ~{estimated_image_storage:.1f} MB")
            
            self.logger.info("=" * 60)

def main():
    """Main function - no user input required"""
    print("🎥 1080p Motion Capture with Video Recording")
    print("==========================================")
    print("Configuration:")
    print("  • Resolution: 1080p (1920x1080)")
    print("  • Mode: Motion detection")
    print("  • Threshold: 1,000 pixel changes")
    print("  • Cooldown: 1 second between captures")
    print("  • Video: Complete session recording")
    print("  • Storage: collection/yyyy-mm-dd-hh-mm/")
    print()
    
    # Create and run capture
    capture = MotionCapture1080p()
    success = capture.capture_and_record()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)