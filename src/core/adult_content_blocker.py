import sys
import os
import re
import time
import threading
import sqlite3
from typing import List, Dict, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QDialog, QLabel, QPushButton, 
                           QTextBrowser, QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont
import psutil
import win32gui
import win32process
import win32api

class ContentAnalyzer(QObject):
    """Analyzes web content for adult material"""
    
    def __init__(self):
        super().__init__()
        # Extended list of adult content keywords
        self.adult_keywords = [
            'porn', 'sex', 'adult', 'nude', 'naked', 'xxx', 'erotic', 'nsfw',
            'mature', 'explicit', 'sensual', 'seductive', 'intimate', 'sensuous',
            'provocative', 'sultry', 'steamy', 'risque', 'racy', 'suggestive',
            'bikini', 'lingerie', 'underwear', 'bra', 'panties', 'thong',
            'escort', 'dating', 'hookup', 'casual', 'affair', 'romance',
            'lesbian', 'gay', 'bisexual', 'transgender', 'fetish', 'kink',
            'webcam', 'cam girl', 'live show', 'strip', 'tease', 'dance',
            'massage', 'therapy', 'spa', 'relax', 'pleasure', 'satisfaction',
            'xvideos', 'pornhub', 'youporn', 'redtube', 'xhamster',
            # Arabic keywords
            'جنس', 'اباحي', 'عاري',
        ]
        
        # Adult domains/sites
        self.adult_domains = [
            'pornhub.com', 'xvideos.com', 'redtube.com', 'youporn.com',
            'xhamster.com', 'tube8.com', 'beeg.com', 'spankbang.com',
            'tnaflix.com', 'drtuber.com', 'porn.com', 'sex.com',
            'brazzers.com','bangbros.com','xnxx.com',
        ]
    
    def analyze_url(self, url: str) -> Dict[str, any]:
        """Analyze URL for adult content"""
        result = {
            'is_blocked': False,
            'reason': '',
            'score': 0,
            'detected_keywords': []
        }
        
        try:
            # Check domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            for adult_domain in self.adult_domains:
                if adult_domain in domain:
                    result['is_blocked'] = True
                    result['reason'] = f'Blocked domain: {adult_domain}'
                    result['score'] = 100
                    return result
            
            # Analyze URL path and query
            full_url = url.lower()
            detected = []
            
            for keyword in self.adult_keywords:
                if keyword in full_url:
                    detected.append(keyword)
                    result['score'] += 10
            
            if detected:
                result['detected_keywords'] = detected
                if result['score'] >= 30:  # Threshold for blocking
                    result['is_blocked'] = True
                    result['reason'] = f'Adult keywords detected: {", ".join(detected[:3])}'
            
        except Exception as e:
            print(f"Error analyzing URL: {e}")
        
        return result
    
    def analyze_html_content(self, html_content: str, url: str = "") -> Dict[str, any]:
        """Analyze HTML content for adult material"""
        result = {
            'is_blocked': False,
            'reason': '',
            'score': 0,
            'detected_keywords': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Analyze different parts of the webpage
            elements_to_check = {
                'title': soup.find('title'),
                'meta_description': soup.find('meta', attrs={'name': 'description'}),
                'meta_keywords': soup.find('meta', attrs={'name': 'keywords'}),
                'h1_tags': soup.find_all('h1'),
                'h2_tags': soup.find_all('h2'),
                'img_alt': soup.find_all('img', alt=True),
                'links': soup.find_all('a', href=True)
            }
            
            detected_keywords = []
            
            for element_type, elements in elements_to_check.items():
                if not elements:
                    continue
                    
                if isinstance(elements, list):
                    for element in elements:
                        text = self._extract_text(element, element_type)
                        keywords = self._find_adult_keywords(text)
                        detected_keywords.extend(keywords)
                else:
                    text = self._extract_text(elements, element_type)
                    keywords = self._find_adult_keywords(text)
                    detected_keywords.extend(keywords)
            
            # Remove duplicates and calculate score
            unique_keywords = list(set(detected_keywords))
            result['detected_keywords'] = unique_keywords
            result['score'] = len(unique_keywords) * 15
            
            # Determine if content should be blocked
            if result['score'] >= 30:
                result['is_blocked'] = True
                result['reason'] = f'Adult content detected: {", ".join(unique_keywords[:3])}'
            
        except Exception as e:
            print(f"Error analyzing HTML content: {e}")
        
        return result
    
    def _extract_text(self, element, element_type: str) -> str:
        """Extract text from HTML elements"""
        try:
            if element_type == 'meta_description':
                return element.get('content', '') if element else ''
            elif element_type == 'meta_keywords':
                return element.get('content', '') if element else ''
            elif element_type == 'img_alt':
                return element.get('alt', '') if element else ''
            elif element_type == 'links':
                return element.get('href', '') + ' ' + element.get_text() if element else ''
            else:
                return element.get_text() if element else ''
        except:
            return ''
    
    def _find_adult_keywords(self, text: str) -> List[str]:
        """Find adult keywords in text"""
        if not text:
            return []
            
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.adult_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords

class BlockScreen(QDialog):
    """Full-screen blocking dialog"""
    
    def __init__(self, message: str, reason: str, countdown_seconds: int, redirect_url: str):
        super().__init__()
        self.countdown_seconds = countdown_seconds
        self.redirect_url = redirect_url
        self.reason = reason
        self.timer = None
        
        # Ensure we're on the main thread
        if QApplication.instance().thread() == QThread.currentThread():
            self.init_ui(message)
            self.setup_timer()
        else:
            # Move to main thread if needed
            self.moveToThread(QApplication.instance().thread())
            QMetaObject.invokeMethod(self, "init_ui", 
                                   Qt.QueuedConnection,
                                   Q_ARG(str, message))
            QMetaObject.invokeMethod(self, "setup_timer",
                                   Qt.QueuedConnection)
    def init_ui(self, message: str):
        """Initialize the blocking UI"""
        # Set window properties
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setModal(True)
        self.showFullScreen()
        
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("BlockerHero")
        title_font = QFont("Arial", 32, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Message browser
        self.msg_browser = QTextBrowser()
        self.msg_browser.setHtml(message)
        self.msg_browser.setMaximumHeight(200)
        self.msg_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
            }
        """)
        
        # Why blocked button
        self.toggle_btn = QPushButton("Why Blocked?!")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_reason)
        
        # Reason label (initially hidden)
        self.reason_label = QLabel(self.reason)
        self.reason_label.setAlignment(Qt.AlignCenter)
        self.reason_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 14px;
                margin: 10px;
                padding: 10px;
                background-color: #fadbd8;
                border-radius: 5px;
            }
        """)
        self.reason_label.hide()
        self.reason_visible = False
        
        # Close button with countdown
        self.close_btn = QPushButton(f"Close ({self.countdown_seconds})")
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet("""
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:enabled {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:enabled:hover {
                background-color: #229954;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.msg_browser)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.reason_label)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        
        # Set background color
        self.setStyleSheet("QDialog { background-color: #f8f9fa; }")
        
    def setup_timer(self):
        """Setup countdown timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every second
        
    def update_countdown(self):
        """Update countdown and enable close button when done"""
        self.countdown_seconds -= 1
        self.close_btn.setText(f"Close ({self.countdown_seconds})")
        
        if self.countdown_seconds <= 0:
            self.timer.stop()
            self.close_btn.setText("Close")
            self.close_btn.setEnabled(True)
            # Redirect to specified URL if provided
            if self.redirect_url:
                self.redirect_page()
    
    def toggle_reason(self):
        """Toggle visibility of blocking reason"""
        if self.reason_visible:
            self.reason_label.hide()
        else:
            self.reason_label.show()
        self.reason_visible = not self.reason_visible
    
    def redirect_page(self):
        """Redirect to specified URL (placeholder)"""
        # In a real implementation, this would interact with the browser
        print(f"Redirecting to: {self.redirect_url}")
    
    def keyPressEvent(self, event):
        """Override key press to prevent closing with Escape"""
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Override close event to prevent closing before countdown"""
        if self.countdown_seconds > 0:
            event.ignore()
        else:
            event.accept()

class BrowserMonitor(QThread):
    """Monitor browser activity for adult content"""
    
    content_blocked = pyqtSignal(str, str, str)  # url, reason, detected_content
    monitoring_stopped = pyqtSignal()  # Signal to indicate monitoring has stopped
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.content_analyzer = ContentAnalyzer()
        self.is_monitoring = False
        self.last_urls = {}  # Track last URLs for each browser
        self._stop_event = threading.Event()
        
    def run(self):
        """Main monitoring loop"""
        self.is_monitoring = True
        self._stop_event.clear()
        
        while not self._stop_event.is_set():
            try:
                # Check if adult content blocking is enabled
                if not self.settings_manager.is_adult_content_blocking_enabled():
                    if self._stop_event.wait(2):  # Wait with timeout
                        break
                    continue
                
                # Get active browser windows
                browser_windows = self.get_browser_windows()
                
                for window_info in browser_windows:
                    if self._stop_event.is_set():
                        break
                    self.check_browser_content(window_info)
                
                if self._stop_event.wait(1):  # Wait with timeout
                    break
                
            except Exception as e:
                print(f"Error in browser monitoring: {e}")
                if self._stop_event.wait(2):  # Wait with timeout
                    break
        
        self.is_monitoring = False
        self.monitoring_stopped.emit()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self._stop_event.set()
        self.wait()  # Wait for the thread to finish
    
    def get_browser_windows(self) -> List[Dict]:
        """Get information about active browser windows"""
        browser_processes = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe']
        browser_windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name().lower()
                        
                        if any(browser in process_name for browser in browser_processes):
                            windows.append({
                                'hwnd': hwnd,
                                'title': window_title,
                                'process_name': process_name,
                                'pid': pid
                            })
                    except:
                        pass
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
    
    def check_browser_content(self, window_info: Dict):
        """Check browser content for adult material"""
        try:
            # Extract URL from window title (simplified approach)
            title = window_info['title']
            url = self.extract_url_from_title(title)
            
            if not url:
                return
            
            # Skip if we already checked this URL recently
            process_id = window_info['pid']
            if process_id in self.last_urls and self.last_urls[process_id] == url:
                return
            
            self.last_urls[process_id] = url
            
            # Analyze URL
            url_analysis = self.content_analyzer.analyze_url(url)
            
            if url_analysis['is_blocked']:
                self.content_blocked.emit(url, url_analysis['reason'], 
                                        ', '.join(url_analysis['detected_keywords']))
                return
            
            # Try to get page content (simplified - in practice, this would require browser integration)
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    content_analysis = self.content_analyzer.analyze_html_content(response.text, url)
                    
                    if content_analysis['is_blocked']:
                        self.content_blocked.emit(url, content_analysis['reason'],
                                                ', '.join(content_analysis['detected_keywords']))
                        
            except requests.RequestException:
                pass  # Ignore network errors
                
        except Exception as e:
            print(f"Error checking browser content: {e}")
    
    def extract_url_from_title(self, title: str) -> Optional[str]:
        """Extract URL from browser window title (simplified)"""
        # This is a simplified approach - in practice, you'd need browser-specific APIs
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, title)
        return match.group(0) if match else None

class SettingsManager:
    """Manage application settings"""
    
    def __init__(self, database, user_email):
        self.database = database
        self.user_email = user_email
    
    def is_adult_content_blocking_enabled(self) -> bool:
        """Check if adult content blocking is enabled"""
        setting = self.database.get_setting(self.user_email, 'checkBox')
        return setting if setting is not None else True  # Default to enabled
    
    def get_block_message(self) -> str:
        """Get custom block message from the UI settings"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'block_message'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            print(f"Error getting block message: {e}")
            
        # Default message if not found
        return """
        <div style='text-align: center; font-size: 18px; color: #2c3e50;'>
        <h2>اتقي الله في نفسك</h2>
        <p>This content has been blocked for your protection.</p>
        </div>
        """
    
    def get_countdown_seconds(self) -> int:
        """Get countdown duration from the UI settings"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'countdown_duration'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                if result:
                    return int(result[0])
        except Exception as e:
            print(f"Error getting countdown duration: {e}")
            
        return 30  # Default value
    
    def get_redirect_url(self) -> str:
        """Get redirect URL from the UI settings"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'redirect_url'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    return result[0]
        except Exception as e:
            print(f"Error getting redirect URL: {e}")
            
        return "https://www.google.com"  # Default value

class AdultContentBlocker(QObject):
    """Main adult content blocking system"""
    
    def __init__(self, database, user_email):
        super().__init__()
        self.database = database
        self.user_email = user_email
        self.settings_manager = SettingsManager(database, user_email)
        self.browser_monitor = None
        self.current_block_screen = None
        self._cleanup_done = False
        
    def start_blocking(self):
        """Start the content blocking system"""
        if self.browser_monitor:
            return  # Already started
            
        self.browser_monitor = BrowserMonitor(self.settings_manager)
        self.browser_monitor.content_blocked.connect(self.show_block_screen)
        self.browser_monitor.start()
        print("Adult content blocking started")
    
    def stop_blocking(self):
        """Stop the content blocking system"""
        try:
            if self.current_block_screen:
                self.current_block_screen.close()
                self.current_block_screen = None
            
            if self.browser_monitor:
                self.browser_monitor.stop_monitoring()
                self.browser_monitor.quit()
                self.browser_monitor.wait()
                self.browser_monitor = None
                
            print("Adult content blocking stopped")
        except Exception as e:
            print(f"Error stopping content blocking: {e}")
    
    def cleanup(self):
        """Clean up resources before application exit"""
        if not self._cleanup_done:
            self.stop_blocking()
            self._cleanup_done = True
    
    def show_block_screen(self, url: str, reason: str, detected_content: str):
        """Show the blocking screen"""
        # Close any existing block screen
        if self.current_block_screen:
            self.current_block_screen.close()
        
        # Get settings
        message = self.settings_manager.get_block_message()
        countdown = self.settings_manager.get_countdown_seconds()
        redirect_url = self.settings_manager.get_redirect_url()
        
        # Create and show block screen
        self.current_block_screen = BlockScreen(
            message=message,
            reason=f"Reason: {reason}",
            countdown_seconds=countdown,
            redirect_url=redirect_url
        )
        
        self.current_block_screen.exec_()
        self.current_block_screen = None
    
    def is_blocking_enabled(self) -> bool:
        """Check if blocking is currently enabled"""
        return self.settings_manager.is_adult_content_blocking_enabled()

# Integration with main application
def integrate_with_main_window(main_window):
    """Integrate the blocker with the main window"""
    
    # Initialize the blocker
    main_window.adult_content_blocker = AdultContentBlocker(
        main_window.db, 
        main_window.user_email
    )
    
    # Connect to settings changes
    def on_adult_content_setting_changed(checked):
        if checked:
            main_window.adult_content_blocker.start_blocking()
        else:
            main_window.adult_content_blocker.stop_blocking()
    
    # Connect settings UI elements
    if hasattr(main_window, 'checkBox'):
        main_window.checkBox.toggled.connect(on_adult_content_setting_changed)
    
    # Connect plainTextEdit in groupBox_6
    if hasattr(main_window, 'plainTextEdit'):
        def save_block_message():
            message = main_window.plainTextEdit.toPlainText()
            with sqlite3.connect(main_window.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_settings (user_email, setting_name, setting_value, setting_type) "
                    "VALUES (?, 'block_message', ?, 'text')",
                    (main_window.user_email, message)
                )
                conn.commit()
        main_window.plainTextEdit.textChanged.connect(save_block_message)
    
    # Connect spinBox in groupBox_8
    if hasattr(main_window, 'spinBox'):
        def save_countdown():
            value = main_window.spinBox.value()
            with sqlite3.connect(main_window.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_settings (user_email, setting_name, setting_value, setting_type) "
                    "VALUES (?, 'countdown_duration', ?, 'number')",
                    (main_window.user_email, str(value))
                )
                conn.commit()
        main_window.spinBox.valueChanged.connect(save_countdown)
    
    # Connect lineEdit_2 in groupBox_7
    if hasattr(main_window, 'lineEdit_2'):
        def save_redirect_url():
            url = main_window.lineEdit_2.text()
            with sqlite3.connect(main_window.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_settings (user_email, setting_name, setting_value, setting_type) "
                    "VALUES (?, 'redirect_url', ?, 'text')",
                    (main_window.user_email, url)
                )
                conn.commit()
        main_window.lineEdit_2.textChanged.connect(save_redirect_url)
    
    # Connect cleanup to application quit
    app = QApplication.instance()
    if app:
        app.aboutToQuit.connect(main_window.adult_content_blocker.cleanup)
    
    # Start blocking if enabled
    if main_window.adult_content_blocker.is_blocking_enabled():
        main_window.adult_content_blocker.start_blocking()

# Example usage and testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test the block screen
    block_screen = BlockScreen(
        message="""
        <div style='text-align: center; font-size: 18px; color: #2c3e50;'>
        <h2>اتقي الله في نفسك</h2>
        <p>This content has been blocked for your protection.</p>
        <p>Content blocking helps maintain a safe browsing environment.</p>
        </div>
        """,
        reason="Adult content detected: explicit, mature content",
        countdown_seconds=10,
        redirect_url="https://www.google.com"
    )
    
    block_screen.exec_()
    sys.exit(app.exec_())