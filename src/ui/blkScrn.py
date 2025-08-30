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
    # Class-level variables to track cooldown
    _cooldown_end_time = 0
    COOLDOWN_SECONDS = 5
    
    @classmethod
    def is_in_cooldown(cls):
        """Check if we're in the cooldown period"""
        return time.time() < cls._cooldown_end_time
    
    @classmethod
    def start_cooldown(cls):
        """Start the cooldown period after screen closes"""
        cls._cooldown_end_time = time.time() + cls.COOLDOWN_SECONDS
    
    def __init__(self, user_email=None):
        super().__init__(None)  # Pass None as parent to ensure top-level window
        # Initialize essential attributes first
        self.user_email = user_email
        self.db = Database()
        self.remaining_time = 0
        self.prevent_close = True
        self.initialized = False  # Track initialization state
        
        # Check if we're in cooldown period
        if BlockScreen.is_in_cooldown():
            remaining = round(BlockScreen._cooldown_end_time - time.time(), 1)
            print(f"In cooldown period. Please wait {remaining} seconds.")
            self.close()
            return
            
        # Ensure proper window setup
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Clean up on close
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)  # Prevent automatic activation
        
        # Set window flags for proper fullscreen
        self.setWindowFlags(
            QtCore.Qt.Window |  # Ensure it's a window
            QtCore.Qt.FramelessWindowHint |  # No frame
            QtCore.Qt.WindowStaysOnTopHint |  # Always on top
            QtCore.Qt.X11BypassWindowManagerHint  # Bypass window manager
        )
        BlockScreen.start_cooldown()  # Start the cooldown period

        # Get the directory containing the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the paths to the UI and QSS files
        ui_file = os.path.join(current_dir, r"../../GUI/block_screen.ui")
        qss_file = os.path.join(current_dir, r"../../GUI/block_screen.qss")
        
        # Set window to be modal
        self.setModal(True)
        
        # Load UI
        uic.loadUi(ui_file, self)
        
        # Load and apply stylesheet
        with open(qss_file, 'r') as f:
            style = f.read()
            self.setStyleSheet(style)
        
        # Initialize timers
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.check_focus)
        
        # Set an opaque background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtCore.Qt.black)
        self.setPalette(palette)
        
        # Make sure the window takes up the full screen
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        self.setGeometry(screen_geometry)
        
        print("Block screen window flags set")
        # Use QTimer to ensure proper window setup before showing
        QtCore.QTimer.singleShot(0, self._show_fullscreen)
        print("Block screen fullscreen show scheduled")

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
        
        # Mark as fully initialized
        self.initialized = True
        
    def load_customization(self):
        """Load customization values from database"""
        if self.user_email:
            try:
                # Set custom message from database
                custom_message = self.db.get_setting(self.user_email, 'block_screen_message')
                if custom_message and hasattr(self, 'msg_txtBrwsr'):
                    print("Setting custom message:", custom_message)
                    try:
                        # Convert newlines to <br> tags and preserve formatting
                        formatted_message = custom_message.replace('\n', '<br>')

                        self.msg_txtBrwsr.setHtml(formatted_message)
                        # self.msg_txtBrwsr.setAlignment(QtCore.Qt.AlignCenter)

                        # font = self.msg_txtBrwsr.font()
                        # font.setFamily("Century Gothic")  # Ensure the font is available
                        # font.setPointSize(16)
                        # font.setWeight(QtWidgets.QFont.Bold)
                        # self.msg_txtBrwsr.setFont(font)
                        
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
            # Stop timers before any other operations
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            if hasattr(self, 'focus_timer'):
                self.focus_timer.stop()
                
            # Hide window before redirect to prevent visual artifacts
            self.hide()
            
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
            # Ensure window is hidden and destroyed
            self.hide()
            BlockScreen.start_cooldown()  # Start the cooldown period
            self.close()
            self.deleteLater()  # Ensure proper cleanup

    def closeEvent(self, event):
        """Handle window close event"""
        # If not fully initialized, allow close
        if not hasattr(self, 'initialized') or not self.initialized:
            event.accept()
            return
            
        # Only allow close if countdown is finished
        if self.remaining_time > 0:
            print("Blocking close attempt - countdown not finished")
            event.ignore()
            self.activateWindow()
            self.raise_()
            return
            
        print("Block screen closing...")
        # Start cooldown period when actually closing
        BlockScreen.start_cooldown()
        
        # Stop all timers
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if hasattr(self, 'focus_timer'):
            self.focus_timer.stop()
            
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
            
    def _show_fullscreen(self):
        """Show the window in proper fullscreen mode"""
        if not self.initialized:
            return
            
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        
        # Start timers after showing
        self.focus_timer.start(100)  # Check focus every 100ms
        self.countdown_timer.start(1000)  # Start countdown

    def check_focus(self):
        """Ensure block screen stays in focus and on top"""
        if self.initialized and not self.isActiveWindow() and self.remaining_time > 0:
            self.showFullScreen()  # Ensure it's still fullscreen
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
        if not hasattr(self, 'close_btn'):
            return
            
        try:
            original_text = self.close_btn.text()
            self.close_btn.setText(message)
            
            # Reset the text after 2 seconds, but only if the button still exists
            def restore_text():
                try:
                    if hasattr(self, 'close_btn'):
                        self.close_btn.setText(original_text)
                except RuntimeError:
                    # Button was already destroyed, ignore
                    pass
                    
            QTimer.singleShot(2000, restore_text)
        except RuntimeError:
            # Button was already destroyed when trying to set initial message
            pass

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
