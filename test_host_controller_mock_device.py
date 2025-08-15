#!/usr/bin/env python3
"""
Mock TTY Device for Host Controller Testing
Creates a virtual serial port pair and provides a GUI to send commands
"""

import sys
import os
import threading
import time
import pty
import select
import serial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QTextEdit, QGroupBox, QComboBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

class VirtualSerialPort(QThread):
    """Creates and manages a virtual serial port pair"""
    port_created = pyqtSignal(str)  # Emits the slave port name
    data_received = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.master_fd = None
        self.slave_name = None
        self.running = False
        
    def run(self):
        """Create virtual serial port and listen for data"""
        try:
            # Create pseudo-terminal pair
            self.master_fd, slave_fd = pty.openpty()
            self.slave_name = os.ttyname(slave_fd)
            
            self.status_update.emit(f"Virtual port created: {self.slave_name}")
            self.port_created.emit(self.slave_name)
            
            self.running = True
            
            # Listen for incoming data from host controller
            while self.running:
                # Use select to check for data without blocking
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                
                if ready:
                    try:
                        data = os.read(self.master_fd, 1024)
                        if data:
                            decoded_data = data.decode('utf-8', errors='ignore').strip()
                            if decoded_data:
                                self.data_received.emit(decoded_data)
                    except OSError:
                        # Port might be closed
                        break
                        
        except Exception as e:
            self.status_update.emit(f"Error creating virtual port: {str(e)}")
        finally:
            self.cleanup()
    
    def send_data(self, data):
        """Send data to the virtual port"""
        if self.master_fd and self.running:
            try:
                # Add newline if not present
                if not data.endswith('\n'):
                    data += '\n'
                os.write(self.master_fd, data.encode('utf-8'))
                return True
            except Exception as e:
                self.status_update.emit(f"Error sending data: {str(e)}")
                return False
        return False
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass
            self.master_fd = None
        self.status_update.emit("Virtual port closed")
    
    def stop(self):
        """Stop the virtual port"""
        self.cleanup()
        self.wait()

class MockDevice(QMainWindow):
    def __init__(self):
        super().__init__()
        self.virtual_port = None
        self.init_ui()
        self.create_virtual_port()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Mock TTY Device - Host Controller Tester")
        self.setGeometry(100, 100, 600, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Virtual port info group
        port_group = QGroupBox("Virtual Serial Port")
        port_layout = QVBoxLayout()
        
        self.port_label = QLabel("Port: Creating...")
        self.port_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        port_layout.addWidget(self.port_label)
        
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setStyleSheet("color: #64b5f6;")
        port_layout.addWidget(self.status_label)
        
        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "1. Use the port name above in your Host Controller\n"
            "2. Type commands below and click Send\n"
            "3. Try 'start' and 'stop' commands"
        )
        instructions.setStyleSheet("background-color: #3c3f41; padding: 10px; border: 1px solid #555; color: #e6e6e6;")
        port_layout.addWidget(instructions)
        
        port_group.setLayout(port_layout)
        main_layout.addWidget(port_group)
        
        # Command sending group
        command_group = QGroupBox("Send Commands")
        command_layout = QVBoxLayout()
        
        # Quick command buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick Commands:"))
        
        self.start_btn = QPushButton("Send START")
        self.start_btn.clicked.connect(lambda: self.send_command("start"))
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        quick_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Send STOP")
        self.stop_btn.clicked.connect(lambda: self.send_command("stop"))
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        quick_layout.addWidget(self.stop_btn)
        
        quick_layout.addStretch()
        command_layout.addLayout(quick_layout)
        
        # Custom command input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Custom Command:"))
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command and press Enter or click Send")
        self.command_input.returnPressed.connect(self.send_custom_command)
        input_layout.addWidget(self.command_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_custom_command)
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white;")
        input_layout.addWidget(self.send_btn)
        
        command_layout.addLayout(input_layout)
        
        # Preset commands dropdown
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset Commands:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "start",
            "stop", 
            "START",
            "STOP",
            "invalid_command",
            "test123",
            ""
        ])
        preset_layout.addWidget(self.preset_combo)
        
        self.send_preset_btn = QPushButton("Send Preset")
        self.send_preset_btn.clicked.connect(self.send_preset_command)
        preset_layout.addWidget(self.send_preset_btn)
        
        preset_layout.addStretch()
        command_layout.addLayout(preset_layout)
        
        command_group.setLayout(command_layout)
        main_layout.addWidget(command_group)
        
        # Communication log
        log_group = QGroupBox("Communication Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        clear_layout.addWidget(self.clear_log_btn)
        
        log_layout.addLayout(clear_layout)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Initially disable send buttons
        self.set_send_buttons_enabled(False)
        
        # Status bar
        self.statusBar().showMessage("Initializing virtual port...")
    
    def create_virtual_port(self):
        """Create the virtual serial port"""
        self.virtual_port = VirtualSerialPort()
        self.virtual_port.port_created.connect(self.on_port_created)
        self.virtual_port.data_received.connect(self.on_data_received)
        self.virtual_port.status_update.connect(self.on_status_update)
        self.virtual_port.start()
    
    def on_port_created(self, port_name):
        """Handle virtual port creation"""
        self.port_label.setText(f"Port: {port_name}")
        self.port_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #81c784;")
        self.set_send_buttons_enabled(True)
        self.log_message(f"Virtual port created: {port_name}")
        self.log_message("You can now connect your Host Controller to this port")
    
    def on_data_received(self, data):
        """Handle data received from host controller"""
        self.log_message(f"RECEIVED: {data}")
    
    def on_status_update(self, status):
        """Handle status updates"""
        self.status_label.setText(f"Status: {status}")
        if "Error" in status or "closed" in status:
            self.status_label.setStyleSheet("color: #e57373;")
            self.set_send_buttons_enabled(False)
        else:
            self.status_label.setStyleSheet("color: #81c784;")
        
        self.statusBar().showMessage(status)
    
    def set_send_buttons_enabled(self, enabled):
        """Enable/disable send buttons"""
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.send_preset_btn.setEnabled(enabled)
        self.command_input.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)
    
    def send_command(self, command):
        """Send a command through the virtual port"""
        if self.virtual_port and self.virtual_port.send_data(command):
            self.log_message(f"SENT: {command}")
        else:
            self.log_message(f"FAILED to send: {command}")
    
    def send_custom_command(self):
        """Send custom command from input field"""
        command = self.command_input.text().strip()
        if command:
            self.send_command(command)
            self.command_input.clear()
        else:
            QMessageBox.warning(self, "Warning", "Please enter a command to send")
    
    def send_preset_command(self):
        """Send preset command from dropdown"""
        command = self.preset_combo.currentText()
        if command:
            self.send_command(command)
        else:
            self.send_command("")  # Send empty command
    
    def log_message(self, message):
        """Add message to communication log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear the communication log"""
        self.log_text.clear()
        self.log_message("Log cleared")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.virtual_port:
            self.virtual_port.stop()
        event.accept()

def main():
    """Main function"""
    # Check if running on supported platform
    if os.name != 'posix':
        print("This mock device requires a POSIX system (Linux/macOS/WSL)")
        print("Virtual TTY creation is not supported on Windows natively")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Mock TTY Device")
    
    # Set application style
    app.setStyle('Fusion')
    
    # --- Dark mode palette and stylesheet ---
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(43, 43, 43))
    dark_palette.setColor(QPalette.WindowText, QColor(235, 235, 235))
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(235, 235, 235))
    dark_palette.setColor(QPalette.ToolTipText, QColor(235, 235, 235))
    dark_palette.setColor(QPalette.Text, QColor(235, 235, 235))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(235, 235, 235))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Highlight, QColor(61, 174, 233))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)

    # App-level stylesheet for fine-grained control
    app.setStyleSheet("""
    QWidget { background-color: #2b2b2b; color: #e6e6e6; }
    QGroupBox { border: 1px solid #444; margin-top: 6px; }
    QGroupBox::title { subcontrol-origin: margin; left: 7px; padding: 0 3px 0 3px; color: #e6e6e6; }
    QPushButton { background-color: #3c3f41; color: #e6e6e6; border: 1px solid #555; padding: 4px; border-radius: 3px; }
    QPushButton:disabled { background-color: #555; color: #999; }
    QLineEdit, QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #ffffff; selection-background-color: #3d6ea6; }
    QComboBox { background-color: #3c3f41; color: #e6e6e6; }
    QLabel { color: #e6e6e6; }
    QStatusBar { background: #2b2b2b; color: #cfcfcf; }
    QMenuBar, QMenu { background-color: #2b2b2b; color: #e6e6e6; }
    QScrollBar:vertical { background: #2b2b2b; width:12px; }
    """)
    # --- End dark mode styling ---
    
    # Create and show main window
    window = MockDevice()
    window.show()
    
    print("Mock TTY Device started")
    print("This will create a virtual serial port for testing the Host Controller")
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
