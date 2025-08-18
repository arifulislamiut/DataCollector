#!/usr/bin/env python3
"""
Host Controller - Hardware Button to Script Bridge
Industrial-grade headless controller for GPIO button input
No GUI dependencies, pure serial monitoring and script execution
"""

import sys
import os
import glob
import subprocess
import threading
import time
import serial
import json
import logging
import signal
from datetime import datetime

class ButtonController:
    def __init__(self, config_file="controller_config.json"):
        self.device = self.find_device()
        self.running_processes = {}
        self.serial_port = None
        self.monitoring = False
        self.config_file = config_file
        self.hardware_mode = self.device is not None
        self.venv_python = self.get_venv_python()
        
        self.setup_logging()
        self.setup_signal_handlers()
        self.load_config()
        
    def find_device(self):
        """Find the input device, prefer stable symlink"""
        # Priority order: stable symlink, then USB devices
        candidates = [
            '/dev/input-device',  # Stable udev symlink (preferred)
            *glob.glob('/dev/ttyUSB*'),
            *glob.glob('/dev/ttyACM*'),
            *glob.glob('/dev/pts/[1-9]*')  # Skip pts/0 (console)
        ]
        
        for device in candidates:
            if os.path.exists(device):
                return device
        
        # Return None instead of raising exception - allow software-only mode
        return None
    
    def get_venv_python(self):
        """Get the path to the virtual environment's Python interpreter"""
        # Check for Windows venv structure
        venv_python_win = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python_win):
            return venv_python_win
        
        # Check for Unix/Linux venv structure
        venv_python_unix = os.path.join(os.getcwd(), 'venv', 'bin', 'python')
        if os.path.exists(venv_python_unix):
            return venv_python_unix
        
        # Fallback to system python
        return sys.executable
    
    def setup_logging(self):
        """Configure logging for industrial monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('button_controller.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*50)
        self.logger.info("Button Controller Starting")
        if self.hardware_mode:
            self.logger.info(f"Device: {self.device}")
        else:
            self.logger.warning("WARNING: No serial device found. Running in software-only mode.")
            self.logger.warning("Connect ESP32/NodeMCU or run setup_hardware.sh for hardware button support.")
        self.logger.info(f"Python interpreter: {self.venv_python}")
        self.logger.info("="*50)
    
    def setup_signal_handlers(self):
        """Handle clean shutdown on SIGINT/SIGTERM"""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def load_config(self):
        """Load button command mappings from config file"""
        default_config = {
            "device": self.device,
            "baudrate": 115200,
            "commands": {
                "start": [self.venv_python, "capture_fhd.py"],
                "stop": ["pkill", "-f", "capture_fhd"],
                "func1": ["./sync_cron.sh"],
                "func2": ["./check_cron_sync.sh"],
                "up": ["brightness", "+10"],
                "down": ["brightness", "-10"],
                "left": ["echo", "LEFT button pressed"],
                "right": ["echo", "RIGHT button pressed"]
            },
            "scripts": {
                "capture": "capture_fhd.py",
                "sync": "./sync_cron.sh"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    self.config = {**default_config, **user_config}
                    # Ensure commands dict exists
                    if 'commands' not in self.config:
                        self.config['commands'] = default_config['commands']
                    self.logger.info(f"Loaded config from {self.config_file}")
            else:
                self.config = default_config
                # Save default config
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"Created default config: {self.config_file}")
                
        except Exception as e:
            self.logger.error(f"Config error: {e}, using defaults")
            self.config = default_config
    
    def monitor_buttons(self):
        """Main button monitoring loop"""
        if not self.hardware_mode:
            self.logger.info("Software-only mode: Hardware button monitoring disabled")
            self.logger.info("Available commands can be triggered via keyboard input or API")
            self.software_mode_loop()
            return
            
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"Opening serial connection: {self.device}")
                
                with serial.Serial(
                    port=self.device,
                    baudrate=self.config.get('baudrate', 115200),
                    timeout=1.0,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                ) as ser:
                    
                    self.serial_port = ser
                    self.monitoring = True
                    self.logger.info("Serial monitoring started - Ready for button input")
                    
                    # Reset retry counter on successful connection
                    retry_count = 0
                    
                    while self.monitoring:
                        try:
                            if ser.in_waiting > 0:
                                # Read command from serial
                                command = ser.readline().decode('utf-8', errors='ignore').strip().lower()
                                if command:
                                    self.handle_command(command)
                            
                            time.sleep(0.1)  # Prevent CPU spinning
                            
                        except serial.SerialException as e:
                            self.logger.error(f"Serial read error: {e}")
                            break
                        except Exception as e:
                            self.logger.error(f"Unexpected error in monitoring loop: {e}")
                            break
                            
            except serial.SerialException as e:
                retry_count += 1
                self.logger.error(f"Failed to open {self.device}: {e}")
                if retry_count < max_retries:
                    wait_time = retry_count * 2  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    self.logger.error("Max retries reached. Exiting.")
                    break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break
        
        self.logger.info("Serial monitoring stopped")
    
    def software_mode_loop(self):
        """Software-only mode - accept keyboard input for testing"""
        self.logger.info("Enter commands manually (or press Ctrl+C to exit):")
        self.logger.info(f"Available commands: {list(self.config['commands'].keys())}")
        
        try:
            while True:
                try:
                    command = input("Command: ").strip().lower()
                    if command:
                        if command in ['quit', 'exit', 'q']:
                            break
                        self.handle_command(command)
                except EOFError:
                    break
        except KeyboardInterrupt:
            self.logger.info("Software mode interrupted by user")
    
    def handle_command(self, command):
        """Handle button commands with process tracking"""
        self.logger.info(f"Button pressed: {command.upper()}")
        
        # Special handling for start/stop commands with process tracking
        if command == "start":
            self.start_capture()
        elif command == "stop":
            self.stop_capture()
        else:
            # Execute other commands from config
            cmd_list = self.config['commands'].get(command)
            if cmd_list:
                self.execute_command(command, cmd_list)
            else:
                self.logger.warning(f"Unknown command: {command}")
                self.logger.info(f"Available commands: {list(self.config['commands'].keys())}")
    
    def start_capture(self):
        """Start camera capture with process tracking"""
        if 'capture' in self.running_processes:
            proc = self.running_processes['capture']
            if proc.poll() is None:  # Still running
                self.logger.info("Camera capture already running")
                return
            else:
                # Process ended, remove from tracking
                del self.running_processes['capture']
        
        try:
            # Start camera capture using venv python
            capture_script = self.config['scripts'].get('capture', 'capture_fhd.py')
            process = subprocess.Popen(
                [self.venv_python, capture_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.running_processes['capture'] = process
            self.logger.info(f"Started camera capture (PID: {process.pid})")
            
            # Start thread to monitor process output
            threading.Thread(
                target=self.monitor_process_output,
                args=(process, 'capture'),
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"Failed to start camera capture: {e}")
    
    def stop_capture(self):
        """Stop camera capture"""
        stopped = False
        
        # First try to stop tracked process
        if 'capture' in self.running_processes:
            proc = self.running_processes['capture']
            try:
                proc.terminate()
                proc.wait(timeout=5)
                del self.running_processes['capture']
                self.logger.info(f"Stopped camera capture (PID: {proc.pid})")
                stopped = True
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                del self.running_processes['capture']
                self.logger.info("Force killed camera capture")
                stopped = True
            except Exception as e:
                self.logger.error(f"Error stopping tracked process: {e}")
        
        # Fallback: kill any capture_fhd processes
        if not stopped:
            try:
                result = subprocess.run(
                    ['pkill', '-f', 'capture_fhd'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.logger.info("Killed capture_fhd processes via pkill")
                else:
                    self.logger.info("No capture_fhd processes found to kill")
            except Exception as e:
                self.logger.error(f"Failed to pkill capture processes: {e}")
    
    def execute_command(self, command_name, cmd_list):
        """Execute a command from config"""
        try:
            # Handle shell scripts vs Python commands
            if cmd_list[0].endswith('.sh'):
                # Make shell script executable
                os.chmod(cmd_list[0], 0o755)
            elif cmd_list[0] in ['python', 'python3'] and len(cmd_list) > 1:
                # Replace python/python3 with venv python for Python scripts
                cmd_list = [self.venv_python] + cmd_list[1:]
            
            process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.logger.info(f"Executed {command_name}: {' '.join(cmd_list)} (PID: {process.pid})")
            
            # For non-long-running commands, wait and log result
            if command_name not in ['capture']:
                threading.Thread(
                    target=self.monitor_process_output,
                    args=(process, command_name),
                    daemon=True
                ).start()
            
        except Exception as e:
            self.logger.error(f"Failed to execute {command_name}: {e}")
    
    def monitor_process_output(self, process, command_name):
        """Monitor process output in background"""
        try:
            stdout, stderr = process.communicate(timeout=30)
            
            if stdout:
                self.logger.info(f"{command_name} output: {stdout.decode().strip()}")
            if stderr:
                self.logger.warning(f"{command_name} error: {stderr.decode().strip()}")
            
            if process.returncode == 0:
                self.logger.info(f"{command_name} completed successfully")
            else:
                self.logger.warning(f"{command_name} exited with code {process.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.info(f"{command_name} running in background...")
        except Exception as e:
            self.logger.error(f"Error monitoring {command_name}: {e}")
    
    def shutdown(self, signum=None, frame=None):
        """Clean shutdown"""
        self.logger.info("Shutdown signal received")
        self.monitoring = False
        
        # Stop all running processes
        for name, process in self.running_processes.items():
            try:
                if process.poll() is None:  # Still running
                    self.logger.info(f"Stopping {name}...")
                    process.terminate()
                    process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.info(f"Force killed {name}")
            except Exception as e:
                self.logger.error(f"Error stopping {name}: {e}")
        
        self.logger.info("Button Controller shutdown complete")
        sys.exit(0)

def main():
    """Main function"""
    try:
        controller = ButtonController()
        controller.monitor_buttons()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()