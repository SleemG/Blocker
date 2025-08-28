from typing import Dict, List, Optional, Set, Tuple
import re
import json
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
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'block_message'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                self.block_message = result[0] if result else """
                <div style='text-align: center; font-size: 18px; color: #2c3e50;'>
                    <h2 style='color: #e74c3c;'>اتقي الله في نفسك</h2>
                </div>"""
                
                # Get countdown duration
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'countdown_duration'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                self.countdown_duration = int(result[0]) if result else 60
                
                # Get redirect URL
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'redirect_url'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                self.redirect_url = result[0] if result else "https://www.google.com"
                
        except Exception as e:
            print(f"Error loading block settings: {e}")
            # Set defaults
            self.block_message = """<div style='text-align: center; font-size: 18px; color: #2c3e50;'>
<h2 style='color: #e74c3c;'>اتقي الله في نفسك</h2>
<p><strong>This content has been blocked for your protection.</strong></p>
<p>Content blocking helps maintain a safe and productive browsing environment.</p>
<p style='color: #7f8c8d; font-size: 14px;'>BlockerHero - Your Digital Wellness Partner</p>
</div>"""
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
    
    def _get_blocked_keywords(self) -> Set[str]:
        """Get all blocked keywords for the user"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                # Get user's custom keywords
                cursor.execute("SELECT keyword FROM blocked_keywords WHERE user_email = ?", (self.user_email,))
                custom_keywords = set(keyword[0].lower() for keyword in cursor.fetchall())
                
                # Get default keywords from settings
                cursor.execute("""
                    SELECT setting_value FROM user_settings 
                    WHERE user_email = ? AND setting_name = 'default_keywords'
                """, (self.user_email,))
                result = cursor.fetchone()
                if result and result[0]:
                    try:
                        default_keywords = set(json.loads(result[0]))
                    except json.JSONDecodeError:
                        default_keywords = set()
                else:
                    default_keywords = {
                        'porn', 'xxx', 'adult content', 'nsfw', 'nude', 'naked',
                        'sex', 'explicit', 'adult', 'mature', '18+'
                    }
                
                return custom_keywords.union(default_keywords)
                
        except Exception as e:
            print(f"Error getting blocked keywords: {e}")
            return set()

    def _check_adult_content(self, text: str) -> Tuple[bool, str]:
        """Check if text contains adult content. Returns (is_blocked, matching_keyword)"""
        try:
            if not text:
                return False, ""
                
            text = text.lower()
            blocked_keywords = self._get_blocked_keywords()
            
            # First check exact matches using word boundaries
            text_words = set(re.findall(r'\b\w+\b', text))
            for keyword in blocked_keywords:
                if keyword in text_words:
                    return True, keyword
            
            # Then check for phrases (which might span word boundaries)
            for keyword in blocked_keywords:
                if len(keyword.split()) > 1:  # Multi-word keyword
                    if keyword in text:
                        return True, keyword
                        
            # Finally, check for partial matches within words if enabled
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT setting_value FROM user_settings 
                    WHERE user_email = ? AND setting_name = 'strict_keyword_matching'
                """, (self.user_email,))
                result = cursor.fetchone()
                strict_matching = result[0].lower() == 'true' if result else True
            
            if not strict_matching:
                for keyword in blocked_keywords:
                    if keyword.replace(' ', '') in text.replace(' ', ''):
                        return True, keyword
            
            return False, ""
            
        except Exception as e:
            print(f"Error checking adult content: {e}")
            return False, ""

    def show_block_screen(self, url: str, reason: str):
        """Show block screen and handle redirection"""
        try:
            from src.ui.blkScrn import BlockScreen
            from PyQt5.QtWidgets import QApplication
            
            # Ensure we have a QApplication instance
            app = QApplication.instance() or QApplication([])
            
            # Create block screen with user email
            block_screen = BlockScreen(self.user_email)
            
            # Set the reason in the block screen
            if hasattr(block_screen, 'blkRsn_lbl'):
                block_screen.blkRsn_lbl.setText(f"Blocked: {reason}")
                
            # Show the block screen modally
            block_screen.exec_()
            
            return block_screen
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
            return None
