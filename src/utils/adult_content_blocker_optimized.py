"""
Optimized Adult Content Blocker - Lightweight version with better performance
Focuses on essential features without heavy dependencies that cause lag.
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
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QApplication, QDesktopWidget, QProgressBar)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import subprocess

# Optional OCR support (only import if available)
try:
    import pytesseract
    from PIL import ImageGrab, Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  OCR dependencies not available. Application monitoring will be limited.")


class OptimizedAdultContentBlocker:
    """Optimized adult content blocking system with better performance"""
    
    def __init__(self, db_path="app_blocker.db"):
        self.db_path = db_path
        self.is_active = False
        self.block_screen = None
        self.monitoring_thread = None
        self.setup_database()
        self.load_adult_keywords()
        
        # Performance settings
        self.monitoring_interval = 2.0  # Check every 2 seconds instead of 1
        self.ocr_interval = 5.0  # OCR check every 5 seconds
        self.last_ocr_check = 0
        
        # Browser monitoring (simplified)
        self.browser_processes = ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']
        
        # Default settings
        self.default_countdown = 10
        self.default_redirect_url = "https://google.com"
        self.default_block_message = "This content has been blocked to protect you from inappropriate material."
        
    def setup_database(self):
        """Initialize the blocking database"""
        try:
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
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
        
    def load_adult_keywords(self):
        """Load essential adult content keywords (optimized list)"""
        # Focused keyword list for better performance
        adult_keywords = [
            # Core explicit terms
            'porn', 'xxx', 'sex', 'adult', 'nude', 'naked', 'erotic', 'nsfw',
            'webcam', 'escort', 'massage', 'dating', 'hookup', 'fetish',
            'strip', 'lingerie', 
            
            # Major adult sites
            'pornhub', 'xvideos', 'youporn', 'xhamster', 'redtube',
            'chaturbate', 'onlyfans',
            
            # Gambling
            'casino', 'poker', 'gambling', 'bet',
            
            # Violence (basic)
            'violence', 'gore', 'murder'
        ]
        
        adult_domains = [
            'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com', 'youporn.com',
            'xhamster.com', 'chaturbate.com', 'onlyfans.com'
        ]
        
        try:
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
            print("✅ Keywords and domains loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading keywords: {e}")
        
    def start_monitoring(self):
        """Start the content monitoring system"""
        if not self.is_active:
            self.is_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_content, daemon=True)
            self.monitoring_thread.start()
            print("✅ Content monitoring started")
            
    def stop_monitoring(self):
        """Stop the content monitoring system"""
        self.is_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("❌ Content monitoring stopped")
        
    def _monitor_content(self):
        """Main monitoring loop (optimized)"""
        while self.is_active:
            try:
                # Basic browser process monitoring
                self._monitor_browser_processes()
                
                # OCR monitoring (less frequent)
                current_time = time.time()
                if OCR_AVAILABLE and (current_time - self.last_ocr_check) > self.ocr_interval:
                    self._monitor_applications_ocr_light()
                    self.last_ocr_check = current_time
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
                
    def _monitor_browser_processes(self):
        """Lightweight browser monitoring"""
        try:
            # Check if browsers are running
            browser_running = False
            for proc in psutil.process_iter(['name']):
                if any(browser in proc.info['name'].lower() for browser in self.browser_processes):
                    browser_running = True
                    break
                    
            # For demo purposes, simulate content detection
            # In a real implementation, you'd integrate with browser APIs or extensions
            if browser_running:
                # This is where you'd implement actual browser content checking
                # For now, we'll skip the heavy Selenium implementation
                pass
                
        except Exception as e:
            print(f"Browser monitoring error: {e}")
            
    def _monitor_applications_ocr_light(self):
        """Lightweight OCR monitoring"""
        if not OCR_AVAILABLE:
            return
            
        try:
            # Take a smaller screenshot for better performance
            screenshot = ImageGrab.grab(bbox=(0, 0, 800, 600))  # Smaller area
            screenshot_np = np.array(screenshot)
            
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # Extract text using OCR (with timeout)
            text = pytesseract.image_to_string(gray, timeout=3).lower()
            
            if self._contains_adult_content(text):
                active_app = self._get_active_application()
                self._trigger_block_screen("Application", active_app, "Adult content detected via OCR")
                
        except Exception as e:
            # Don't spam errors for OCR issues
            pass
            
    def _get_active_application(self):
        """Get the currently active application name"""
        try:
            if sys.platform == "win32":
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    return win32gui.GetWindowText(hwnd)
                except ImportError:
                    return "Windows Application"
            elif sys.platform == "darwin":
                try:
                    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                    result = subprocess.check_output(['osascript', '-e', script], timeout=2)
                    return result.decode().strip()
                except:
                    return "macOS Application"
            else:  # Linux
                try:
                    result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                          capture_output=True, text=True, timeout=2)
                    return result.stdout.strip()
                except:
                    return "Linux Application"
        except:
            return "Unknown Application"
            
    def _is_domain_blocked(self, domain):
        """Check if domain is in blocked list"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM blocked_domains WHERE domain = ?', (domain,))
            result = cursor.fetchone()[0] > 0
            conn.close()
            return result
        except:
            return False
        
    def _contains_adult_content(self, text):
        """Check if text contains adult content keywords (optimized)"""
        if not text:
            return False
            
        text = text.lower()
        
        # Quick check against common terms first
        quick_terms = ['porn', 'xxx', 'nude', 'sex', 'adult', 'nsfw']
        for term in quick_terms:
            if term in text:
                return True
                
        # Full database check only if quick check fails
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT keyword FROM blocked_keywords WHERE severity >= 3')
            keywords = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for keyword in keywords:
                if keyword in text:
                    return True
                    
        except:
            pass
            
        return False
        
    def _trigger_block_screen(self, content_type, source, reason):
        """Trigger the block screen"""
        # Log the block
        self._log_block(content_type, source, reason)
        
        # Show block screen (only if not already showing)
        if not self.block_screen or not self.block_screen.isVisible():
            self.block_screen = OptimizedBlockScreen(content_type, source, reason, self)
            self.block_screen.show()
            
    def _log_block(self, content_type, source, reason):
        """Log blocked content to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO block_logs (content_type, content_source, block_reason, app_name)
                VALUES (?, ?, ?, ?)
            ''', (content_type, source, reason, self._get_active_application()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Logging error: {e}")
            
    def analyze_url_simple(self, url):
        """Simple URL analysis without heavy dependencies"""
        try:
            # Check domain first
            domain = urlparse(url).netloc.lower()
            if self._is_domain_blocked(domain):
                return True
                
            # Simple keyword check in URL
            if self._contains_adult_content(url):
                return True
                
            # Optional: Fetch page title only (lightweight)
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; ContentBlocker/1.0)'
                })
                if response.status_code == 200:
                    # Extract just the title for quick analysis
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        title = title_match.group(1).strip()
                        if self._contains_adult_content(title):
                            return True
            except:
                pass  # Don't block on network errors
                
            return False
            
        except Exception as e:
            print(f"URL analysis error: {e}")
            return False


class OptimizedBlockScreen(QWidget):
    """Optimized block screen with better performance"""
    
    def __init__(self, content_type, source, reason, blocker_instance):
        super().__init__()
        self.content_type = content_type
        self.source = source
        self.reason = reason
        self.blocker = blocker_instance
        self.countdown_seconds = self.blocker.default_countdown
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the optimized block screen UI"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
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
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 4px;
                text-align: center;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #ff4444;
                border-radius: 2px;
            }
        """)
        
        # Make fullscreen
        self.showFullScreen()
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Warning icon and title
        title_label = QLabel("🚫 CONTENT BLOCKED")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 32, QFont.Bold))
        title_label.setStyleSheet("color: #ff4444; margin: 20px;")
        layout.addWidget(title_label)
        
        # Block reason
        reason_label = QLabel(f"Reason: {self.reason}")
        reason_label.setAlignment(Qt.AlignCenter)
        reason_label.setFont(QFont("Arial", 16))
        reason_label.setStyleSheet("color: #ffaa44; margin: 10px;")
        layout.addWidget(reason_label)
        
        # Content source
        if self.source and self.source != "Unknown Application":
            source_label = QLabel(f"{self.content_type}: {self.source}")
            source_label.setAlignment(Qt.AlignCenter)
            source_label.setFont(QFont("Arial", 12))
            source_label.setStyleSheet("color: #aaaaaa; margin: 10px;")
            layout.addWidget(source_label)
        
        # Custom message
        message_label = QLabel(self.blocker.default_block_message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont("Arial", 14))
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: white; margin: 20px; max-width: 600px;")
        layout.addWidget(message_label)
        
        # Countdown timer
        self.countdown_label = QLabel(f"Redirecting in {self.countdown_seconds} seconds...")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont("Arial", 18))
        self.countdown_label.setStyleSheet("color: #ffaa44; margin: 15px;")
        layout.addWidget(self.countdown_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.countdown_seconds)
        self.progress_bar.setValue(self.countdown_seconds)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setFixedWidth(300)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # Close button (smaller, less prominent)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                font-size: 10px;
                padding: 4px 8px;
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
        try:
            if self.content_type == "Website":
                # Open safe URL
                import webbrowser
                webbrowser.open(self.blocker.default_redirect_url)
            elif self.content_type == "Application":
                # Could implement app closing here
                pass
        except Exception as e:
            print(f"Redirect error: {e}")
            
        self.close()
        
    def keyPressEvent(self, event):
        """Handle key press events (limited bypass prevention)"""
        # Allow closing with Escape for testing
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# Global optimized blocker instance
_optimized_blocker_instance = None

def get_optimized_blocker_instance():
    """Get or create the global optimized blocker instance"""
    global _optimized_blocker_instance
    if _optimized_blocker_instance is None:
        _optimized_blocker_instance = OptimizedAdultContentBlocker()
    return _optimized_blocker_instance

def start_optimized_content_blocking():
    """Start optimized content blocking"""
    blocker = get_optimized_blocker_instance()
    blocker.start_monitoring()
    
def stop_optimized_content_blocking():
    """Stop optimized content blocking"""
    blocker = get_optimized_blocker_instance()
    blocker.stop_monitoring()
    
def is_optimized_content_blocking_active():
    """Check if optimized content blocking is active"""
    blocker = get_optimized_blocker_instance()
    return blocker.is_active

if __name__ == "__main__":
    # Test the optimized block screen
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    blocker = get_optimized_blocker_instance()
    block_screen = OptimizedBlockScreen("Website", "test-site.com", "Adult content detected (TEST)", blocker)
    block_screen.show()
    sys.exit(app.exec_())