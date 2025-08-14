#!/usr/bin/env python3
"""
Host Controller - PyQt GUI for device monitoring and script execution
Allows selection of COM/TTY devices and execution of Python scripts
"""

import sys
import os
import glob
import subprocess
import threading
import time
import serial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QComboBox, QPushButton, 
                            QTextEdit, QFileDialog, QMessageBox, QGroupBox,
                            QSplitter, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

class DeviceMonitor(QThread):
    """Thread to monitor device list changes"""
    devices_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.running = False
        
    def run(self):
        self.running = True
        last_devices = []
        
        while self.running:
            current_devices = self.get_devices()
            if current_devices != last_devices:
                self.devices_updated.emit(current_devices)
                last_devices = current_devices.copy()
            time.sleep(1.0)  # Check every second
    
    def stop(self):
        self.running = False
        self.wait()
    
    def get_devices(self):
        """Get list of available COM/TTY devices"""
        devices = []
        
        # Linux/Unix devices
        if os.name == 'posix':
            # USB serial devices
            usb_devices = glob.glob('/dev/ttyUSB*')
            devices.extend(sorted(usb_devices))
            
            # ACM devices (Arduino, etc.)
            acm_devices = glob.glob('/dev/ttyACM*')
            devices.extend(sorted(acm_devices))
            
            # Virtual TTY devices (pts)
            pts_devices = glob.glob('/dev/pts/*')
            # Filter out non-numeric pts devices and pts/0 (usually console)
            for pts in pts_devices:
                try:
                    pts_num = int(os.path.basename(pts))
                    if pts_num > 0:  # Skip pts/0 which is usually the console
                        devices.append(pts)
                except ValueError:
                    pass  # Skip non-numeric pts devices
            
            # Other serial devices
            other_devices = glob.glob('/dev/ttyS*')
            devices.extend(sorted(other_devices))
            
        # Windows devices
        elif os.name == 'nt':
            try:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                for port in sorted(ports, key=lambda x: x.device):
                    devices.append(f"{port.device} - {port.description}")
            except ImportError:
                # Fallback without pyserial
                for i in range(1, 21):  # COM1 to COM20
                    try:
                        # Try to open the port to see if it exists
                        import serial
                        ser = serial.Serial(f'COM{i}', timeout=0.1)
                        ser.close()
                        devices.append(f'COM{i}')
                    except:
                        pass
        
        return devices

class SerialMonitor(QThread):
    """Thread to monitor serial port for commands"""
    command_received = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        self.port_name = ""
        
    def set_port(self, port_name):
        """Set the serial port to monitor"""
        self.stop_monitoring()
        self.port_name = port_name
        
    def run(self):
        """Monitor serial port for commands"""
        if not self.port_name:
            return
            
        self.running = True
        
        try:
            # Extract just the device name for Linux
            device_name = self.port_name.split(' - ')[0] if ' - ' in self.port_name else self.port_name
            
            # Open serial connection
            self.serial_port = serial.Serial(
                port=device_name,
                baudrate=9600,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.status_update.emit(f"Monitoring {device_name}")
            
            # Read commands from serial port
            while self.running:
                try:
                    if self.serial_port.in_waiting > 0:
                        # Read line from serial port
                        line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self.status_update.emit(f"Received: {line}")
                            self.command_received.emit(line.lower())
                    
                    time.sleep(0.1)  # Small delay to prevent high CPU usage
                    
                except serial.SerialException as e:
                    self.status_update.emit(f"Serial error: {str(e)}")
                    break
                except Exception as e:
                    self.status_update.emit(f"Unexpected error: {str(e)}")
                    break
                    
        except serial.SerialException as e:
            self.status_update.emit(f"Failed to open {device_name}: {str(e)}")
        except Exception as e:
            self.status_update.emit(f"Error setting up serial monitor: {str(e)}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.status_update.emit("Serial monitoring stopped")
    
    def stop_monitoring(self):
        """Stop serial monitoring"""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.wait()

class ScriptRunner(QThread):
    """Thread to run Python scripts without blocking GUI"""
    output_ready = pyqtSignal(str)
    finished_signal = pyqtSignal(int)  # exit code
    
    def __init__(self, script_path, python_executable="python3"):
        super().__init__()
        self.script_path = script_path
        self.python_executable = python_executable
        self.process = None
        
    def run(self):
        try:
            # Start the process
            self.process = subprocess.Popen(
                [self.python_executable, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_ready.emit(line.rstrip())
            
            # Wait for process to complete
            self.process.wait()
            self.finished_signal.emit(self.process.returncode)
            
        except Exception as e:
            self.output_ready.emit(f"Error running script: {str(e)}")
            self.finished_signal.emit(-1)
    
    def stop_script(self):
        """Stop the running script"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
            if self.process.poll() is None:
                self.process.kill()

class HostController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_monitor = None
        self.serial_monitor = None
        self.script_runner = None
        self.selected_script = ""
        self.current_device = ""
        
        self.init_ui()
        self.start_device_monitoring()
        self.setup_serial_monitoring()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Host Controller - Device Monitor & Script Executor")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable sections
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # Device selection group
        device_group = QGroupBox("Device Selection")
        device_layout = QVBoxLayout()
        
        # Device dropdown
        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("COM/TTY Device:"))
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.device_combo.currentTextChanged.connect(self.on_device_selected)
        device_row.addWidget(self.device_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        device_row.addWidget(self.refresh_btn)
        
        device_layout.addLayout(device_row)
        
        # Selected device display
        self.selected_device_label = QLabel("Selected: None")
        self.selected_device_label.setStyleSheet("font-weight: bold; color: blue;")
        device_layout.addWidget(self.selected_device_label)
        
        # Serial monitoring status
        self.serial_status_label = QLabel("Serial: Not monitoring")
        self.serial_status_label.setStyleSheet("font-style: italic; color: gray;")
        device_layout.addWidget(self.serial_status_label)
        
        device_group.setLayout(device_layout)
        device_group.setMaximumHeight(150)
        
        # Script execution group
        script_group = QGroupBox("Script Execution")
        script_layout = QVBoxLayout()
        
        # Script selection
        script_row = QHBoxLayout()
        script_row.addWidget(QLabel("Python Script:"))
        
        self.script_path_label = QLabel("No script selected")
        self.script_path_label.setStyleSheet("border: 1px solid gray; padding: 5px; background-color: #f0f0f0;")
        script_row.addWidget(self.script_path_label)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_script)
        script_row.addWidget(self.browse_btn)
        
        script_layout.addLayout(script_row)
        
        # Execution controls
        exec_row = QHBoxLayout()
        
        self.run_btn = QPushButton("Run Script")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.run_btn.setEnabled(False)
        exec_row.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop Script")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.stop_btn.setEnabled(False)
        exec_row.addWidget(self.stop_btn)
        
        exec_row.addStretch()
        script_layout.addLayout(exec_row)
        
        script_group.setLayout(script_layout)
        script_group.setMaximumHeight(120)
        
        # Output display
        output_group = QGroupBox("Script Output")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        output_layout.addWidget(self.output_text)
        
        # Clear output button
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        clear_row.addWidget(self.clear_btn)
        
        output_layout.addLayout(clear_row)
        output_group.setLayout(output_layout)
        
        # Add groups to splitter
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(device_group)
        top_layout.addWidget(script_group)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter.addWidget(top_widget)
        splitter.addWidget(output_group)
        splitter.setStretchFactor(0, 0)  # Top section fixed
        splitter.setStretchFactor(1, 1)  # Output section expandable
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initial device refresh
        self.refresh_devices()
    
    def start_device_monitoring(self):
        """Start monitoring devices for changes"""
        self.device_monitor = DeviceMonitor()
        self.device_monitor.devices_updated.connect(self.update_device_list)
        self.device_monitor.start()
    
    def setup_serial_monitoring(self):
        """Setup serial port monitoring"""
        self.serial_monitor = SerialMonitor()
        self.serial_monitor.command_received.connect(self.handle_serial_command)
        self.serial_monitor.status_update.connect(self.update_serial_status)
    
    def handle_serial_command(self, command):
        """Handle commands received from serial port"""
        command = command.strip().lower()
        
        if command == "start":
            self.append_output(f"[SERIAL] Received START command")
            if self.selected_script and not self.script_runner:
                self.run_script()
            elif not self.selected_script:
                self.append_output("[SERIAL] No script selected - ignoring START command")
            else:
                self.append_output("[SERIAL] Script already running - ignoring START command")
                
        elif command == "stop":
            self.append_output(f"[SERIAL] Received STOP command")
            if self.script_runner:
                self.stop_script()
            else:
                self.append_output("[SERIAL] No script running - ignoring STOP command")
        else:
            self.append_output(f"[SERIAL] Unknown command: {command}")
    
    def update_serial_status(self, status):
        """Update serial monitoring status"""
        self.serial_status_label.setText(f"Serial: {status}")
        if "Monitoring" in status:
            self.serial_status_label.setStyleSheet("font-style: italic; color: green;")
        elif "error" in status.lower() or "failed" in status.lower():
            self.serial_status_label.setStyleSheet("font-style: italic; color: red;")
        else:
            self.serial_status_label.setStyleSheet("font-style: italic; color: gray;")
    
    def update_device_list(self, devices):
        """Update device dropdown with new device list"""
        current_selection = self.device_combo.currentText()
        
        self.device_combo.clear()
        if devices:
            self.device_combo.addItems(devices)
            # Try to restore previous selection
            index = self.device_combo.findText(current_selection)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        else:
            self.device_combo.addItem("No devices found")
        
        self.statusBar().showMessage(f"Found {len(devices)} device(s)")
    
    def refresh_devices(self):
        """Manually refresh device list"""
        if self.device_monitor:
            devices = self.device_monitor.get_devices()
            self.update_device_list(devices)
    
    def on_device_selected(self, device):
        """Handle device selection"""
        if device and device != "No devices found":
            self.selected_device_label.setText(f"Selected: {device}")
            self.selected_device_label.setStyleSheet("font-weight: bold; color: green;")
            
            # Start monitoring the selected device
            self.current_device = device
            if self.serial_monitor:
                self.serial_monitor.set_port(device)
                self.serial_monitor.start()
        else:
            self.selected_device_label.setText("Selected: None")
            self.selected_device_label.setStyleSheet("font-weight: bold; color: blue;")
            
            # Stop monitoring
            if self.serial_monitor:
                self.serial_monitor.stop_monitoring()
            self.current_device = ""
    
    def browse_script(self):
        """Open file dialog to select Python script"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Python files (*.py);;All files (*.*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_script = selected_files[0]
                script_name = os.path.basename(self.selected_script)
                self.script_path_label.setText(script_name)
                self.script_path_label.setToolTip(self.selected_script)  # Show full path on hover
                self.run_btn.setEnabled(True)
                self.statusBar().showMessage(f"Script selected: {script_name}")
    
    def run_script(self):
        """Run the selected Python script"""
        if not self.selected_script or not os.path.exists(self.selected_script):
            QMessageBox.warning(self, "Error", "Please select a valid Python script first.")
            return
        
        # Determine Python executable
        python_exe = "python3" if os.name == 'posix' else "python"
        
        # Clear output and show start message
        self.output_text.clear()
        self.append_output(f"Starting script: {os.path.basename(self.selected_script)}")
        self.append_output(f"Full path: {self.selected_script}")
        self.append_output("=" * 50)
        
        # Start script runner thread
        self.script_runner = ScriptRunner(self.selected_script, python_exe)
        self.script_runner.output_ready.connect(self.append_output)
        self.script_runner.finished_signal.connect(self.on_script_finished)
        self.script_runner.start()
        
        # Update UI state
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("Script running...")
    
    def stop_script(self):
        """Stop the running script"""
        if self.script_runner:
            self.append_output("\n[STOPPING SCRIPT...]")
            self.script_runner.stop_script()
            self.script_runner.wait(5000)  # Wait up to 5 seconds
            
        self.on_script_finished(-1)
    
    def on_script_finished(self, exit_code):
        """Handle script completion"""
        self.append_output("=" * 50)
        if exit_code == 0:
            self.append_output("Script completed successfully.")
        elif exit_code == -1:
            self.append_output("Script was stopped.")
        else:
            self.append_output(f"Script exited with code: {exit_code}")
        
        # Reset UI state
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Ready")
        
        self.script_runner = None
    
    def append_output(self, text):
        """Append text to output display"""
        self.output_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_output(self):
        """Clear the output display"""
        self.output_text.clear()
        self.statusBar().showMessage("Output cleared")
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop monitoring thread
        if self.device_monitor:
            self.device_monitor.stop()
        
        # Stop serial monitoring
        if self.serial_monitor:
            self.serial_monitor.stop_monitoring()
        
        # Stop script if running
        if self.script_runner:
            self.script_runner.stop_script()
            self.script_runner.wait(5000)
        
        event.accept()

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Host Controller")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = HostController()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
