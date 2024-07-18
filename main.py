from src.gui import MidiCommandApp
import sys
print(sys.path)
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MidiCommandApp()
    window.show()
    sys.exit(app.exec_())