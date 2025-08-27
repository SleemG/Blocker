from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QTimer, QUrl, QDateTime
import sys
import os
import time

# Handle imports whether run as module or script
try:
    from ..utils.database import Database
except ImportError:
    # If running directly, modify path to import from parent directory
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.utils.database import Database

import webbrowser

class BlockScreen(QtWidgets.QDialog):
    # Class-level variables to track last shown time
    last_shown_time = 0
    DELAY_SECONDS = 5
    
    @classmethod
    def can_show_screen(cls):
        """Check if enough time has passed since last shown"""
        current_time = time.time()
        time_passed = current_time - cls.last_shown_time
        return time_passed >= cls.DELAY_SECONDS or cls.last_shown_time == 0
    
    @classmethod
    def update_last_shown(cls):
        """Update the last shown time"""
        cls.last_shown_time = time.time()
    
    def __init__(self, user_email=None):
        super().__init__()
        # Initialize essential attributes first
        self.user_email = user_email
        self.db = Database()
        self.remaining_time = 0
        self.prevent_close = True
        
        if not BlockScreen.can_show_screen():
            remaining_wait = BlockScreen.DELAY_SECONDS - (time.time() - BlockScreen.last_shown_time)
            print(f"Please wait {remaining_wait:.1f} seconds before showing block screen again")
            self.close()
            return
        BlockScreen.update_last_shown()  # Update last shown time

        # Set up focus check timer
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.check_focus)
        self.focus_timer.start(100)  # Check every 100ms

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
        
        # Initialize timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
            
        # Set window flags to ensure it stays on top and blocks input
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | 
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowSystemMenuHint |
            QtCore.Qt.X11BypassWindowManagerHint  # Bypass window manager
        )
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        
        # Set window attributes
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Clean up on close
        
        # Set modal to block input to other windows
        self.setModal(True)
        
        # Set an opaque background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtCore.Qt.black)
        self.setPalette(palette)
        
        print("Block screen window flags set")
        self.showFullScreen()
        print("Block screen shown fullscreen")

        # Ensure the window is activated and raised
        self.activateWindow()
        self.raise_()
        
        # Disconnect any existing connections on toggle_btn to prevent duplicate signals
        self.toggle_btn.clicked.disconnect() if self.toggle_btn.receivers(self.toggle_btn.clicked) > 0 else None
        
        # Initialize label state
        self.blkRsn_lbl.hide()  # Initially hide the label
        self.label_visible = False  # label is hidden at start

        # Connect buttons
        self.toggle_btn.clicked.connect(self.toggle_label)
        if hasattr(self, 'close_btn'):
            self.close_btn.clicked.connect(self.handle_close)
        if hasattr(self, 'redirect_btn'):
            self.redirect_btn.clicked.connect(self.handle_redirect)

        # Set default values
        self.remaining_time = 30  # Default countdown
        self.update_countdown_display()  # Initialize display
        
        # Load customization values
        self.load_customization()

    def load_customization(self):
        """Load customization values from database"""
        if self.user_email:
            try:
                # Set custom message from database
                custom_message = self.db.get_setting(self.user_email, 'block_screen_message')
                if custom_message and hasattr(self, 'msg_txtBrwsr'):
                    print("Setting custom message:", custom_message)
                    try:
                        self.msg_txtBrwsr.setHtml(custom_message)
                        self.msg_txtBrwsr.setAlignment(QtCore.Qt.AlignCenter)
                        print("Message set successfully")
                    except Exception as e:
                        print(f"Error setting message: {e}")
                        # Try plain text as fallback
                        self.msg_txtBrwsr.setPlainText(custom_message)

                # Set countdown duration from database
                duration = self.db.get_setting(self.user_email, 'block_screen_timer')
                try:
                    if duration:
                        self.remaining_time = int(duration)
                    else:
                        self.remaining_time = 30  # Default value
                    print(f"Setting countdown duration: {self.remaining_time} seconds")
                    
                    # Start the countdown timer
                    self.update_countdown_display()
                    self.countdown_timer.start(1000)
                    
                    # Update UI elements
                    if hasattr(self, 'countdown_label'):
                        self.countdown_label.setText(f"{self.remaining_time // 60:02d}:{self.remaining_time % 60:02d}")
                    if hasattr(self, 'close_btn'):
                        self.close_btn.setText(f"Close ({self.remaining_time})")
                except (ValueError, TypeError) as e:
                    print(f"Invalid duration value: {e}, using default")
                    self.remaining_time = 30

                # Set redirect URL from database
                redirect_url = self.db.get_setting(self.user_email, 'redirect_url')
                if redirect_url:
                    print("Setting redirect URL:", redirect_url)
                    self.redirect_url = redirect_url
                else:
                    self.redirect_url = "https://www.google.com"  # Default safe URL
                    # Save default URL to database
                    self.db.update_setting(self.user_email, 'redirect_url', self.redirect_url)
                    
            except Exception as e:
                print(f"Error loading customization: {e}")
                self.remaining_time = 30  # Fallback to default
                self.redirect_url = "https://www.google.com"

    def update_countdown(self):
        """Update the countdown timer"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_countdown_display()
            # Update close button text
            if hasattr(self, 'close_btn'):
                self.close_btn.setText(f"Close ({self.remaining_time})")
        else:
            self.countdown_timer.stop()
            self.handle_redirect()

    def update_countdown_display(self):
        """Update the countdown display in the UI"""
        if hasattr(self, 'countdown_label'):
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            print(f"Countdown updated: {minutes:02d}:{seconds:02d}")

    def handle_redirect(self):
        """Handle redirect when countdown ends"""
        try:
            if self.user_email:
                redirect_url = self.db.get_setting(self.user_email, 'redirect_url')
                if not redirect_url:
                    redirect_url = "https://www.google.com"  # Default safe URL
                # Ensure URL starts with http:// or https://
                if not redirect_url.startswith(('http://', 'https://')):
                    redirect_url = 'https://' + redirect_url
                webbrowser.open(redirect_url)
            else:
                webbrowser.open("https://www.google.com")  # Fallback for no email
        except Exception as e:
            print(f"Error in redirect: {e}")
            webbrowser.open("https://www.google.com")  # Fallback on error
        finally:
            self.hide()
            self.close()
            self.deleteLater()  # Ensure proper cleanup

    def closeEvent(self, event):
        """Handle window close event"""
        # Only allow close if countdown is finished
        if self.remaining_time > 0:
            print("Blocking close attempt - countdown not finished")
            event.ignore()
            self.activateWindow()
            self.raise_()
            return
            
        print("Block screen closing...")
        BlockScreen.update_last_shown()  # Update last shown time when closing
        self.hide()
        event.accept()
        self.deleteLater()

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Block Alt+F4 and other system keys
        if event.key() in (QtCore.Qt.Key_F4, QtCore.Qt.Key_Escape):
            event.ignore()
            return
        if event.modifiers() & (QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier):
            event.ignore()
            return
        super().keyPressEvent(event)
            
    def check_focus(self):
        """Ensure block screen stays in focus and on top"""
        if not self.isActiveWindow() and self.remaining_time > 0:
            self.activateWindow()
            self.raise_()

    def handle_close(self):
        """Handle close button click"""
        if self.remaining_time > 0:
            print("Cannot close - countdown not finished")
            self.show_status_message("Please wait for the countdown to finish")
            self.activateWindow()
            self.raise_()
            return
        # Only redirect when countdown is finished
        self.handle_redirect()

    def show_status_message(self, message: str):
        """Show a temporary status message"""
        if hasattr(self, 'close_btn'):
            original_text = self.close_btn.text()
            self.close_btn.setText(message)
            # Reset the text after 2 seconds
            QTimer.singleShot(2000, lambda: self.close_btn.setText(original_text))

    def toggle_label(self):
        """Toggle visibility of block reason label with animation"""
        # Create animation for opacity
        self.animation = QtCore.QPropertyAnimation(self.blkRsn_lbl, b"windowOpacity")
        self.animation.setDuration(250)  # Animation duration in milliseconds
        
        if self.label_visible:
            # Animate hiding
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)
            self.animation.finished.connect(self.blkRsn_lbl.hide)
        else:
            # Show immediately but animate opacity
            self.blkRsn_lbl.show()
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            
        self.animation.start()
        self.label_visible = not self.label_visible  # flip state


# Only run if script is executed directly
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # Use a test email for demonstration
    test_email = "test@example.com"
    window = BlockScreen(user_email=test_email)
    window.show()
    sys.exit(app.exec_())
