from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class SettingsChangeDialog(QDialog):
    def __init__(self, parent=None, setting_name="", current_value=""):
        super().__init__(parent)
        self.parent = parent
        self.setting_name = setting_name
        self.current_value = current_value
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Partner Verification Required")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            f"Your accountability partner will be notified of this settings change.\n"
            f"Please enter their verification code to proceed."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Code input
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter verification code")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.code_input)
        
        # Verify button
        verify_btn = QPushButton("Verify")
        verify_btn.clicked.connect(self.verify_code)
        layout.addWidget(verify_btn)
        
        self.setLayout(layout)

    def verify_code(self):
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please enter the verification code.")
            return
            
        # TODO: Add actual verification logic here
        # For now, we'll accept any 6-digit code
        if len(code) == 6 and code.isdigit():
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid verification code.")
