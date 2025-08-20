import os
import json
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.uic import loadUi
from ..utils.email_sender import EmailSender
from ..utils.helpers import generate_verification_code
from .code_input_widget import CodeInputWidget

class PartnerDialog(QDialog):
    partner_verified = pyqtSignal(str, str)  # Signal to emit when partner is verified (email, name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Get the absolute path to the GUI folder
        gui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "GUI")
        
        # Load the UI
        loadUi(os.path.join(gui_dir, "partner.ui"), self)
        
        # Initialize variables
        self.verification_code = None
        self.partner_email = None
        self.partner_name = None
        
        # Setup timers
        self.cooldown_timer = QTimer()
        self.cooldown_timer.setInterval(1000)  # 1 second interval for countdown
        self.cooldown_remaining = 30  # 30 seconds cooldown
        self.cooldown_timer.timeout.connect(self.update_cooldown)
        
        self.code_timer = QTimer()
        self.code_timer.setInterval(5 * 60 * 1000)  # 5 minutes expiration
        self.code_timer.timeout.connect(self.code_expired)
        
        # Initialize CodeInputWidget
        self.code_input = CodeInputWidget(self, cell_names=[
            'lineEdit_43', 'lineEdit_44', 'lineEdit_45', 
            'lineEdit_46', 'lineEdit_47', 'lineEdit_48'
        ])
        self.code_input.code_complete.connect(self.on_code_complete)
        self.code_input.setup_cells(self)
        
        # Connect signals
        self.signUp_btn.clicked.connect(self.send_verification)
        self.verify_btn_3.clicked.connect(self.verify_code)
        self.resend_btn_3.clicked.connect(self.send_verification)
        
    def send_verification(self):
        """Send verification code to partner's email"""
        self.partner_email = self.email_lineEdit.text().strip()
        self.partner_name = self.name_lineEdit.text().strip()
        
        if not self.partner_email or not self.partner_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter both name and email.")
            return
            
        # Start cooldown timer
        self.resend_btn_3.setEnabled(False)  # Disable resend button
        self.cooldown_remaining = 30
        self.cooldown_timer.start()  # Start countdown
        self.timer_lbl_3.setText("Wait 30 seconds to resend")
        
        # Generate verification code
        self.verification_code = generate_verification_code()
        
        # Load email configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'email_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                email_sender = EmailSender(
                    sender_email=config['email'],
                    sender_password=config['password']
                )
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Configuration Error",
                "Failed to load email configuration. Please check email_config.json")
            self.resend_btn_3.setEnabled(True)
            self.cooldown_timer.stop()
            return
        success, error = email_sender.send_verification_code(
            self.partner_email,
            self.verification_code
        )
        
        if success:
            # Start code expiration timer and switch to verification page
            self.code_timer.start()
            self.stackedWidget.setCurrentWidget(self.partnerVerf_page)
            QMessageBox.information(self, "Success", "Verification code sent to partner's email.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to send verification code: {error}")
            self.resend_btn_3.setEnabled(True)
            self.cooldown_timer.stop()
            
    def update_cooldown(self):
        """Update the cooldown timer display"""
        self.cooldown_remaining -= 1
        if self.cooldown_remaining <= 0:
            self.cooldown_timer.stop()
            self.resend_btn_3.setEnabled(True)
            self.timer_lbl_3.setText("You can resend the code now")
        else:
            self.timer_lbl_3.setText(f"Wait {self.cooldown_remaining} seconds to resend")
            
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
            
        if entered_code == self.verification_code:
            # Add partner to database and update UI
            success = self.parent.db.add_partner(
                self.parent.user_email,
                self.partner_name,
                self.partner_email
            )
            
            if success:
                # Update partner info in main window and emit signal
                self.parent.update_partner_info()
                self.partner_verified.emit(self.partner_email, self.partner_name)
                QMessageBox.information(self, "Success", "Partner added successfully!")
                self.accept()  # Use accept() for QDialog
            else:
                QMessageBox.critical(self, "Database Error", 
                    "Failed to add partner to database.\n\n"
                    "If this error persists, please check if the database file is accessible "
                    "and you have write permissions.")
                self.code_input.clear()
        else:
            QMessageBox.warning(self, "Invalid Code", "Incorrect verification code. Please try again.")
            self.code_input.clear()
            
    def code_expired(self):
        """Handle code expiration"""
        QMessageBox.warning(self, "Code Expired", 
            "The verification code has expired. Please request a new one.")
        self.stackedWidget.setCurrentWidget(self.partner_page)  # Go back to partner details entry
        self.resend_btn_3.setEnabled(True)
        self.cooldown_timer.stop()
