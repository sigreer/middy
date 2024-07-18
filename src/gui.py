import sys
print(sys.path)
try:
    import pyudev
    print(pyudev.__version__)
except ImportError:
    pyudev = None
    print("pyudev is not available. USB port detection will be skipped.")

from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QLabel, QHBoxLayout
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtSvg import QSvgWidget  # Add this import
import mido
import subprocess
from PySide6.QtGui import QPixmap
import os
import queue

class MidiCommandApp(QMainWindow):
    midi_message_received = Signal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIDI to Command Mapper")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()

        self.device_selector = QComboBox(self)
        self.device_selector.setFixedWidth(150)  # Set width to 150px
        self.update_device_list()
        layout.addWidget(self.device_selector)
        
        self.toggle_button = QPushButton("Start Listening", self)
        self.toggle_button.setFixedWidth(150)  # Set width to 150px
        self.toggle_button.clicked.connect(self.toggle_listening)
        layout.addWidget(self.toggle_button)

        icon_container = QWidget(self)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        icon_layout.setAlignment(Qt.AlignLeft)  # Align left

        self.icon_label = QSvgWidget(self)
        self.icon_label.setFixedSize(50, 50)  # Set size to 50x50px
        icon_layout.addWidget(self.icon_label)

        icon_container.setFixedWidth(150)  # Set container width to 150px
        layout.addWidget(icon_container)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.midi_input = None
        self.command_map = {}
        self.last_note_on_event = None  # Variable to store the last note_on event

        self.midi_message_received.connect(self.handle_midi_message)

        self.message_queue = queue.Queue()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_message_queue)
        self.timer.start(100)  # Process messages every 100 ms

    def update_device_list(self):
        available_ports = mido.get_input_names()
        self.device_selector.clear()
        self.device_selector.addItems(available_ports)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_device_list()  # Update the device list when the window is shown

    def toggle_listening(self):
        if self.midi_input:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        try:
            selected_port = self.device_selector.currentText()
            if not selected_port:
                print("No MIDI input port selected")
                return

            print(f"Selected MIDI input port: {selected_port}")  # Debug print
            self.midi_input = mido.open_input(selected_port, callback=self.midi_callback)
            self.toggle_button.setText("Stop Listening")
            self.update_icon("listening")
            print(f"Started listening for MIDI messages on {selected_port}")  # Debug print
        except Exception as e:
            print(f"Error: {e}")
    
    def stop_listening(self):
        if self.midi_input:
            self.midi_input.close()
            self.midi_input = None
            self.toggle_button.setText("Start Listening")
            self.update_icon("unassigned")
    
    def update_icon(self, state):
        icon_map = {
            "unassigned": "assets/unassigned.svg",
            "listening": "assets/listening.svg",
            "assigned": "assets/assigned.svg",
        }
        icon_path = icon_map[state]
        print(f"Loading icon from: {icon_path}")  # Debug print
        if not os.path.exists(icon_path):
            print(f"Icon not found: {icon_path}")  # Debug print
        self.icon_label.load(icon_path)

    def midi_callback(self, message):
        print(f"MIDI callback triggered with message: {message}")  # Debug print
        self.message_queue.put(message)

    def process_message_queue(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if message.type == 'note_on':
                self.last_note_on_event = f"{message.channel}:{message.note}"
                self.midi_message_received.emit(f"Received MIDI message: {message}")

    def handle_midi_message(self, message):
        print(f"Handling MIDI message: {message}")  # Debug print
        self.stop_listening()  # Stop listening when a message is received
        print(message)
        print(f"Stored note_on event: {self.last_note_on_event}")  # Debug print
        if self.last_note_on_event:
            self.toggle_button.setText(self.last_note_on_event)
            self.update_icon("assigned")