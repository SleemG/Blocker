import sys
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QListWidget, 
                           QListWidgetItem, QTextEdit, QTabWidget, QMessageBox,
                           QDialog, QFormLayout, QLineEdit, QComboBox, QStackedWidget)
from src.ui.account_details import AccountDetailsPage
from datetime import datetime
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

class EmailConfig:
    """Email configuration class"""
    def __init__(self):
        # Gmail SMTP settings (modify for other email providers)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993

class NotificationData:
    """Class to handle notification data structure"""
    def __init__(self, sender_email, notification_type, setting_name, 
                 new_value, old_value, timestamp, notification_id):
        self.sender_email = sender_email
        self.notification_type = notification_type  # 'request' or 'response'
        self.setting_name = setting_name
        self.new_value = new_value
        self.old_value = old_value
        self.timestamp = timestamp
        self.notification_id = notification_id
        self.status = 'pending'  # 'pending', 'accepted', 'rejected'

class EmailService(QObject):
    """Service class to handle email operations"""
    notification_received = pyqtSignal(dict)
    
    def __init__(self, user_email, user_password):
        super().__init__()
        self.user_email = user_email
        self.user_password = user_password
        self.config = EmailConfig()
        self.is_monitoring = False
        
    def send_notification(self, recipient_email, notification_data):
        """Send notification via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.user_email
            msg['To'] = recipient_email
            msg['Subject'] = f"App Notification - {notification_data['type']}"
            
            # Create email body
            body = json.dumps(notification_data, indent=2)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.user_email, self.user_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def start_monitoring(self):
        """Start monitoring for incoming notifications"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_emails)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring emails"""
        self.is_monitoring = False
    
    def _monitor_emails(self):
        """Monitor emails for notifications"""
        while self.is_monitoring:
            try:
                # Connect to IMAP server
                mail = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
                mail.login(self.user_email, self.user_password)
                mail.select('inbox')
                
                # Search for unread emails
                result, data = mail.search(None, 'UNSEEN SUBJECT "App Notification"')
                
                if result == 'OK' and data[0]:
                    email_ids = data[0].split()
                    
                    for email_id in email_ids:
                        # Fetch email
                        result, data = mail.fetch(email_id, '(RFC822)')
                        if result == 'OK':
                            email_message = email.message_from_bytes(data[0][1])
                            
                            # Parse email content
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        try:
                                            notification_data = json.loads(body)
                                            self.notification_received.emit(notification_data)
                                        except json.JSONDecodeError:
                                            continue
                            
                            # Mark as read
                            mail.store(email_id, '+FLAGS', '\\Seen')
                
                mail.close()
                mail.logout()
                
            except Exception as e:
                print(f"Error monitoring emails: {e}")
            
            time.sleep(10)  # Check every 10 seconds

class NotificationWidget(QWidget):
    """Widget for displaying individual notifications"""
    def __init__(self, notification_data, parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self.parent_tab = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header with sender and timestamp
        header_layout = QHBoxLayout()
        sender_label = QLabel(f"From: {self.notification_data.get('sender_email', 'Unknown')}")
        sender_label.setFont(QFont("Arial", 10, QFont.Bold))
        timestamp_label = QLabel(f"Time: {self.notification_data.get('timestamp', 'Unknown')}")
        
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(timestamp_label)
        
        # Notification content
        if self.notification_data.get('type') == 'setting_change_request':
            if self.notification_data.get('setting_type') == 'checkbox':
                checkbox_name = self.notification_data.get('checkbox_name', 'Unknown')
                new_state = self.notification_data.get('checkbox_state', False)
                state_text = "uncheck" if not new_state else "check"
                content_text = f"""Setting Change Request:

Your partner wants to {state_text} the following setting:
Setting: {checkbox_name}

Do you want to accept this change?"""
            else:
                content_text = f"""Setting Change Request:
            
Setting: {self.notification_data.get('setting_name', 'Unknown')}
Current Value: {self.notification_data.get('old_value', 'Unknown')}
Requested Value: {self.notification_data.get('new_value', 'Unknown')}
            
Do you want to accept this change?"""
        else:
            content_text = f"""Response to your request:
            
Setting: {self.notification_data.get('setting_name', 'Unknown')}
Status: {self.notification_data.get('response', 'Unknown')}"""
        
        content_label = QLabel(content_text)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        
        # Action buttons (only for requests)
        button_layout = QHBoxLayout()
        if self.notification_data.get('type') == 'setting_change_request':
            accept_btn = QPushButton("Accept")
            reject_btn = QPushButton("Reject")
            
            accept_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 3px;")
            reject_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px; border-radius: 3px;")
            
            accept_btn.clicked.connect(lambda: self.respond_to_request('accepted'))
            reject_btn.clicked.connect(lambda: self.respond_to_request('rejected'))
            
            button_layout.addWidget(accept_btn)
            button_layout.addWidget(reject_btn)
        
        button_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #757575; color: white; padding: 5px 15px; border-radius: 3px;")
        delete_btn.clicked.connect(self.delete_notification)
        button_layout.addWidget(delete_btn)
        
        # Add all to main layout
        layout.addLayout(header_layout)
        layout.addWidget(content_label)
        layout.addLayout(button_layout)
        
        # Add separator line
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #ccc; margin: 10px 0;")
        layout.addWidget(separator)
        
        self.setLayout(layout)
        self.setStyleSheet("margin: 5px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;")
    
    def respond_to_request(self, response):
        """Send response back to requester"""
        response_data = {
            'type': 'setting_change_response',
            'sender_email': self.parent_tab.app.user_email,
            'original_id': self.notification_data.get('id'),
            'setting_name': self.notification_data.get('setting_name'),
            'setting_type': self.notification_data.get('setting_type'),
            'action': self.notification_data.get('action'),
            'item': self.notification_data.get('item'),
            'old_value': self.notification_data.get('old_value'),
            'new_value': self.notification_data.get('new_value'),
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send response via email
        recipient_email = self.notification_data.get('sender_email')
        if self.parent_tab.app.email_service.send_notification(recipient_email, response_data):
            msg = "Change approved" if response == "accepted" else "Change rejected"
            QMessageBox.information(self, "Response Sent", f"{msg} and notification sent successfully!")
            self.delete_notification()
        else:
            QMessageBox.warning(self, "Error", "Failed to send response!")
    
    def delete_notification(self):
        """Delete this notification"""
        self.parent_tab.remove_notification(self)

class NotificationTab(QWidget):
    """Main notification tab widget"""
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.notifications = []
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Notifications")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet("margin: 10px 0; color: #333;")
        
        # Notifications container (scrollable)
        self.notifications_layout = QVBoxLayout()
        self.notifications_widget = QWidget()
        self.notifications_widget.setLayout(self.notifications_layout)
        
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.notifications_widget)
        
        # Empty state message
        self.empty_label = QLabel("No notifications")
        self.empty_label.setStyleSheet("color: #999; font-style: italic; text-align: center; margin: 50px;")
        self.notifications_layout.addWidget(self.empty_label)
        
        main_layout.addWidget(header_label)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def add_notification(self, notification_data):
        """Add a new notification"""
        # Remove empty state message if it exists
        if self.empty_label.parent():
            self.empty_label.hide()
        
        notification_widget = NotificationWidget(notification_data, self)
        self.notifications_layout.insertWidget(0, notification_widget)  # Add at top
        self.notifications.append(notification_widget)
    
    def remove_notification(self, notification_widget):
        """Remove a notification"""
        self.notifications_layout.removeWidget(notification_widget)
        notification_widget.deleteLater()
        if notification_widget in self.notifications:
            self.notifications.remove(notification_widget)
        
        # Show empty state if no notifications
        if len(self.notifications) == 0:
            self.empty_label.show()

class SettingsChangeDialog(QDialog):
    """Dialog for requesting setting changes"""
    def __init__(self, parent=None, setting_type=None, action=None, item=None, current_list=None, 
                 is_checkbox=False, checkbox_name=None, checkbox_state=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setting_type = setting_type  # 'whitelist', 'blocklist', or 'checkbox'
        self.action = action  # 'add', 'remove', or 'change'
        self.item = item
        self.current_list = current_list
        self.is_checkbox = is_checkbox
        self.checkbox_name = checkbox_name
        self.checkbox_state = checkbox_state
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Confirm Setting Change")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QFormLayout()
        
        # Create hidden fields for internal use
        self.setting_name = QLineEdit()
        self.setting_name.hide()
        self.current_value = QLineEdit()
        self.current_value.hide()
        self.new_value = QLineEdit()
        self.new_value.hide()
        
        # Show informative message
        message = self.create_message()
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addRow(message_label)
        
        button_layout = QHBoxLayout()
        send_btn = QPushButton("Send Request")
        cancel_btn = QPushButton("Cancel")
        
        send_btn.clicked.connect(self.send_request)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(send_btn)
        button_layout.addWidget(cancel_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_message(self):
        """Create an informative message about the requested change"""
        if self.is_checkbox:
            state_text = "uncheck" if self.checkbox_state is False else "check"
            message = f"""
You are about to {state_text} the following setting:

Setting: {self.checkbox_name}

This change requires your partner's approval. A request will be sent to your partner.
Do you want to proceed?
"""
        else:
            action_text = "add to" if self.action == "add" else "remove from"
            list_type = "whitelist" if self.setting_type == "whitelist" else "blocklist"
            message = f"""
You are about to {action_text} the {list_type}:

Item: {self.item}

This change requires your partner's approval. A request will be sent to your partner.
Do you want to proceed?
"""
        return message

    def send_request(self):
        """Send the setting change request"""
        request_data = {
            'type': 'setting_change_request',
            'id': f"req_{int(time.time())}",
            'sender_email': self.parent_app.user_email,
            'timestamp': datetime.now().isoformat()
        }

        if self.is_checkbox:
            # Handle checkbox setting change
            request_data.update({
                'setting_type': 'checkbox',
                'setting_name': self.checkbox_name,
                'action': 'change',
                'old_value': str(not self.checkbox_state),  # Current state
                'new_value': str(self.checkbox_state),      # Requested state
                'checkbox_name': self.checkbox_name,
                'checkbox_state': self.checkbox_state
            })
        else:
            # Handle whitelist/blocklist changes
            new_list = list(self.current_list)
            if self.action == "add":
                new_list.append(self.item)
            else:
                new_list.remove(self.item)

            request_data.update({
                'setting_name': f"{self.setting_type}_{self.action}",
                'setting_type': self.setting_type,
                'action': self.action,
                'item': self.item,
                'old_value': json.dumps(self.current_list),
                'new_value': json.dumps(new_list)
            })
        
        if self.parent_app.email_service.send_notification(self.parent_app.partner_email, request_data):
            QMessageBox.information(self, "Success", "Request sent successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to send request!")

class MainApplication(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.user_email = ""
        self.user_name = ""
        self.partner_email = ""
        self.email_service = None
        self.login_time = None
        self.setup_ui()
        self.setup_email_config()
        
    def setup_ui(self):
        self.setWindowTitle("Partner Notification App")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create notification tab
        self.notification_tab = NotificationTab(self)
        self.tab_widget.addTab(self.notification_tab, "Notifications")
        
        # Create settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Create stacked widget for settings
        self.settings_stacked = QStackedWidget()
        
        # Add Account Details page
        self.accountDetails_page = AccountDetailsPage()
        self.settings_stacked.addWidget(self.accountDetails_page)
        
        # Add other widgets
        request_btn = QPushButton("Request Setting Change")
        request_btn.clicked.connect(self.open_request_dialog)
        settings_layout.addWidget(request_btn)
        settings_layout.addWidget(self.settings_stacked)
        
        self.tab_widget.addTab(settings_tab, "Settings")
        
        layout.addWidget(self.tab_widget)
    
    def setup_email_config(self):
        """Setup email configuration dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Email Configuration")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        user_name_edit = QLineEdit()
        user_email_edit = QLineEdit()
        user_password_edit = QLineEdit()
        user_password_edit.setEchoMode(QLineEdit.Password)
        partner_email_edit = QLineEdit()
        
        layout.addRow("Your Name:", user_name_edit)
        layout.addRow("Your Email:", user_email_edit)
        layout.addRow("Your Password:", user_password_edit)
        layout.addRow("Partner Email:", partner_email_edit)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        def on_ok():
            if all([user_name_edit.text(), user_email_edit.text(), 
                   user_password_edit.text(), partner_email_edit.text()]):
                self.user_name = user_name_edit.text()
                self.user_email = user_email_edit.text()
                self.partner_email = partner_email_edit.text()
                self.login_time = datetime.now()
                
                # Initialize email service
                self.email_service = EmailService(self.user_email, user_password_edit.text())
                self.email_service.notification_received.connect(self.handle_notification)
                self.email_service.start_monitoring()
                
                # Update account details
                if hasattr(self, 'accountDetails_page'):
                    self.accountDetails_page.update_user_details(
                        self.user_name,
                        self.user_email,
                        self.login_time
                    )
                    # Show the account details page
                    self.settings_stacked.setCurrentWidget(self.accountDetails_page)
                
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please fill all fields!")
        
        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(button_layout)
        
        dialog.setLayout(main_layout)
        
        if dialog.exec_() != QDialog.Accepted:
            self.close()
    
    def open_request_dialog(self):
        """Open dialog to request setting change"""
        dialog = SettingsChangeDialog(self)
        dialog.exec_()
    
    def handle_notification(self, notification_data):
        """Handle incoming notifications"""
        self.notification_tab.add_notification(notification_data)
        
        # Switch to notification tab
        self.tab_widget.setCurrentWidget(self.notification_tab)
        
        if notification_data.get('type') == 'setting_change_request':
            # Show notification for setting change request
            setting_type = notification_data.get('setting_type', '')
            action = notification_data.get('action', '')
            item = notification_data.get('item', '')
            msg = f"Partner wants to {action} '{item}' to/from {setting_type}"
            QMessageBox.information(self, "New Setting Change Request", msg)
        
        elif notification_data.get('type') == 'setting_change_response':
            # Handle the response and apply changes if accepted
            if notification_data.get('response') == 'accepted':
                # Apply the change
                setting_type = notification_data.get('setting_type')
                action = notification_data.get('action')
                item = notification_data.get('item')
                self.apply_setting_change(setting_type, action, item)
                
                QMessageBox.information(self, "Setting Change Approved", 
                    f"Your request to {action} '{item}' to/from {setting_type} has been approved and applied.")
            else:
                QMessageBox.warning(self, "Setting Change Rejected",
                    f"Your setting change request was rejected by your partner.")
    
    def apply_setting_change(self, setting_type, action, item):
        """Apply the approved setting change"""
        # This method should be connected to your main application's settings system
        if hasattr(self, 'main_window'):
            if setting_type == 'checkbox':
                # Handle checkbox setting changes
                checkbox_name = item  # In this case, item is the checkbox name
                checkbox_state = self.notification_data.get('checkbox_state', False)
                self.main_window.update_checkbox_setting(checkbox_name, checkbox_state)
            elif setting_type == 'whitelist':
                if action == 'add':
                    self.main_window.add_to_whitelist(item)
                else:
                    self.main_window.remove_from_whitelist(item)
            elif setting_type == 'blocklist':
                if action == 'add':
                    self.main_window.add_to_blocklist(item)
                else:
                    self.main_window.remove_from_blocklist(item)
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.email_service:
            self.email_service.stop_monitoring()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainApplication()
    window.show()
    
    sys.exit(app.exec_())