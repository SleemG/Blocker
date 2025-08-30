import sys
import os
import re
import time
import threading
from typing import List, Dict, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont
import psutil
import win32gui
import win32process
import win32api

# Import the proper block screen implementation
from ..ui.blkScrn import BlockScreen

from .content_filters import ADULT_DOMAINS, ADULT_KEYWORDS, SUSPICIOUS_URL_PATTERNS

class ContentAnalyzer(QObject):
    """Analyzes web content for adult material"""
    
    # Signal for content detection
    content_detected = pyqtSignal(str, str)  # url, reason
    
    def __init__(self):
        super().__init__()
        print("Initializing ContentAnalyzer")
        
        # Load filters from configuration
        self.adult_domains = ADULT_DOMAINS
        self.adult_keywords = ADULT_KEYWORDS
        self.suspicious_patterns = SUSPICIOUS_URL_PATTERNS
    
    def analyze_url(self, url: str) -> Dict[str, any]:
        """Analyze URL for adult content"""
        result = {
            'is_blocked': False,
            'reason': '',
            'score': 0,
            'detected_keywords': []
        }
        
        if not url:  # Handle None or empty URLs
            return result
            
        try:
            # Debug print
            print(f"Analyzing URL: {url}")
            
            # Check domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower() if parsed_url.netloc else ''
            
            # Debug print
            print(f"Checking domain: {domain}")
            
            for adult_domain in self.adult_domains:
                if adult_domain in domain:
                    print(f"Adult domain detected: {adult_domain}")
                    result['is_blocked'] = True
                    result['reason'] = f'Blocked domain: {adult_domain}'
                    result['score'] = 100
                    self._notify_block_detected(url, result['reason'])
                    return result
            
            # Analyze URL path and query
            full_url = url.lower()
            detected = []
            
            # Debug print
            print("Checking for suspicious patterns in URL...")
            
            # Check keyword matches
            for keyword in self.adult_keywords:
                if keyword in full_url:
                    print(f"Found keyword in URL: {keyword}")
                    detected.append(keyword)
                    result['score'] += 10
            
            # Check regex patterns
            for pattern in self.suspicious_patterns:
                matches = re.findall(pattern, full_url)
                if matches:
                    print(f"Found suspicious pattern in URL: {pattern}")
                    detected.append(matches[0])  # Add the first match
                    result['score'] += 15  # Higher score for regex pattern matches
            
            if detected:
                result['detected_keywords'] = detected
                if result['score'] >= 30:  # Threshold for blocking
                    print(f"Score {result['score']} exceeds threshold")
                    result['is_blocked'] = True
                    result['reason'] = f'Adult keywords detected: {", ".join(detected[:3])}'
                    print(f"Adult content detected: keywords pattern matched")
                    self._notify_block_detected(url, result['reason'])
            
        except Exception as e:
            print(f"Error analyzing URL: {e}")
            import traceback
            print(traceback.format_exc())
        
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
                print(f"Adult content detected: content pattern matched")
                self._notify_block_detected(url, result['reason'])
            
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
    
    def analyze_text(self, text: str) -> Dict[str, any]:
        """Analyze text content for adult material"""
        result = {
            'is_blocked': False,
            'reason': '',
            'score': 0,
            'detected_keywords': []
        }
        
        try:
            # First check for known adult domains
            for domain in self.adult_domains:
                if domain.lower() in text.lower():
                    result['is_blocked'] = True
                    result['reason'] = f'Adult domain detected: {domain}'
                    result['score'] = 100
                    result['detected_keywords'] = [domain]
                    self._notify_block_detected(text, result['reason'])
                    return result
            
            # Then analyze the text for keywords
            detected = self._find_adult_keywords(text)
            
            if detected:
                result['detected_keywords'] = detected
                result['score'] = len(detected) * 10
                
                # Block if score exceeds threshold
                if result['score'] >= 30:  # Same threshold as URL/content analysis
                    result['is_blocked'] = True
                    result['reason'] = f'Adult content detected: {", ".join(detected[:3])}'
                    self._notify_block_detected(text, result['reason'])
        except Exception as e:
            print(f"Error analyzing text: {e}")
            
        return result
    
    def _notify_block_detected(self, url: str, reason: str):
        """Notify that adult content was detected - internal method"""
        print(f"Adult content detected at: {url}")
        print(f"Reason: {reason}")
        # Emit the signal for the main blocker to handle
        self.content_detected.emit(url, reason)

class BrowserMonitor(QThread):
    """Monitor browser activity for adult content"""
    
    content_blocked = pyqtSignal(str, str, str)  # url, reason, detected_content
    
    def __init__(self, database, user_email):
        super().__init__()
        print("Initializing BrowserMonitor...")
        self.settings_manager = SettingsManager(database, user_email)
        self.content_analyzer = ContentAnalyzer()
        self.is_monitoring = False
        self.last_urls = {}  # Track last URLs for each browser
        
        # Connect content analyzer signals
        self.content_analyzer.content_detected.connect(
            lambda url, reason: self.content_blocked.emit(url, reason, "")
        )
        print("BrowserMonitor initialized")
        
    def run(self):
        """Main monitoring loop"""
        print("Starting browser monitor thread...")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Check if adult content blocking is enabled
                if not self.settings_manager.is_adult_content_blocking_enabled():
                    print("Adult content blocking is disabled")
                    time.sleep(2)
                    continue
                
                print("Checking browser windows...")
                # Get active browser windows
                browser_windows = self.get_browser_windows()
                
                if browser_windows:
                    print(f"Found {len(browser_windows)} browser windows")
                    for window_info in browser_windows:
                        print(f"Checking window: {window_info['title']}")
                        self.check_browser_content(window_info)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in browser monitoring: {e}")
                import traceback
                print(traceback.format_exc())
                time.sleep(2)
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_monitoring = False
    
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
            title = window_info['title']
            print(f"\nChecking content for window: {title}")
            
            # First directly check title against keywords
            title_lower = title.lower()
            from .content_filters import ADULT_KEYWORDS, ADULT_DOMAINS
            
            # Check for keywords first
            for keyword in ADULT_KEYWORDS:
                if keyword.lower() in title_lower:
                    reason = f"Blocked keyword found in title: {keyword}"
                    print(f"Adult content detected in title: {reason}")
                    if not hasattr(self, 'current_block_screen') or not self.current_block_screen:
                        self.content_blocked.emit(title, reason, keyword)
                    return
            
            # Then check for domain names
            for domain in ADULT_DOMAINS:
                domain_name = domain.split('.')[0]  # Get just the domain name without TLD
                if domain_name.lower() in title_lower:
                    reason = f"Blocked domain found in title: {domain}"
                    print(f"Adult content detected in title: {reason}")
                    if not hasattr(self, 'current_block_screen') or not self.current_block_screen:
                        self.content_blocked.emit(title, reason, domain)
                    return
            
            # If no adult content in title, try to get URL
            url = self.extract_url_from_title(title)
            if not url:
                print("No URL found in title")
                return
            
            print(f"Found URL: {url}")
            
            # Skip if we already checked this URL recently
            process_id = window_info['pid']
            if process_id in self.last_urls and self.last_urls[process_id] == url:
                print("URL was recently checked, skipping")
                return
            
            self.last_urls[process_id] = url
            print("Analyzing URL content...")
            
            # Analyze URL
            url_analysis = self.content_analyzer.analyze_url(url)
            print(f"URL analysis result: {url_analysis}")
            
            if url_analysis['is_blocked']:
                print("URL is blocked, emitting signal")
                self.content_blocked.emit(url, url_analysis['reason'], 
                                        ', '.join(url_analysis['detected_keywords']))
                return
            
            # Try to get page content
            try:
                print("Fetching page content...")
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    print("Analyzing page content...")
                    content_analysis = self.content_analyzer.analyze_html_content(response.text, url)
                    print(f"Content analysis result: {content_analysis}")
                    
                    if content_analysis['is_blocked']:
                        print("Content is blocked, emitting signal")
                        self.content_blocked.emit(url, content_analysis['reason'],
                                                ', '.join(content_analysis['detected_keywords']))
                        
            except requests.RequestException as e:
                print(f"Error fetching content: {e}")  # Log the error for debugging
                
        except Exception as e:
            print(f"Error checking browser content: {e}")
    
    def extract_url_from_title(self, title: str) -> Optional[str]:
        """Extract URL or domain from browser window title"""
        # First try to find a full URL
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, title)
        if match:
            return match.group(0)
        
        # Then try to find common domains
        domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'
        match = re.search(domain_pattern, title.lower())
        if match:
            domain = match.group(0)
            # Skip obvious non-website domains
            if any(skip in domain for skip in ['microsoft', 'windows', 'mozilla', 'firefox', 'chrome', 'edge']):
                return None
            return f"http://{domain}"
            
        return None

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
        """Get custom block message from database"""
        message = self.database.get_setting(self.user_email, 'block_screen_message')
        if not message:
            # Return default message if none saved
            return """<div style='text-align: center; font-size: 18px; color: #2c3e50;'>
<h2>اتقي الله في نفسك</h2>
<p>This content has been blocked for your protection.</p>
<p>Content blocking helps maintain a safe browsing environment.</p>
</div>"""
        return message
    
    def get_countdown_seconds(self) -> int:
        """Get countdown duration from database"""
        duration = self.database.get_setting(self.user_email, 'block_screen_timer')
        try:
            if duration:
                return int(duration)
        except (ValueError, TypeError):
            print("Invalid duration in database")
        return 30  # Default if no valid setting found
    
    def get_redirect_url(self) -> str:
        """Get redirect URL"""
        # In practice, this would come from groupBox_7->lineEdit_2
        return "https://www.google.com"

class AdultContentBlocker(QObject):
    """Main adult content blocking system"""
    
    def __init__(self, database, user_email):
        super().__init__()
        print("Initializing AdultContentBlocker...")
        self.database = database
        self.user_email = user_email
        self.current_block_screen = None
        self.content_analyzer = ContentAnalyzer()
        
        # Create browser monitor
        self.settings_manager = SettingsManager(database, user_email)
        self.browser_monitor = BrowserMonitor(database, user_email)
        
        # Connect signals
        self.browser_monitor.content_blocked.connect(self.handle_detected_content)
        self.content_analyzer.content_detected.connect(self.handle_detected_content)
        
        # Start monitoring automatically
        print("Starting monitoring automatically...")
        self.start_blocking()
        
    def start_blocking(self):
        """Start the content blocking system"""
        print("Starting content blocking system...")
        
        # If we don't have a browser monitor, create one
        if not self.browser_monitor:
            self.browser_monitor = BrowserMonitor(self.database, self.user_email)
            self.browser_monitor.content_blocked.connect(self.handle_detected_content)
        
        # Make sure monitoring is enabled
        self.browser_monitor.is_monitoring = True
        
        # Start the monitor if it's not running
        if not self.browser_monitor.isRunning():
            print("Starting browser monitor thread...")
            self.browser_monitor.start()
            print("Adult content blocking started")
        else:
            print("Browser monitor thread already running")
        
    def handle_detected_content(self, url: str, reason: str, detected_content: str = ""):
        """Handle detected adult content"""
        print(f"Content detected - URL: {url}, Reason: {reason}, Content: {detected_content}")
        
        # Don't create a new block screen if one is already showing
        if self.current_block_screen is not None:
            print("Block screen already showing, skipping...")
            return
            
        try:
            print("Creating block screen...")
            self.current_block_screen = BlockScreen(user_email=self.user_email)
            
            # Set the reason text
            if hasattr(self.current_block_screen, 'blkRsn_lbl'):
                self.current_block_screen.blkRsn_lbl.setText(f"Blocked: {url}\nReason: {reason}")
                # self.current_block_screen.blkRsn_lbl.show()
            print("Showing block screen...")
            self.current_block_screen.show()
            self.current_block_screen.activateWindow()
            self.current_block_screen.raise_()
            result = self.current_block_screen.exec_()
            print(f"Block screen closed with result: {result}")
            if self.current_block_screen:
                self.current_block_screen.deleteLater()
                self.current_block_screen = None
        except Exception as e:
            print(f"Error showing block screen: {e}")
            import traceback
            print(traceback.format_exc())
            # Clean up on error
            if self.current_block_screen:
                try:
                    self.current_block_screen.deleteLater()
                except:
                    pass
                self.current_block_screen = None
    
    def stop_blocking(self):
        """Stop the content blocking system"""
        if self.browser_monitor:
            self.browser_monitor.stop_monitoring()
            print("Stopped monitoring")
            if self.browser_monitor.isRunning():
                self.browser_monitor.quit()
                self.browser_monitor.wait()
            self.browser_monitor.is_monitoring = False
            
        # Clear any existing block screen
        if self.current_block_screen:
            try:
                self.current_block_screen.close()
                self.current_block_screen.deleteLater()
            except:
                pass
            self.current_block_screen = None
            
        print("Adult content blocking stopped")
    
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
        print(f"Adult content blocking setting changed to: {checked}")
        if checked:
            if not main_window.adult_content_blocker.browser_monitor or \
               not main_window.adult_content_blocker.browser_monitor.isRunning():
                main_window.adult_content_blocker.start_blocking()
            else:
                print("Enabling existing monitor...")
                main_window.adult_content_blocker.browser_monitor.is_monitoring = True
        else:
            main_window.adult_content_blocker.stop_blocking()
    
    # Connect to the checkBox toggle (assuming it's converted to toggle switch)
    if hasattr(main_window, 'checkBox_toggle'):
        main_window.checkBox_toggle.toggled.connect(on_adult_content_setting_changed)
    
    # Start blocking if enabled by default
    if main_window.adult_content_blocker.is_blocking_enabled():
        main_window.adult_content_blocker.start_blocking()
        
    # Add cleanup on window close
    original_close_event = main_window.closeEvent
    def enhanced_close_event(event):
        if hasattr(main_window, 'adult_content_blocker'):
            main_window.adult_content_blocker.stop_blocking()
        original_close_event(event)
    main_window.closeEvent = enhanced_close_event

# Example usage and testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
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