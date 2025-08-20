"""
VPN-Resistant Adult Content Blocker
Enhanced version that works effectively even when VPN is active.
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
import hashlib
import json

# Optional OCR support
try:
    import pytesseract
    from PIL import ImageGrab, Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class VPNResistantContentBlocker:
    """Content blocker designed to work effectively with VPN connections"""
    
    def __init__(self, db_path="app_blocker.db"):
        self.db_path = db_path
        self.is_active = False
        self.block_screen = None
        self.monitoring_thread = None
        
        # VPN detection
        self.vpn_detected = False
        self.original_ip = None
        self.current_ip = None
        
        # Enhanced monitoring settings
        self.monitoring_interval = 1.5
        self.ocr_interval = 3.0
        self.content_analysis_interval = 2.0
        self.last_ocr_check = 0
        self.last_content_check = 0
        
        # VPN-resistant blocking strategies
        self.use_deep_content_analysis = True
        self.use_enhanced_ocr = True
        self.use_pattern_matching = True
        self.use_behavioral_analysis = True
        
        self.setup_database()
        self.load_comprehensive_keywords()
        self.detect_vpn_status()
        
        # Default settings
        self.default_countdown = 10
        self.default_redirect_url = "https://google.com"
        self.default_block_message = "This content has been blocked to protect you from inappropriate material."
        
    def detect_vpn_status(self):
        """Detect if VPN is currently active"""
        try:
            # Method 1: Check for VPN processes
            vpn_processes = ['openvpn', 'nordvpn', 'expressvpn', 'surfshark', 'cyberghost', 
                           'tunnelbear', 'windscribe', 'protonvpn', 'privatevpn']
            
            for proc in psutil.process_iter(['name']):
                if any(vpn in proc.info['name'].lower() for vpn in vpn_processes):
                    self.vpn_detected = True
                    print("🔒 VPN detected - Enhanced blocking mode activated")
                    return
                    
            # Method 2: Check network interfaces for VPN adapters
            import psutil
            for interface, addrs in psutil.net_if_addrs().items():
                interface_lower = interface.lower()
                if any(vpn_indicator in interface_lower for vpn_indicator in 
                      ['vpn', 'tun', 'tap', 'nord', 'express', 'proton']):
                    self.vpn_detected = True
                    print("🔒 VPN interface detected - Enhanced blocking mode activated")
                    return
                    
            # Method 3: IP change detection (basic)
            try:
                response = requests.get('https://api.ipify.org', timeout=5)
                self.current_ip = response.text.strip()
                
                # Store original IP for comparison
                if not self.original_ip:
                    self.original_ip = self.current_ip
                elif self.original_ip != self.current_ip:
                    self.vpn_detected = True
                    print("🔒 IP change detected - Possible VPN usage")
                    
            except:
                pass  # Don't fail if IP detection doesn't work
                
            if not self.vpn_detected:
                print("🌐 No VPN detected - Standard blocking mode")
                
        except Exception as e:
            print(f"VPN detection error: {e}")
            
    def setup_database(self):
        """Enhanced database setup with VPN-resistant features"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Standard tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_keywords (
                    id INTEGER PRIMARY KEY,
                    keyword TEXT UNIQUE,
                    category TEXT,
                    severity INTEGER,
                    pattern_type TEXT DEFAULT 'exact'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    id INTEGER PRIMARY KEY,
                    domain TEXT UNIQUE,
                    category TEXT,
                    severity INTEGER,
                    domain_hash TEXT
                )
            ''')
            
            # Enhanced tables for VPN resistance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern TEXT UNIQUE,
                    pattern_type TEXT,
                    category TEXT,
                    confidence REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS block_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content_type TEXT,
                    content_source TEXT,
                    block_reason TEXT,
                    app_name TEXT,
                    vpn_status TEXT,
                    detection_method TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Enhanced database initialized")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            
    def load_comprehensive_keywords(self):
        """Load comprehensive keywords optimized for VPN scenarios"""
        
        # Enhanced keyword categories
        keyword_categories = {
            'explicit_content': {
                'keywords': ['porn', 'xxx', 'sex', 'nude', 'naked', 'erotic', 'nsfw', 
                           'adult', 'mature', 'explicit', 'hardcore', 'softcore'],
                'severity': 5
            },
            'adult_services': {
                'keywords': ['escort', 'massage', 'webcam', 'cam girl', 'live cam', 
                           'strip', 'stripper', 'lingerie', 'hookup', 'dating'],
                'severity': 4
            },
            'adult_sites': {
                'keywords': ['pornhub', 'xvideos', 'youporn', 'xhamster', 'redtube',
                           'chaturbate', 'onlyfans', 'manyvids', 'clips4sale'],
                'severity': 5
            },
            'content_patterns': {
                'keywords': ['18+', '21+', 'adults only', 'mature content', 'nsfw content',
                           'explicit material', 'adult entertainment', 'for adults'],
                'severity': 4
            },
            'gambling': {
                'keywords': ['casino', 'poker', 'gambling', 'bet', 'betting', 'slots',
                           'jackpot', 'lottery', 'blackjack', 'roulette'],
                'severity': 3
            }
        }
        
        # Domain patterns (VPN-resistant)
        domain_patterns = [
            # Direct domains
            'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com', 'youporn.com',
            'xhamster.com', 'tube8.com', 'spankbang.com', 'chaturbate.com',
            'cam4.com', 'livejasmin.com', 'stripchat.com', 'onlyfans.com',
            
            # Pattern-based detection (works even with VPN domain masking)
            '*.porn.*', '*.sex.*', '*.xxx.*', '*.adult.*', '*.nude.*',
            '*.cam.*', '*.live.*', '*.strip.*', '*.escort.*'
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert keywords with categories
            for category, data in keyword_categories.items():
                for keyword in data['keywords']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO blocked_keywords 
                        (keyword, category, severity, pattern_type)
                        VALUES (?, ?, ?, 'enhanced')
                    ''', (keyword, category, data['severity']))
                    
            # Insert domain patterns
            for domain in domain_patterns:
                domain_hash = hashlib.md5(domain.encode()).hexdigest()
                cursor.execute('''
                    INSERT OR IGNORE INTO blocked_domains 
                    (domain, category, severity, domain_hash)
                    VALUES (?, 'adult', 4, ?)
                ''', (domain, domain_hash))
                
            # Insert content patterns for deep analysis
            content_patterns = [
                ('adult.*content', 'regex', 'adult', 0.8),
                ('explicit.*material', 'regex', 'adult', 0.9),
                ('18\\+.*only', 'regex', 'adult', 0.7),
                ('mature.*audience', 'regex', 'adult', 0.6),
                ('nsfw.*warning', 'regex', 'adult', 0.8)
            ]
            
            for pattern, pattern_type, category, confidence in content_patterns:
                cursor.execute('''
                    INSERT OR IGNORE INTO content_patterns 
                    (pattern, pattern_type, category, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (pattern, pattern_type, category, confidence))
                
            conn.commit()
            conn.close()
            print("✅ Comprehensive keyword database loaded")
            
        except Exception as e:
            print(f"❌ Error loading keywords: {e}")
            
    def start_monitoring(self):
        """Start VPN-resistant monitoring"""
        if not self.is_active:
            self.is_active = True
            self.monitoring_thread = threading.Thread(target=self._enhanced_monitor_content, daemon=True)
            self.monitoring_thread.start()
            
            if self.vpn_detected:
                print("🔒 VPN-resistant monitoring started")
            else:
                print("✅ Standard monitoring started")
                
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("❌ Monitoring stopped")
        
    def _enhanced_monitor_content(self):
        """Enhanced monitoring loop optimized for VPN scenarios"""
        while self.is_active:
            try:
                current_time = time.time()
                
                # Always monitor applications via OCR (VPN-proof)
                if OCR_AVAILABLE and (current_time - self.last_ocr_check) > self.ocr_interval:
                    self._enhanced_ocr_monitoring()
                    self.last_ocr_check = current_time
                
                # Enhanced content analysis (works with VPN)
                if (current_time - self.last_content_check) > self.content_analysis_interval:
                    self._deep_content_analysis()
                    self.last_content_check = current_time
                
                # Browser process monitoring (VPN-resistant)
                self._enhanced_browser_monitoring()
                
                # VPN status check (periodic)
                if int(current_time) % 30 == 0:  # Every 30 seconds
                    self.detect_vpn_status()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Enhanced monitoring error: {e}")
                time.sleep(3)
                
    def _enhanced_ocr_monitoring(self):
        """Enhanced OCR monitoring (100% VPN-proof)"""
        if not OCR_AVAILABLE:
            return
            
        try:
            # Take strategic screenshots
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            
            # Enhanced preprocessing for better OCR
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # Apply image enhancement
            enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
            
            # Extract text with multiple methods
            text_methods = []
            
            # Method 1: Standard OCR
            try:
                text1 = pytesseract.image_to_string(enhanced, timeout=3).lower()
                text_methods.append(text1)
            except:
                pass
                
            # Method 2: OCR with different config
            try:
                custom_config = r'--oem 3 --psm 6'
                text2 = pytesseract.image_to_string(enhanced, config=custom_config, timeout=3).lower()
                text_methods.append(text2)
            except:
                pass
            
            # Analyze all extracted text
            for text in text_methods:
                if self._enhanced_content_analysis(text):
                    active_app = self._get_active_application()
                    self._trigger_enhanced_block_screen("Application", active_app, 
                                                      "Adult content detected via OCR", "ocr")
                    return
                    
        except Exception as e:
            pass  # Silent fail for OCR errors
            
    def _deep_content_analysis(self):
        """Deep content analysis that works regardless of VPN"""
        try:
            # Analyze clipboard content (if accessible)
            try:
                from PyQt5.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard_text = clipboard.text().lower()
                
                if clipboard_text and self._enhanced_content_analysis(clipboard_text):
                    self._trigger_enhanced_block_screen("Clipboard", "System Clipboard", 
                                                      "Adult content in clipboard", "clipboard")
                    return
            except:
                pass
                
            # Analyze recent browser history (if accessible)
            self._analyze_browser_history()
            
        except Exception as e:
            pass
            
    def _analyze_browser_history(self):
        """Analyze browser history for adult content (VPN-resistant)"""
        try:
            # Chrome history analysis
            chrome_history_paths = [
                os.path.expanduser("~/.config/google-chrome/Default/History"),  # Linux
                os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History"),  # macOS
                os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/History")  # Windows
            ]
            
            for history_path in chrome_history_paths:
                if os.path.exists(history_path):
                    # Copy to temporary file to avoid lock issues
                    import shutil
                    temp_path = history_path + "_temp"
                    try:
                        shutil.copy2(history_path, temp_path)
                        
                        conn = sqlite3.connect(temp_path)
                        cursor = conn.cursor()
                        
                        # Get recent URLs
                        cursor.execute('''
                            SELECT url, title FROM urls 
                            ORDER BY last_visit_time DESC 
                            LIMIT 10
                        ''')
                        
                        recent_urls = cursor.fetchall()
                        conn.close()
                        
                        # Analyze URLs and titles
                        for url, title in recent_urls:
                            if self._enhanced_url_analysis(url, title):
                                self._trigger_enhanced_block_screen("Browser History", url, 
                                                                  "Adult content in browser history", "history")
                                return
                                
                        os.remove(temp_path)
                        
                    except:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
        except Exception as e:
            pass
            
    def _enhanced_browser_monitoring(self):
        """Enhanced browser monitoring that works with VPN"""
        try:
            # Monitor browser processes and windows
            browser_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                proc_name = proc.info['name'].lower()
                if any(browser in proc_name for browser in 
                      ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
                    browser_processes.append(proc)
                    
            # Analyze command line arguments for URLs
            for proc in browser_processes:
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                    if self._enhanced_content_analysis(cmdline):
                        self._trigger_enhanced_block_screen("Browser Process", 
                                                          proc.info['name'], 
                                                          "Adult content in browser command line", 
                                                          "process")
                        return
                except:
                    continue
                    
        except Exception as e:
            pass
            
    def _enhanced_url_analysis(self, url, title=""):
        """Enhanced URL analysis that works with VPN obfuscation"""
        try:
            # Method 1: Direct domain check
            domain = urlparse(url).netloc.lower()
            if self._is_domain_blocked_enhanced(domain):
                return True
                
            # Method 2: URL pattern analysis
            full_url = url.lower()
            if self._enhanced_content_analysis(full_url):
                return True
                
            # Method 3: Title analysis
            if title and self._enhanced_content_analysis(title.lower()):
                return True
                
            # Method 4: URL structure analysis
            suspicious_patterns = [
                r'adult.*content', r'18.*plus', r'xxx.*', r'porn.*',
                r'nude.*', r'sex.*', r'cam.*girl', r'live.*cam'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, full_url):
                    return True
                    
            return False
            
        except Exception as e:
            return False
            
    def _is_domain_blocked_enhanced(self, domain):
        """Enhanced domain blocking that works with VPN"""
        try:
            # Direct domain check
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check exact match
            cursor.execute('SELECT COUNT(*) FROM blocked_domains WHERE domain = ?', (domain,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return True
                
            # Check pattern matches
            cursor.execute('SELECT domain FROM blocked_domains WHERE domain LIKE ?', ('%.%',))
            patterns = cursor.fetchall()
            
            for (pattern,) in patterns:
                if '*' in pattern:
                    # Convert wildcard pattern to regex
                    regex_pattern = pattern.replace('*', '.*')
                    if re.match(regex_pattern, domain):
                        conn.close()
                        return True
                        
            # Check domain hash (for obfuscated domains)
            domain_hash = hashlib.md5(domain.encode()).hexdigest()
            cursor.execute('SELECT COUNT(*) FROM blocked_domains WHERE domain_hash = ?', (domain_hash,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return True
                
            conn.close()
            return False
            
        except:
            return False
            
    def _enhanced_content_analysis(self, text):
        """Enhanced content analysis optimized for VPN scenarios"""
        if not text:
            return False
            
        text = text.lower().strip()
        
        # Quick bail-out for very short text
        if len(text) < 3:
            return False
            
        try:
            # Method 1: Enhanced keyword matching
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get high-severity keywords first
            cursor.execute('SELECT keyword FROM blocked_keywords WHERE severity >= 4')
            high_severity_keywords = [row[0] for row in cursor.fetchall()]
            
            for keyword in high_severity_keywords:
                if keyword in text:
                    conn.close()
                    return True
                    
            # Method 2: Pattern matching
            cursor.execute('SELECT pattern, confidence FROM content_patterns WHERE pattern_type = "regex"')
            patterns = cursor.fetchall()
            
            for pattern, confidence in patterns:
                if re.search(pattern, text):
                    if confidence >= 0.7:  # High confidence threshold
                        conn.close()
                        return True
                        
            # Method 3: Combined keyword analysis
            adult_indicators = 0
            cursor.execute('SELECT keyword FROM blocked_keywords')
            all_keywords = [row[0] for row in cursor.fetchall()]
            
            for keyword in all_keywords:
                if keyword in text:
                    adult_indicators += 1
                    
            conn.close()
            
            # Multiple indicators suggest adult content
            if adult_indicators >= 2:
                return True
                
            # Method 4: Context analysis
            adult_contexts = [
                'adults only', 'mature content', 'explicit material',
                '18+ content', 'nsfw warning', 'adult entertainment'
            ]
            
            for context in adult_contexts:
                if context in text:
                    return True
                    
            return False
            
        except Exception as e:
            # Fallback to basic keyword check
            basic_keywords = ['porn', 'xxx', 'nude', 'sex', 'adult', 'nsfw']
            return any(keyword in text for keyword in basic_keywords)
            
    def _trigger_enhanced_block_screen(self, content_type, source, reason, detection_method):
        """Trigger enhanced block screen with VPN information"""
        # Enhanced logging
        self._log_enhanced_block(content_type, source, reason, detection_method)
        
        # Show block screen
        if not self.block_screen or not self.block_screen.isVisible():
            self.block_screen = VPNResistantBlockScreen(content_type, source, reason, self)
            self.block_screen.show()
            
    def _log_enhanced_block(self, content_type, source, reason, detection_method):
        """Enhanced logging with VPN status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            vpn_status = "VPN_DETECTED" if self.vpn_detected else "NO_VPN"
            
            cursor.execute('''
                INSERT INTO block_logs 
                (content_type, content_source, block_reason, app_name, vpn_status, detection_method)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (content_type, source, reason, self._get_active_application(), 
                  vpn_status, detection_method))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Logging error: {e}")
            
    def _get_active_application(self):
        """Get active application (VPN-proof)"""
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


class VPNResistantBlockScreen(QWidget):
    """Enhanced block screen with VPN awareness"""
    
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
        """Setup enhanced block screen UI"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QProgressBar {
                border: 2px solid #21262d;
                border-radius: 6px;
                text-align: center;
                background-color: #161b22;
            }
            QProgressBar::chunk {
                background-color: #da3633;
                border-radius: 4px;
            }
        """)
        
        self.showFullScreen()
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)
        
        # Enhanced title with VPN indicator
        title_text = "🛡️ CONTENT BLOCKED"
        if self.blocker.vpn_detected:
            title_text += " (VPN DETECTED)"
            
        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title_label.setStyleSheet("color: #f85149; margin: 20px;")
        layout.addWidget(title_label)
        
        # VPN warning (if detected)
        if self.blocker.vpn_detected:
            vpn_warning = QLabel("⚠️ VPN connection detected - Enhanced blocking active")
            vpn_warning.setAlignment(Qt.AlignCenter)
            vpn_warning.setFont(QFont("Segoe UI", 14))
            vpn_warning.setStyleSheet("color: #f79000; margin: 10px;")
            layout.addWidget(vpn_warning)
        
        # Block reason
        reason_label = QLabel(f"Reason: {self.reason}")
        reason_label.setAlignment(Qt.AlignCenter)
        reason_label.setFont(QFont("Segoe UI", 16))
        reason_label.setStyleSheet("color: #ffa657; margin: 10px;")
        layout.addWidget(reason_label)
        
        # Content source
        if self.source and self.source != "Unknown Application":
            source_label = QLabel(f"{self.content_type}: {self.source}")
            source_label.setAlignment(Qt.AlignCenter)
            source_label.setFont(QFont("Segoe UI", 12))
            source_label.setStyleSheet("color: #8b949e; margin: 10px;")
            layout.addWidget(source_label)
        
        # Enhanced message
        message_text = self.blocker.default_block_message
        if self.blocker.vpn_detected:
            message_text += "\n\nNote: VPN usage detected. This blocking system works regardless of VPN status."
            
        message_label = QLabel(message_text)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont("Segoe UI", 14))
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #c9d1d9; margin: 20px; max-width: 700px;")
        layout.addWidget(message_label)
        
        # Countdown
        self.countdown_label = QLabel(f"Redirecting in {self.countdown_seconds} seconds...")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.countdown_label.setStyleSheet("color: #ffa657; margin: 15px;")
        layout.addWidget(self.countdown_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.countdown_seconds)
        self.progress_bar.setValue(self.countdown_seconds)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setFixedWidth(400)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
    def setup_timer(self):
        """Setup timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        
    def update_countdown(self):
        """Update countdown"""
        self.countdown_seconds -= 1
        self.progress_bar.setValue(self.countdown_seconds)
        
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Redirecting in {self.countdown_seconds} seconds...")
        else:
            self.countdown_label.setText("Redirecting now...")
            self.timer.stop()
            self.handle_redirect()
            
    def handle_redirect(self):
        """Handle redirect"""
        try:
            if self.content_type == "Website":
                import webbrowser
                webbrowser.open(self.blocker.default_redirect_url)
        except Exception as e:
            print(f"Redirect error: {e}")
            
        self.close()


# Global VPN-resistant blocker instance
_vpn_resistant_blocker_instance = None

def get_vpn_resistant_blocker_instance():
    """Get VPN-resistant blocker instance"""
    global _vpn_resistant_blocker_instance
    if _vpn_resistant_blocker_instance is None:
        _vpn_resistant_blocker_instance = VPNResistantContentBlocker()
    return _vpn_resistant_blocker_instance

def start_vpn_resistant_blocking():
    """Start VPN-resistant blocking"""
    blocker = get_vpn_resistant_blocker_instance()
    blocker.start_monitoring()
    
def stop_vpn_resistant_blocking():
    """Stop VPN-resistant blocking"""
    blocker = get_vpn_resistant_blocker_instance()
    blocker.stop_monitoring()

if __name__ == "__main__":
    # Test VPN-resistant blocker
    blocker = get_vpn_resistant_blocker_instance()
    print(f"VPN Status: {'Detected' if blocker.vpn_detected else 'Not detected'}")
    start_vpn_resistant_blocking()
    time.sleep(10)
    stop_vpn_resistant_blocking()