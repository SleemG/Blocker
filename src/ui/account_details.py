# from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
#                             QFormLayout, QStackedWidget)
# from PyQt5.QtGui import QFont
# from PyQt5.QtCore import Qt
# from datetime import datetime

# class AccountDetailsPage(QWidget):
#     """Widget for displaying user account details"""
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setup_ui()
        
#     def setup_ui(self):
#         layout = QVBoxLayout(self)
        
#         # User Details Group Box
#         self.userDetails_grbx = QGroupBox("Account Information")
#         self.userDetails_grbx.setStyleSheet("""
#             QGroupBox {
#                 background-color: #09c;
#                 border: 2px solid #e0e0e0;
#                 border-radius: 8px;
#                 margin-top: 15px;
#                 padding: 15px;
#             }
#             QGroupBox::title {
#                 background-color: #ffffff;
#                 color: #333333;
#                 font-weight: bold;
#                 subcontrol-origin: margin;
#                 subcontrol-position: top center;
#                 padding: 5px 10px;
#             }
#             QLabel {
#                 color: #333333;
#                 font-size: 13px;
#                 margin: 5px;
#             }
#             QLabel#valueLabel {
#                 color: #1a73e8;
#                 font-weight: bold;
#             }
#         """)
        
#         details_layout = QFormLayout(self.userDetails_grbx)
#         details_layout.setSpacing(15)
#         details_layout.setContentsMargins(20, 30, 20, 20)
        
#         # Username
#         self.name_label = QLabel()
#         self.name_label.setObjectName("valueLabel")
#         self.name_label.setFont(QFont("Arial", 11))
#         details_layout.addRow("Name:", self.name_label)
        
#         # Email
#         self.email_label = QLabel()
#         self.email_label.setObjectName("valueLabel")
#         self.email_label.setFont(QFont("Arial", 11))
#         details_layout.addRow("Email:", self.email_label)
        
#         # Login Date/Time
#         self.login_time_label = QLabel()
#         self.login_time_label.setObjectName("valueLabel")
#         self.login_time_label.setFont(QFont("Arial", 11))
#         details_layout.addRow("Logged in:", self.login_time_label)
        
#         layout.addWidget(self.userDetails_grbx)
#         layout.addStretch()
    
#     def update_user_details(self, name, email, login_time=None):
#         """Update the displayed user details"""
#         self.name_label.setText(name)
#         self.email_label.setText(email)
#         if login_time is None:
#             login_time = datetime.now()
#         self.login_time_label.setText(login_time.strftime("%Y-%m-%d %H:%M:%S"))
