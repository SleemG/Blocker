import time
import threading
from typing import Optional
import win32gui
import win32process
import psutil
from PyQt5.QtCore import QObject, pyqtSignal
from .adult_content_blocker import ContentAnalyzer

class BrowserMonitor(QObject):
    """Monitors browser windows for adult content"""
    
    # Signal emitted when content is detected
    content_detected = pyqtSignal(str, str)  # url, reason
    
    def __init__(self, database_path: str, user_email: str):
        super().__init__()
        print("Initializing BrowserMonitor...")
        self.database_path = database_path
        self.user_email = user_email
        self.is_monitoring = False
        self.content_analyzer = ContentAnalyzer()
        self.content_analyzer.content_detected.connect(self._on_content_detected)
        self.monitor_thread = None
        print("BrowserMonitor initialized")
    
    def start(self):
        """Start monitoring browser windows"""
        if self.is_monitoring:
            print("Monitor already running")
            return
            
        print("Starting browser monitor...")
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Browser monitor started")
    
    def stop(self):
        """Stop monitoring"""
        print("Stopping browser monitor...")
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("Browser monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        print("Monitor loop started")
        while self.is_monitoring:
            try:
                # Get all browser windows
                browser_windows = self._get_browser_windows()
                if browser_windows:
                    print(f"Found {len(browser_windows)} browser windows")
                    for window in browser_windows:
                        self._check_window(window)
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(2)
    
    def _get_browser_windows(self):
        """Get all browser windows"""
        windows = []
        def enum_window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        if any(browser in process.name().lower() 
                             for browser in ['chrome', 'firefox', 'msedge', 'opera']):
                            windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'pid': pid,
                                'process': process.name()
                            })
                    except Exception:
                        pass
        
        win32gui.EnumWindows(enum_window_callback, windows)
        return windows
    
    def _check_window(self, window):
        """Check a browser window for adult content"""
        try:
            title = window['title']
            print(f"\nChecking window: {title}")
            
            # Extract URL from title
            url = self._extract_url(title)
            if url:
                print(f"Found URL: {url}")
                # Analyze the URL
                self.content_analyzer.analyze_url(url)
        except Exception as e:
            print(f"Error checking window: {e}")
    
    def _extract_url(self, title: str) -> Optional[str]:
        """Extract URL from window title"""
        import re
        
        # Skip browser-specific titles
        skip_terms = ['google chrome', 'mozilla firefox', 'microsoft edge', 
                     'new tab', 'blank page']
        title_lower = title.lower()
        if any(term in title_lower for term in skip_terms):
            return None
        
        # Try to find URL in title
        patterns = [
            r'https?://[^\s\-]+',  # Direct URL
            r'(?:- )?((?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',  # Domain
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return None
    
    def _on_content_detected(self, url: str, reason: str):
        """Handle content detection"""
        print(f"Content detected in monitor - URL: {url}, Reason: {reason}")
        self.content_detected.emit(url, reason)
