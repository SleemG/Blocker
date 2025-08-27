import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QWidget, QVBoxLayout, 
                           QDialogButtonBox, QPushButton)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from .code_input_widget import CodeInputWidget
from PyQt5.uic import loadUi

from ..utils.database import Database
from ..utils.email_sender import EmailSender
from ..utils.helpers import generate_verification_code

class SignUpDialog(QMainWindow):
    code_verified = pyqtSignal(str)  # Signal to emit when code is verified

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get the application root directory
        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        gui_dir = os.path.join(app_root, 'GUI')
        
        # Load UI file
        ui_file = os.path.join(gui_dir, 'SignUp.ui')
        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"UI file not found at {ui_file}")
        loadUi(ui_file, self)
        
        # Load modern stylesheet
        style_file = os.path.join(gui_dir, 'modern_style.qss')
        if not os.path.exists(style_file):
            raise FileNotFoundError(f"Style file not found at {style_file}")
        with open(style_file, "r") as f:
            self.setStyleSheet(f.read())
        
        # Initialize database and email sender
        self.db = Database()
        self.email_sender = EmailSender(
            "mogee.hasob@gmail.com",  #app gmail
            "cjll atcz nyrr rfqt"     # app password
        )
        
        # Instance variables
        self.verification_code = None
        self.email = None
        
        # Setup timers  
        self.cooldown_timer = QTimer()
        self.cooldown_timer.setInterval(1000)  # 1 second interval for countdown
        self.cooldown_remaining = 30  # 30 seconds cooldown
        self.cooldown_timer.timeout.connect(self.update_cooldown)
        
        self.code_timer = QTimer()
        self.code_timer.setInterval(5 * 60 * 1000)  # 5 minutes expiration
        self.code_timer.timeout.connect(self.code_expired)
        
        # Initialize CodeInputWidget with the line edits from Qt Designer
        self.code_input = CodeInputWidget(self, cell_names=[
            'lineEdit', 'lineEdit_2', 'lineEdit_3', 
            'lineEdit_4', 'lineEdit_5', 'lineEdit_6'
        ])
        self.code_input.code_complete.connect(self.on_code_complete)
        # Setup the cells with the line edits from the UI
        self.code_input.setup_cells(self)
        
        # Connect signals
        self.signUp_btn.clicked.connect(self.send_verification_code)  # Send verification code button
        self.verify_btn.clicked.connect(self.verify_code)  # Verify button
        self.resend_btn.clicked.connect(self.send_verification_code)  # Resend button
            
        # Initially disable verification page
        self.stackedWidget.setCurrentIndex(0)  # Show signup_pg
        
        # Create database tables
        self.db.create_tables()

    def update_cooldown(self):
        """Update the cooldown timer display"""
        self.cooldown_remaining -= 1
        if self.cooldown_remaining <= 0:
            self.cooldown_timer.stop()
            self.resend_btn.setEnabled(True)
            self.timer_lbl.setText("You can resend the code now")
        else:
            self.timer_lbl.setText(f"Wait {self.cooldown_remaining} seconds to resend")
        
    def send_verification_code(self):
        """Send a verification code via email"""
        self.email = self.email_lineEdit.text().strip()  # Email input field
        
        # Validate email format
        if not self.email_sender.is_valid_email(self.email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        
        # Start cooldown timer
        self.resend_btn.setEnabled(False)  # Disable resend button
        self.cooldown_remaining = 30
        self.cooldown_timer.start()  # Start countdown
        self.timer_lbl.setText("Wait 30 seconds to resend")
        
        # Generate a 6-digit verification code
        self.verification_code = generate_verification_code()
        
        # Send verification email
        success, error_message = self.email_sender.send_verification_code(self.email, self.verification_code)
        
        if success:
            # Store code in database
            if self.db.add_verification_code(self.email, self.verification_code)[0]:
                # Start code expiration timer and switch to verification page
                self.code_timer.start()
                self.stackedWidget.setCurrentWidget(self.verify_pg)
                
                QMessageBox.information(self, "Verification Sent", 
                    "A verification code has been sent to your email.\n"
                    "Please check your inbox and enter the code.")
            else:
                QMessageBox.critical(self, "Database Error", 
                    "Failed to store verification code.\n"
                    "Please try again.")
                self.signUp_btn.setEnabled(True)
                self.cooldown_timer.stop()
        else:
            QMessageBox.critical(self, "Email Error", error_message)
            self.signUp_btn.setEnabled(True)
            self.cooldown_timer.stop()
            
    def on_code_complete(self, code):
        """Called when all 6 digits are entered"""
        self.verify_code(code)
        
    def verify_code(self, entered_code=None):
        """Verify the entered code"""
        if entered_code is None:
            entered_code = self.code_input.get_code()
        
        if not entered_code:
            QMessageBox.warning(self, "Invalid Code", "Please enter the complete 6-digit code.")
            return
            
        if not self.email:
            QMessageBox.warning(self, "Error", "Email address not found. Please try again.")
            return
            
        success, error_message = self.db.verify_code(self.email, entered_code)
        
        if success:
            # Get username
            username = self.name_lineEdit.text().strip()
            if not username:
                QMessageBox.warning(self, "Invalid Input", "Please enter a username!")
                return
                
            # Add verified user to database
            success, add_error = self.db.add_user(self.email, username)
            if success:
                self.code_verified.emit(self.email)
                self.close()  # Use close() for QMainWindow instead of accept()
            else:
                QMessageBox.critical(self, "Database Error",
                    f"Failed to create user account: {add_error}\n"
                    "Please try again.")
                self.code_input.clear()  # Clear the input for retry
        else:
            QMessageBox.warning(self, "Verification Failed", error_message)
            self.code_input.clear()  # Clear the input for retry
            
    def code_expired(self):
        """Handle code expiration"""
        QMessageBox.warning(self, "Code Expired", 
            "The verification code has expired. Please request a new one.")
        self.stackedWidget.setCurrentWidget(self.signup_pg)  # Go back to email entry
        self.signUp_btn.setEnabled(True)  # Enable send button
        self.cooldown_timer.stop()
