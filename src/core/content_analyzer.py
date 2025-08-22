from typing import Dict, List, Optional
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sqlite3
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

class ContentAnalyzer:
    """Analyzes webpage content for adult content"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.load_block_settings()
        
    def load_block_settings(self):
        """Load blocking settings from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                # Get block message
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'blockMessage'",
                    (self.user_email,)
                )
                self.block_message = cursor.fetchone()[0] if cursor.fetchone() else "Access Blocked"
                
                # Get countdown duration
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'countdownDuration'",
                    (self.user_email,)
                )
                self.countdown_duration = int(cursor.fetchone()[0]) if cursor.fetchone() else 60
                
                # Get redirect URL
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'redirectUrl'",
                    (self.user_email,)
                )
                self.redirect_url = cursor.fetchone()[0] if cursor.fetchone() else "https://www.google.com"
        except Exception as e:
            print(f"Error loading block settings: {e}")
            # Set defaults
            self.block_message = "Access Blocked"
            self.countdown_duration = 60
            self.redirect_url = "https://www.google.com"

    def analyze_webpage(self, url: str) -> Dict:
        """Analyze webpage content for adult content"""
        try:
            # Get webpage content
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            title = soup.title.string if soup.title else ""
            meta_desc = soup.find('meta', {'name': 'description'})
            description = meta_desc['content'] if meta_desc else ""
            
            # Get visible text
            visible_text = ' '.join([
                text for text in soup.stripped_strings
                if len(text.strip()) > 0
            ])
            
            # Analyze content
            result = {
                'is_blocked': False,
                'reason': None,
                'confidence': 0.0
            }
            
            # Check title and meta description
            if self._check_adult_content(title) or self._check_adult_content(description):
                result['is_blocked'] = True
                result['reason'] = "Adult content detected in page metadata"
                result['confidence'] = 0.9
                return result
            
            # Check main content
            content_check = self._check_adult_content(visible_text)
            if content_check:
                result['is_blocked'] = True
                result['reason'] = "Adult content detected in page content"
                result['confidence'] = 0.8
                return result
            
            # Check images
            images = soup.find_all('img')
            for img in images:
                alt_text = img.get('alt', '')
                if self._check_adult_content(alt_text):
                    result['is_blocked'] = True
                    result['reason'] = "Adult content detected in image metadata"
                    result['confidence'] = 0.7
                    return result
            
            return result
            
        except Exception as e:
            print(f"Error analyzing webpage: {e}")
            return {'is_blocked': False, 'reason': None, 'confidence': 0.0}
    
    def _check_adult_content(self, text: str) -> bool:
        """Check if text contains adult content"""
        try:
            # Get blocked keywords from database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT keyword FROM blocked_keywords WHERE user_email = ?", (self.user_email,))
                blocked_keywords = cursor.fetchall()
                
            # Convert keywords to regex patterns
            patterns = []
            for (keyword,) in blocked_keywords:
                # Escape special regex characters and create word boundary pattern
                escaped_keyword = re.escape(keyword.strip())
                patterns.append(fr'\b{escaped_keyword}\b')
            
            # Add default patterns if no custom keywords
            if not patterns:
                patterns = [
                    r'\b(?:porn|xxx|adult[\s-]content|nsfw)\b',
                    r'\b(?:nude|naked|sex|explicit)\b',
                    r'\b(?:adult|mature|18\+|xxx)\b'
                ]
            
            # Check text against all patterns
            text = text.lower()
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            return False
            
        except Exception as e:
            print(f"Error checking adult content: {e}")
            return False

    def show_block_screen(self, url: str, reason: str):
        """Show block screen and handle redirection"""
        try:
            from src.ui.blkScrn import MainWindow
            
            # Get settings from database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get block message (from groupBox_6->plainTextEdit)
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'block_message'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                message = result[0] if result else "Access Blocked"
                
                # Get countdown duration (from groupBox_8->spinBox)
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'countdown_duration'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                countdown = int(result[0]) if result else 30
                
                # Get redirect URL (from groupBox_7->lineEdit_2)
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'redirect_url'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                redirect_url = result[0] if result else "https://www.google.com"
            
            # Create block screen with settings
            app = QApplication.instance() or QApplication([])
            block_screen = MainWindow(
                message=message,
                countdown=countdown,
                redirect_url=redirect_url,
                reason=f"Blocked: {reason}"
            )
            
            # Show the block screen
            block_screen.show()
            return block_screen
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
            return None
            timer.start(1000)  # Update every second
            
            block_screen.exec_()
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
