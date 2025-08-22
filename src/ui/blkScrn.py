from PyQt5 import QtWidgets, uic, QtCore
import sys
import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import webbrowser

class MainWindow(QtWidgets.QDialog):
    blockFinished = pyqtSignal(str)  # Signal to emit when block screen finishes

    def __init__(self, message="Access Blocked", countdown=60, redirect_url="https://www.google.com", reason=""):
        super().__init__()
        
        # Store parameters
        self.redirect_url = redirect_url
        self.remaining_time = countdown
        self.initial_countdown = countdown  # Store initial value for calculations
        self._setup_ui()
        self._setup_messages(message, reason)
        self._setup_window_flags()
        self._setup_timer()
    
    def _setup_ui(self):
        """Setup the UI components"""
        # Get the directory containing the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load UI and stylesheet
        ui_file = os.path.join(current_dir, r"../../GUI/block_screen.ui")
        qss_file = os.path.join(current_dir, r"../../GUI/block_screen.qss")
        
        uic.loadUi(ui_file, self)
        
        # Connect close button
        if hasattr(self, 'close_btn'):
            self.close_btn.clicked.connect(self._on_close_clicked)
            self.close_btn.setEnabled(False)  # Initially disabled
        
        # Connect toggle button for reason label
        if hasattr(self, 'toggle_btn') and hasattr(self, 'blkRsn_lbl'):
            self.toggle_btn.clicked.connect(self._toggle_reason_label)
            self.blkRsn_lbl.hide()  # Initially hidden
        
        with open(qss_file, 'r') as f:
            self.setStyleSheet(f.read())

    def _setup_messages(self, message, reason):
        """Setup the message and reason labels"""
        if hasattr(self, 'blkRsn_lbl'):
            self.blkRsn_lbl.setText(reason if reason else "Access to this content is blocked")
        
        if hasattr(self, 'msg_txtBrwsr'):
            self.msg_txtBrwsr.setText(message)
            
        if hasattr(self, 'close_btn'):
            self.close_btn.setText(f"Close ({self.remaining_time})")
            self.close_btn.setEnabled(False)  # Disable until countdown finishes

    def _setup_window_flags(self):
        """Setup window flags to keep on top and prevent closing"""
        flags = Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        self.setWindowFlags(flags)
        self.setWindowModality(Qt.ApplicationModal)  # Block input to other windows
        self.showFullScreen()

    def _setup_timer(self):
        """Setup the countdown timer"""
        self.timer = QTimer(self)  # Create timer with this window as parent
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every second

    def update_countdown(self):
        """Update countdown timer and handle redirection"""
        self.remaining_time -= 1
        
        # Update close button text
        if hasattr(self, 'close_btn'):
            self.close_btn.setText(f"Close ({self.remaining_time})")
        
        if self.remaining_time <= 0:
            if hasattr(self, 'close_btn'):
                self.close_btn.setEnabled(True)  # Enable the close button
                self.close_btn.setText("Close")  # Remove counter when done
            self.timer.stop()
            self.redirect_and_close()

    def redirect_and_close(self):
        """Handle redirection and window closing"""
        try:
            # Emit signal with redirect URL
            self.blockFinished.emit(self.redirect_url)
            # Try to open redirect URL
            webbrowser.open(self.redirect_url)
        finally:
            self.close()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.remaining_time > 0:
            event.ignore()  # Prevent closing if countdown not finished
        else:
            if self.timer.isActive():
                self.timer.stop()
            event.accept()
            
    def _on_close_clicked(self):
        """Handle close button click"""
        if self.remaining_time <= 0:
            self.close()

    def _toggle_reason_label(self):
        """Toggle the visibility of the reason label"""
        if hasattr(self, 'blkRsn_lbl'):
            visible = not self.blkRsn_lbl.isVisible()
            self.blkRsn_lbl.setVisible(visible)
            # Update toggle button text to show current state
            if hasattr(self, 'toggle_btn'):
                self.toggle_btn.setText("Why Blocked?! ˅" if not visible else "Why Blocked?! ˄")
            
    def keyPressEvent(self, event):
        """Prevent escape key from closing the window"""
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
