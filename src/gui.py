import sys
print(sys.path)
try:
    import pyudev
    print(pyudev.__version__)
except ImportError:
    pyudev = None
    print("pyudev is not available. USB port detection will be skipped.")

from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QLabel, QHBoxLayout, QLineEdit
from PySide6.QtCore import Signal, Slot, Qt, QTimer
try:
    from PySide6.QtSvg import QSvgWidget
except ImportError:
    QSvgWidget = None
    print("QSvgWidget is not available. SVG icons will not be displayed.")
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

        main_layout = QVBoxLayout()

        # Create a container for the dropdown, button, and icon
        control_container = QWidget(self)
        control_layout = QVBoxLayout(control_container)
        control_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        control_layout.setSpacing(2)  # Set spacing to 2px

        self.device_selector = QComboBox(self)
        self.device_selector.setFixedWidth(150)  # Set width to 150px
        self.update_device_list()
        control_layout.addWidget(self.device_selector)
        
        self.toggle_button = QPushButton("Start Listening", self)
        self.toggle_button.setFixedWidth(150)  # Set width to 150px
        self.toggle_button.clicked.connect(self.toggle_listening)
        control_layout.addWidget(self.toggle_button)

        # Add the new action selector dropdown
        self.action_selector = QComboBox(self)
        self.action_selector.setFixedWidth(150)  # Set width to 150px
        self.action_selector.addItems(["Run command", "Run shell script", "Send OBS command", "Load website"])
        control_layout.addWidget(self.action_selector)

        # Add the input box for user to enter their desired command, script location, OBS command, or website URL
        self.action_input = QLineEdit(self)
        self.action_input.setFixedWidth(150)  # Set width to 150px
        control_layout.addWidget(self.action_input)

        # Add the new 'Activate' button
        self.activate_button = QPushButton("Activate", self)
        self.activate_button.setFixedWidth(150)  # Set width to 150px
        self.activate_button.clicked.connect(self.activate_action)
        control_layout.addWidget(self.activate_button)

        icon_container = QWidget(self)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        icon_layout.setAlignment(Qt.AlignLeft)  # Align left

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(50, 50)  # Set size to 50x50px
        icon_layout.addWidget(self.icon_label)

        icon_container.setFixedWidth(150)  # Set container width to 150px
        icon_container.setFixedHeight(50)  # Set container height to 50px
        control_layout.addWidget(icon_container)

        # Calculate the fixed height for the control container
        control_container.setFixedHeight(
            self.device_selector.sizeHint().height() +
            self.toggle_button.sizeHint().height() +
            self.action_selector.sizeHint().height() +
            self.action_input.sizeHint().height() +  # Include the height of the new input box
            self.activate_button.sizeHint().height() +  # Include the height of the new 'Activate' button
            icon_container.sizeHint().height() +
            10  # 2px padding between each of the 5 elements, plus 2px for the new button
        )

        main_layout.addWidget(control_container)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.midi_input = None
        self.command_map = {}
        self.last_note_on_event = None  # Variable to store the last note_on event
        self.command1 = None  # Initialize the variable to store the command
        self.expected_note_on_event = None  # Variable to store the expected note_on event

        self.midi_message_received.connect(self.handle_midi_message)

        self.message_queue = queue.Queue()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_message_queue)
        self.timer.start(100)  # Process messages every 100 ms

        self.update_icon("unassigned")  # Set the initial icon to "unassigned"

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
            return

        pixmap = QPixmap(icon_path)
        self.icon_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def midi_callback(self, message):
        print(f"MIDI callback triggered with message: {message}")  # Debug print
        if message.type == 'note_on':
            note_on_event = f"{message.channel}:{message.note}"
            if self.expected_note_on_event and note_on_event == self.expected_note_on_event:
                print(f"received {note_on_event}")  # Print the received event
            elif not self.expected_note_on_event:
                self.last_note_on_event = note_on_event
                self.midi_message_received.emit(f"Received MIDI message: {message}")
                self.stop_listening()  # Stop listening when a message is received
                print(f"Stored note_on event: {self.last_note_on_event}")  # Debug print
                self.toggle_button.setText(self.last_note_on_event)
                self.update_icon("assigned")
            else:
                print(f"Ignored MIDI message: {message}")  # Debug print for ignored messages
        else:
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

    def activate_action(self):
        if self.action_selector.currentText() == "Run command":
            self.command1 = self.action_input.text()
            print(f"Command stored: {self.command1}")  # Debug print
            if self.last_note_on_event:
                self.expected_note_on_event = self.last_note_on_event
                print(f"Listening for MIDI event: {self.expected_note_on_event}")  # Debug print
                self.start_listening()  # Start listening for MIDI input