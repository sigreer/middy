from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit, QMessageBox
import mido
import subprocess

class MidiCommandApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIDI to Command Mapper")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()
        
        self.midi_port_label = QLabel("MIDI Input Port:")
        layout.addWidget(self.midi_port_label)

        self.midi_port_input = QLineEdit(self)
        layout.addWidget(self.midi_port_input)

        self.start_button = QPushButton("Start Listening", self)
        self.start_button.clicked.connect(self.start_listening)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Listening", self)
        self.stop_button.clicked.connect(self.stop_listening)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.midi_input = None
        self.command_map = {}

    def start_listening(self):
        port_name = self.midi_port_input.text()
        try:
            self.midi_input = mido.open_input(port_name, callback=self.midi_callback)
            QMessageBox.information(self, "Info", "Started listening on port: " + port_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def stop_listening(self):
        if self.midi_input:
            self.midi_input.close()
            self.midi_input = None
            QMessageBox.information(self, "Info", "Stopped listening")
    
    def midi_callback(self, message):
        if message.type == 'note_on':
            command = self.command_map.get(message.note)
            if command:
                subprocess.run(command, shell=True)

    def assign_command(self, note, command):
        self.command_map[note] = command
