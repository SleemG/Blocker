from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication
import sys
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
