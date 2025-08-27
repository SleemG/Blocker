from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    # app.setWindowIcon(QIcon("icons/app_icon.png"))  # Set application icon
    window = MainWindow(show_on_start=False)  # Don't show immediately
    
    # Initialize user before showing main window
    window.initialize_user()  # This will handle showing the window after verification
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
