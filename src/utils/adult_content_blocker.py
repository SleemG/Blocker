"""
Adult Content Blocker - Comprehensive content filtering system
Blocks adult content in browsers and applications using multiple detection techniques.
"""

import sys
import time
import threading
import sqlite3
import re
import requests
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import psutil
import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QApplication, QDesktopWidget, QProgressBar)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class AdultContentBlocker:
    """Main adult content blocking system"""
    
    def __init__(self, db_path="app_blocker.db"):
        self.db_path = db_path
        self.is_active = False
        self.block_screen = None
        self.monitoring_thread = None
        self.setup_database()
        self.load_adult_keywords()
        
        # Browser monitoring
        self.browser_processes = ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']
        
    def setup_database(self):
        """Initialize the blocking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for blocked content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_keywords (
                id INTEGER PRIMARY KEY,
                keyword TEXT UNIQUE,
                category TEXT,
                severity INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_domains (
                id INTEGER PRIMARY KEY,
                domain TEXT UNIQUE,
                category TEXT,
                severity INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS block_logs (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                content_type TEXT,
                content_source TEXT,
                block_reason TEXT,
                app_name TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_adult_keywords(self):
        """Load comprehensive adult content keywords"""
        adult_keywords = [
            # Explicit content keywords
            'porn', 'xxx', 'sex', 'adult', 'nude', 'naked', 'erotic', 'nsfw',
            'webcam', 'escort', 'massage', 'dating', 'hookup', 'fetish',
            'lesbian', 'gay', 'bisexual', 'transgender', 'bdsm', 'kinky',
            'strip', 'lingerie', 'underwear', 'bikini', 'swimsuit',
            
            # Adult website patterns
            'redtube', 'pornhub', 'xvideos', 'youporn', 'xhamster', 'tube8',
            'spankbang', 'chaturbate', 'cam4', 'livejasmin', 'stripchat',
            'onlyfans', 'manyvids', 'clips4sale',
            
            # Gambling and inappropriate content
            'casino', 'poker', 'gambling', 'bet', 'lottery', 'slots',
            'violence', 'gore', 'blood', 'murder', 'death', 'suicide',
            'drugs', 'cocaine', 'marijuana', 'heroin', 'meth',
            
            # Social media adult content indicators
            'dm me', 'snap me', 'kik me', 'telegram', 'onlyfans link',
            'premium snap', 'sell nudes', 'sugar daddy', 'sugar baby'
        ]
        
        adult_domains = [
            'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com', 'youporn.com',
            'tube8.com', 'spankbang.com', 'xhamster.com', 'chaturbate.com',
            'cam4.com', 'livejasmin.com', 'stripchat.com', 'onlyfans.com',
            'manyvids.com', 'clips4sale.com', 'adultfriendfinder.com',
            'ashley-madison.com', 'seeking.com', 'tinder.com', 'bumble.com'
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert keywords
        for keyword in adult_keywords:
            cursor.execute('''
                INSERT OR IGNORE INTO blocked_keywords (keyword, category, severity)
                VALUES (?, 'adult', 3)
            ''', (keyword,))
            
        # Insert domains
        for domain in adult_domains:
            cursor.execute('''
                INSERT OR IGNORE INTO blocked_domains (domain, category, severity)
                VALUES (?, 'adult', 3)
            ''', (domain,))
            
        conn.commit()
        conn.close()
        
    def start_monitoring(self):
        """Start the content monitoring system"""
        if not self.is_active:
            self.is_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_content, daemon=True)
            self.monitoring_thread.start()
            print("Adult content blocker started")
            
    def stop_monitoring(self):
        """Stop the content monitoring system"""
        self.is_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("Adult content blocker stopped")
        
    def _monitor_content(self):
        """Main monitoring loop"""
        while self.is_active:
            try:
                # Monitor browser content
                self._monitor_browsers()
                
                # Monitor applications using OCR
                self._monitor_applications_ocr()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
                
    def _monitor_browsers(self):
        """Monitor browser content for adult material"""
        try:
            # Get active browser processes
            browser_procs = []
            for proc in psutil.process_iter(['pid', 'name']):
                if any(browser in proc.info['name'].lower() for browser in self.browser_processes):
                    browser_procs.append(proc)
                    
            if not browser_procs:
                return
                
            # Check browser content using automation
            self._check_browser_content()
            
        except Exception as e:
            print(f"Browser monitoring error: {e}")
            
    def _check_browser_content(self):
        """Check current browser content for adult material"""
        try:
            # Use Chrome WebDriver to check current tab content
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Get current active window URL (simplified approach)
            # In practice, you'd need to integrate with browser APIs
            current_url = self._get_current_browser_url()
            
            if current_url:
                if self._analyze_url_content(current_url, driver):
                    self._trigger_block_screen("Website", current_url, "Adult content detected")
                    
            driver.quit()
            
        except Exception as e:
            print(f"Browser content check error: {e}")
            
    def _get_current_browser_url(self):
        """Get current browser URL (simplified implementation)"""
        # This is a placeholder - in practice, you'd need browser-specific APIs
        # or browser extensions to get the current URL
        return None
        
    def _analyze_url_content(self, url, driver=None):
        """Analyze URL content for adult material"""
        try:
            # Check domain against blocked list
            domain = urlparse(url).netloc.lower()
            if self._is_domain_blocked(domain):
                return True
                
            # Fetch and analyze page content
            if driver:
                driver.get(url)
                title = driver.title.lower()
                page_source = driver.page_source.lower()
            else:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string.lower() if soup.title else ""
                page_source = response.text.lower()
                
            # Check title and content for adult keywords
            if self._contains_adult_content(title) or self._contains_adult_content(page_source):
                return True
                
            # Check meta descriptions
            if driver:
                meta_desc = driver.find_elements(By.XPATH, "//meta[@name='description']")
                if meta_desc and self._contains_adult_content(meta_desc[0].get_attribute("content")):
                    return True
            else:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and self._contains_adult_content(meta_desc.get("content", "")):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"URL analysis error: {e}")
            return False
            
    def _monitor_applications_ocr(self):
        """Monitor applications using OCR for adult content"""
        try:
            # Take screenshot of current screen
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(gray).lower()
            
            if self._contains_adult_content(text):
                active_app = self._get_active_application()
                self._trigger_block_screen("Application", active_app, "Adult content detected via OCR")
                
        except Exception as e:
            print(f"OCR monitoring error: {e}")
            
    def _get_active_application(self):
        """Get the currently active application name"""
        try:
            if sys.platform == "win32":
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(hwnd)
            elif sys.platform == "darwin":
                script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                return subprocess.check_output(['osascript', '-e', script]).decode().strip()
            else:  # Linux
                result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
        except:
            return "Unknown Application"
            
    def _is_domain_blocked(self, domain):
        """Check if domain is in blocked list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blocked_domains WHERE domain = ?', (domain,))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result
        
    def _contains_adult_content(self, text):
        """Check if text contains adult content keywords"""
        if not text:
            return False
            
        text = text.lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT keyword FROM blocked_keywords')
        keywords = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for keyword in keywords:
            if keyword in text:
                return True
                
        return False
        
    def _trigger_block_screen(self, content_type, source, reason):
        """Trigger the block screen"""
        # Log the block
        self._log_block(content_type, source, reason)
        
        # Show block screen
        if not self.block_screen or not self.block_screen.isVisible():
            self.block_screen = BlockScreen(content_type, source, reason)
            self.block_screen.show()
            
    def _log_block(self, content_type, source, reason):
        """Log blocked content to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO block_logs (content_type, content_source, block_reason, app_name)
            VALUES (?, ?, ?, ?)
        ''', (content_type, source, reason, self._get_active_application()))
        conn.commit()
        conn.close()


class BlockScreen(QWidget):
    """Full-screen block screen with countdown timer"""
    
    def __init__(self, content_type, source, reason):
        super().__init__()
        self.content_type = content_type
        self.source = source
        self.reason = reason
        self.countdown_seconds = self._get_countdown_time()
        self.redirect_url = self._get_redirect_url()
        self.block_message = self._get_block_message()
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the block screen UI"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: white;
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ff4444;
                border-radius: 3px;
            }
        """)
        
        # Make fullscreen
        self.showFullScreen()
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Warning icon and title
        title_label = QLabel("🚫 CONTENT BLOCKED")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 36, QFont.Bold))
        title_label.setStyleSheet("color: #ff4444; margin: 20px;")
        layout.addWidget(title_label)
        
        # Block reason
        reason_label = QLabel(f"Reason: {self.reason}")
        reason_label.setAlignment(Qt.AlignCenter)
        reason_label.setFont(QFont("Arial", 18))
        reason_label.setStyleSheet("color: #ffaa44; margin: 10px;")
        layout.addWidget(reason_label)
        
        # Content type and source
        if self.source != "Unknown Application":
            source_label = QLabel(f"{self.content_type}: {self.source}")
            source_label.setAlignment(Qt.AlignCenter)
            source_label.setFont(QFont("Arial", 14))
            source_label.setStyleSheet("color: #aaaaaa; margin: 10px;")
            layout.addWidget(source_label)
        
        # Custom message
        if self.block_message:
            message_label = QLabel(self.block_message)
            message_label.setAlignment(Qt.AlignCenter)
            message_label.setFont(QFont("Arial", 16))
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: white; margin: 20px; max-width: 800px;")
            layout.addWidget(message_label)
        
        # Countdown timer
        self.countdown_label = QLabel(f"Redirecting in {self.countdown_seconds} seconds...")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont("Arial", 20))
        self.countdown_label.setStyleSheet("color: #ffaa44; margin: 20px;")
        layout.addWidget(self.countdown_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.countdown_seconds)
        self.progress_bar.setValue(self.countdown_seconds)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setFixedWidth(400)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # Close button (for testing purposes)
        close_btn = QPushButton("Close (Admin)")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                font-size: 12px;
                padding: 5px 10px;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
    def setup_timer(self):
        """Setup countdown timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every second
        
    def update_countdown(self):
        """Update countdown timer"""
        self.countdown_seconds -= 1
        self.progress_bar.setValue(self.countdown_seconds)
        
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Redirecting in {self.countdown_seconds} seconds...")
        else:
            self.countdown_label.setText("Redirecting now...")
            self.timer.stop()
            self.handle_redirect()
            
    def handle_redirect(self):
        """Handle redirect after countdown"""
        if self.content_type == "Website":
            # Redirect browser to safe URL
            self._redirect_browser()
        elif self.content_type == "Application":
            # Close the application
            self._close_application()
            
        self.close()
        
    def _redirect_browser(self):
        """Redirect browser to safe URL"""
        try:
            if self.redirect_url:
                # Open safe URL in default browser
                import webbrowser
                webbrowser.open(self.redirect_url)
        except Exception as e:
            print(f"Redirect error: {e}")
            
    def _close_application(self):
        """Close the blocked application"""
        try:
            # Get active application and close it
            active_app = self._get_active_application_process()
            if active_app:
                active_app.terminate()
        except Exception as e:
            print(f"App close error: {e}")
            
    def _get_active_application_process(self):
        """Get active application process"""
        try:
            # This is a simplified implementation
            # In practice, you'd need more sophisticated process detection
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'chrome' not in proc.info['name'].lower():
                    return proc
        except:
            pass
        return None
        
    def _get_countdown_time(self):
        """Get countdown time from settings"""
        # This should read from the UI spinBox value
        # For now, return default value
        return 10
        
    def _get_redirect_url(self):
        """Get redirect URL from settings"""
        # This should read from the UI lineEdit_2 value
        # For now, return default value
        return "https://google.com"
        
    def _get_block_message(self):
        """Get block message from settings"""
        # This should read from the UI plainTextEdit value
        # For now, return default message
        return "This content has been blocked to protect you from inappropriate material."
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Disable Alt+F4, Escape, etc.
        if event.key() == Qt.Key_Escape:
            return
        super().keyPressEvent(event)


# Global blocker instance
_blocker_instance = None

def get_blocker_instance():
    """Get or create the global blocker instance"""
    global _blocker_instance
    if _blocker_instance is None:
        _blocker_instance = AdultContentBlocker()
    return _blocker_instance

def start_content_blocking():
    """Start content blocking"""
    blocker = get_blocker_instance()
    blocker.start_monitoring()
    
def stop_content_blocking():
    """Stop content blocking"""
    blocker = get_blocker_instance()
    blocker.stop_monitoring()
    
def is_content_blocking_active():
    """Check if content blocking is active"""
    blocker = get_blocker_instance()
    return blocker.is_active

if __name__ == "__main__":
    # Test the block screen
    app = QApplication(sys.argv)
    block_screen = BlockScreen("Website", "example.com", "Adult content detected")
    block_screen.show()
    sys.exit(app.exec_())