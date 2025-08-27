import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional

class EmailSender:
    def __init__(self, sender_email: str, sender_password: str):
        self.sender_email = sender_email
        self.sender_password = sender_password

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if an email address is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def send_verification_code(self, to_email: str, code: str) -> Tuple[bool, Optional[str]]:
        """Send verification code via email. Returns (success, error_message)"""
        try:
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Subject"] = "App Blocker - Email Verification"
            
            body = f"""
            Welcome to App Blocker!
            
            Your verification code is: {code}
            
            Please enter this code in the verification page to complete your registration.
            If you didn't request this code, please ignore this email.
            
            The code will expire in 5 minutes.
            
            Note: This email was sent from an automated system. Please do not reply.
            """
            
            message.attach(MIMEText(body, "plain"))
            
            # Connect to SMTP server (for Gmail)
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            return True, None
            
        except smtplib.SMTPAuthenticationError:
            return False, ("Failed to authenticate with Gmail.\n\n"
                         "If you're using Gmail, you need to use an App Password:\n"
                         "1. Go to your Google Account settings\n"
                         "2. Select 'Security'\n"
                         "3. Enable 2-Step Verification if not already enabled\n"
                         "4. Select 'App Passwords'\n"
                         "5. Generate a new app password for 'Mail'\n"
                         "6. Update the sender_password in the code")
        except smtplib.SMTPException as e:
            return False, f"SMTP Error: {str(e)}"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
