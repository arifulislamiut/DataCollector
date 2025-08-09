#!/usr/bin/env python3
"""
Camera Capture with Date-wise Image Storage
Captures frames and saves images organized by date and time
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

class CameraCaptureStorage:
    def __init__(self, camera_index=0, target_fps=60, base_storage_path="captured_images", resolution="1080p"):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.base_storage_path = base_storage_path
        self.resolution = resolution.lower()
        self.cap = None
        self.running = False
        self.frame_times = deque(maxlen=60)
        self.frame_count = 0
        self.saved_images = 0
        self.start_time = None
        
        # Resolution settings
        if self.resolution == "4k":
            self.width, self.height = 3840, 2160
            self.jpeg_quality = 90  # Slightly lower for 4K file size management
            self.target_fps = 30    # Max supported at 4K
        else:  # Default to 1080p
            self.width, self.height = 1920, 1080
            self.jpeg_quality = 95  # High quality for 1080p
            self.resolution = "1080p"  # Normalize
        
        # Storage settings
        self.save_interval = 1.0  # Save one image per second by default
        self.last_save_time = 0
        self.current_date_folder = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Create base storage directory
        self.create_storage_structure()
    
    def signal_handler(self, sig, frame):
        self.logger.info("Stopping capture and storage...")
        self.stop_capture()
        sys.exit(0)
    
    def create_storage_structure(self):
        """Create base storage directory structure"""
        try:
            if not os.path.exists(self.base_storage_path):
                os.makedirs(self.base_storage_path)
                self.logger.info(f"Created base storage directory: {self.base_storage_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create storage directory: {e}")
            return False
    
    def get_date_folder_path(self):
        """Get current date folder path"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        date_folder = os.path.join(self.base_storage_path, current_date)
        
        # Create date folder if it doesn't exist
        if not os.path.exists(date_folder):
            os.makedirs(date_folder)
            self.logger.info(f"Created date folder: {date_folder}")
        
        return date_folder
    
    def get_image_filename(self):
        """Generate timestamped filename for image"""
        timestamp = datetime.now().strftime("%H-%M-%S-%f")[:-3]  # Include milliseconds
        prefix = "4K" if self.resolution == "4k" else "capture"
        return f"{prefix}_{timestamp}.jpg"
    
    def save_frame(self, frame):
        """Save frame to date-wise folder"""
        try:
            date_folder = self.get_date_folder_path()
            filename = self.get_image_filename()
            filepath = os.path.join(date_folder, filename)
            
            # Save image with resolution-optimized quality
            success = cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            
            if success:
                self.saved_images += 1
                # Get file size for logging
                file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                self.logger.info(f"Saved {self.resolution.upper()}: {filename} ({file_size:.1f} MB)")
                return True
            else:
                self.logger.error(f"Failed to save image: {filepath}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return False
    
    def initialize_camera(self):
        """Initialize camera with resolution-specific optimal settings"""
        try:
            # Use V4L2 backend for best performance
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set minimal buffer
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Set format and resolution
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            self.logger.info(f"{self.resolution.upper()} Camera initialized:")
            self.logger.info(f"  Resolution: {actual_width}x{actual_height}")
            self.logger.info(f"  Target FPS: {self.target_fps}")
            self.logger.info(f"  Camera FPS: {actual_fps}")
            self.logger.info(f"  Format: {fourcc_str}")
            self.logger.info(f"  JPEG Quality: {self.jpeg_quality}%")
            self.logger.info(f"  Storage: {self.base_storage_path}")
            
            # Verify resolution is correct
            if actual_width != self.width or actual_height != self.height:
                self.logger.warning(f"Expected {self.width}x{self.height} but got {actual_width}x{actual_height}")
                if self.resolution == "4k" and (actual_width != 3840 or actual_height != 2160):
                    self.logger.error("4K resolution not achieved - check camera support")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            return False
    
    def calculate_fps(self):
        """Calculate current FPS"""
        if len(self.frame_times) < 2:
            return 0.0
        time_span = self.frame_times[-1] - self.frame_times[0]
        return (len(self.frame_times) - 1) / time_span if time_span > 0 else 0.0
    
    def calculate_average_fps(self):
        """Calculate average FPS since start"""
        if self.start_time and self.frame_count > 0:
            elapsed = time.time() - self.start_time
            return self.frame_count / elapsed
        return 0.0
    
    def log_stats(self):
        """Log statistics periodically"""
        sleep_interval = 3 if self.resolution == "4k" else 2  # Longer interval for 4K
        while self.running:
            time.sleep(sleep_interval)
            if self.frame_count > 0:
                current_fps = self.calculate_fps()
                avg_fps = self.calculate_average_fps()
                
                # Calculate estimated storage
                avg_mb_per_image = self.estimate_image_size()
                total_mb = avg_mb_per_image * self.saved_images
                
                self.logger.info(f"{self.resolution.upper()} - Frames: {self.frame_count:5d} | "
                               f"FPS: {current_fps:4.1f} | "
                               f"Saved: {self.saved_images:4d} | "
                               f"Storage: {total_mb:.0f} MB")
    
    def capture_and_store(self, save_mode="interval", save_interval=1.0, show_preview=True, 
                         motion_threshold=5000, motion_cooldown=1.0):
        """
        Main capture loop with storage
        
        save_mode options:
        - "interval": Save every N seconds
        - "all": Save every frame (be careful with disk space!)
        - "manual": Save on spacebar press
        - "motion": Save when motion detected
        
        motion_threshold: Motion sensitivity (pixels changed, default: 5000)
                         Lower = more sensitive, Higher = less sensitive
        motion_cooldown: Minimum seconds between motion captures (default: 1.0)
        """
        if not self.initialize_camera():
            return False
        
        self.running = True
        self.start_time = time.time()
        self.save_interval = save_interval
        
        self.logger.info(f"Starting capture with storage...")
        self.logger.info(f"Save mode: {save_mode}")
        if save_mode == "interval":
            self.logger.info(f"Interval: {save_interval}s")
        elif save_mode == "motion":
            self.logger.info(f"Motion threshold: {motion_threshold} pixels")
            self.logger.info(f"Motion cooldown: {motion_cooldown}s")
        self.logger.info(f"Preview: {'ON' if show_preview else 'OFF'}")
        self.logger.info(f"Press Ctrl+C to stop")
        
        if show_preview:
            self.logger.info(f"Press 'q' to quit, 's' to save current frame, SPACE for manual save")
        
        # Start logging thread
        log_thread = threading.Thread(target=self.log_stats, daemon=True)
        log_thread.start()
        
        try:
            prev_frame = None  # For motion detection
            last_motion_save = 0  # For motion cooldown
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.error("Failed to capture frame")
                    break
                
                current_time = time.time()
                self.frame_times.append(current_time)
                self.frame_count += 1
                
                # Determine if we should save this frame
                should_save = False
                
                if save_mode == "interval":
                    if current_time - self.last_save_time >= save_interval:
                        should_save = True
                        self.last_save_time = current_time
                
                elif save_mode == "all":
                    should_save = True
                
                elif save_mode == "motion" and prev_frame is not None:
                    # Enhanced motion detection with 4K optimization
                    if current_time - last_motion_save >= motion_cooldown:
                        if self.resolution == "4k":
                            # Use downscaled frames for 4K motion detection (performance optimization)
                            small_frame = cv2.resize(frame, (960, 540))  # 1/4 size
                            small_prev = cv2.resize(prev_frame, (960, 540))
                            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                            prev_gray = cv2.cvtColor(small_prev, cv2.COLOR_BGR2GRAY)
                            diff = cv2.absdiff(gray, prev_gray)
                            motion_pixels = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
                            # Scale motion threshold for smaller comparison
                            effective_threshold = motion_threshold // 16  # Adjust for 1/4 size
                            display_motion = motion_pixels * 16  # Scale for display
                        else:
                            # Full resolution motion detection for 1080p
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                            diff = cv2.absdiff(gray, prev_gray)
                            motion_pixels = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
                            effective_threshold = motion_threshold
                            display_motion = motion_pixels
                        
                        if motion_pixels > effective_threshold:
                            should_save = True
                            last_motion_save = current_time
                            self.logger.info(f"{self.resolution.upper()} Motion detected: {display_motion} pixels changed")
                
                # Save frame if needed
                if should_save:
                    self.save_frame(frame)
                
                # Display preview with 4K optimization
                if show_preview:
                    if self.resolution == "4k":
                        # Downscale 4K for preview to improve performance
                        preview_frame = cv2.resize(frame, (1920, 1080))
                        window_title = f'4K Camera Capture (1080p Preview)'
                        if self.frame_count == 1:  # Show warning once
                            self.logger.warning("4K preview downscaled to 1080p for performance")
                    else:
                        preview_frame = frame
                        window_title = f'{self.resolution.upper()} Camera Capture'
                    
                    cv2.imshow(window_title, preview_frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        self.logger.info("Quit key pressed")
                        break
                    elif key == ord('s') or key == ord(' '):  # Manual save
                        self.save_frame(frame)
                        self.logger.info(f"Manual {self.resolution.upper()} save triggered")
                
                prev_frame = frame.copy()
        
        except Exception as e:
            self.logger.error(f"Capture error: {e}")
        
        finally:
            self.stop_capture()
        
        return True
    
    def stop_capture(self):
        """Stop capture and cleanup"""
        self.running = False
        
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics
        if self.frame_count > 0:
            elapsed = time.time() - self.start_time if self.start_time else 0
            avg_fps = self.calculate_average_fps()
            
            self.logger.info("=" * 60)
            self.logger.info("CAPTURE SESSION SUMMARY:")
            self.logger.info(f"  Duration: {elapsed:.1f} seconds")
            self.logger.info(f"  Frames captured: {self.frame_count}")
            self.logger.info(f"  Images saved: {self.saved_images}")
            self.logger.info(f"  Average FPS: {avg_fps:.1f}")
            self.logger.info(f"  Storage location: {os.path.abspath(self.base_storage_path)}")
            
            # Calculate storage info
            if self.saved_images > 0:
                avg_size_mb = self.estimate_storage_size() / self.saved_images
                total_size_mb = avg_size_mb * self.saved_images
                self.logger.info(f"  Estimated storage used: {total_size_mb:.1f} MB")
                self.logger.info(f"  Average image size: {avg_size_mb:.1f} MB")
            
            self.logger.info("=" * 60)
    
    def estimate_image_size(self):
        """Estimate average image size in MB"""
        if self.resolution == "4k":
            return 0.65  # Based on actual testing: ~0.65 MB per 4K image
        else:
            return 0.25  # 1080p: ~0.25 MB per image
    
    def estimate_storage_size(self):
        """Estimate total storage size in MB"""
        return self.saved_images * self.estimate_image_size()

def main():
    """Main function with user options"""
    print("📸 Camera Capture with Date-wise Storage")
    print("========================================")
    
    # Resolution selection
    print("\nResolution options:")
    print("1. 1080p (1920x1080) - Standard quality, smaller files (~0.25MB)")
    print("2. 4K (3840x2160) - Ultra high quality, larger files (~0.65MB)")
    
    resolution_choice = input("Choose resolution (1-2, default: 1): ").strip() or "1"
    
    resolution_map = {"1": "1080p", "2": "4k"}
    resolution = resolution_map.get(resolution_choice, "1080p")
    
    # Configuration options
    default_storage = "captured_images_4k" if resolution == "4k" else "captured_images"
    storage_path = input(f"Storage folder (default: '{default_storage}'): ").strip() or default_storage
    
    print("\nSave modes:")
    print("1. Interval - Save every N seconds")
    print("2. All frames - Save every single frame (WARNING: Lots of storage!)")
    print("3. Manual - Save on spacebar/s key press")
    print("4. Motion - Save when motion detected")
    
    mode_choice = input("Choose save mode (1-4, default: 1): ").strip() or "1"
    
    mode_map = {
        "1": "interval",
        "2": "all", 
        "3": "manual",
        "4": "motion"
    }
    
    save_mode = mode_map.get(mode_choice, "interval")
    
    # Resolution-specific defaults
    if resolution == "4k":
        save_interval = 3.0  # Longer interval recommended for 4K
        motion_threshold = 15000  # Higher threshold for 4K
        motion_cooldown = 2.0  # Longer cooldown for 4K
    else:
        save_interval = 1.0
        motion_threshold = 5000
        motion_cooldown = 1.0
    
    if save_mode == "interval":
        default_interval = "3.0 (recommended for 4K)" if resolution == "4k" else "1.0"
        interval_input = input(f"Save interval in seconds (default: {default_interval}): ").strip()
        try:
            save_interval = float(interval_input) if interval_input else save_interval
        except ValueError:
            save_interval = save_interval
    
    elif save_mode == "motion":
        print(f"\n🎯 Motion Detection Settings ({resolution.upper()}):")
        print("  Threshold: Lower = more sensitive, Higher = less sensitive")
        if resolution == "4k":
            print("  4K values: 10000 (sensitive), 15000 (normal), 25000 (less sensitive)")
        else:
            print("  1080p values: 1000 (very sensitive), 5000 (normal), 15000 (less sensitive)")
        
        threshold_input = input(f"Motion threshold (default: {motion_threshold}): ").strip()
        try:
            motion_threshold = int(threshold_input) if threshold_input else motion_threshold
        except ValueError:
            motion_threshold = motion_threshold
        
        cooldown_input = input(f"Cooldown between captures (default: {motion_cooldown}): ").strip()
        try:
            motion_cooldown = float(cooldown_input) if cooldown_input else motion_cooldown
        except ValueError:
            motion_cooldown = motion_cooldown
    
    preview_input = input("Show preview window? (y/n, default: y): ").strip().lower()
    show_preview = preview_input != 'n'
    
    print(f"\n🚀 Starting {resolution.upper()} capture:")
    print(f"  Resolution: {resolution.upper()}")
    print(f"  Storage: {storage_path}")
    print(f"  Save mode: {save_mode}")
    if save_mode == "interval":
        print(f"  Interval: {save_interval}s")
        if resolution == "4k":
            storage_per_hour = (3600 / save_interval) * 0.65  # MB per hour
            print(f"  Expected storage: ~{storage_per_hour:.0f} MB/hour")
    elif save_mode == "motion":
        print(f"  Motion threshold: {motion_threshold} pixels")
        print(f"  Motion cooldown: {motion_cooldown}s")
    print(f"  Preview: {'ON' if show_preview else 'OFF'}")
    if resolution == "4k" and show_preview:
        print("  Note: 4K preview downscaled to 1080p for performance")
    print()
    
    # Create and run capture with resolution
    capture = CameraCaptureStorage(camera_index=0, base_storage_path=storage_path, resolution=resolution)
    success = capture.capture_and_store(
        save_mode=save_mode,
        save_interval=save_interval,
        show_preview=show_preview,
        motion_threshold=motion_threshold,
        motion_cooldown=motion_cooldown
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)