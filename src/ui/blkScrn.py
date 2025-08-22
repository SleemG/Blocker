from PyQt5 import QtWidgets, uic, QtCore
import sys
import os

class MainWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Get the directory containing the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the paths to the UI and QSS files
        ui_file = os.path.join(current_dir, r"../../GUI/block_screen.ui")
        qss_file = os.path.join(current_dir, r"../../GUI/block_screen.qss")
        
        # Load UI
        uic.loadUi(ui_file, self)
        
        # Load and apply stylesheet
        with open(qss_file, 'r') as f:
            style = f.read()
            self.setStyleSheet(style)
            
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.showFullScreen()

        self.blkRsn_lbl.hide()  # Initially hide the label
        self.label_visible = False  # label is hidden at start

        # Connect button
        self.toggle_btn.clicked.connect(self.toggle_label)

    def toggle_label(self):
        if self.label_visible:  
            self.blkRsn_lbl.hide()   # hide label
        else:
            self.blkRsn_lbl.show()   # show label
        self.label_visible = not self.label_visible  # flip state


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
