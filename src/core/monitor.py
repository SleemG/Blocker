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
        try:
            # Connect signal handler
            self.content_analyzer.content_detected.connect(self._on_content_detected)
            print("Connected signal handlers")
            
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Browser monitor thread started")
            
            # Verify thread is running
            if self.monitor_thread.is_alive():
                print("Monitor thread is confirmed running")
            else:
                print("WARNING: Monitor thread failed to start!")
        except Exception as e:
            print(f"Error starting monitor: {str(e)}")
    
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
            
            # First check the title itself for keywords
            print("Checking title for keywords...")
            try:
                # Import both keywords and domains
                from .content_filters import ADULT_KEYWORDS, ADULT_DOMAINS
                
                # Clean and prepare the title
                title_lower = ' ' + title.lower() + ' '  # Add spaces to ensure word boundaries
                print(f"Title being checked: {title_lower}")
                
                # Check keywords
                for keyword in ADULT_KEYWORDS:
                    keyword_lower = ' ' + keyword.lower() + ' '
                    print(f"Checking keyword: {keyword}")
                    if keyword_lower in title_lower:
                        print(f"MATCH FOUND! Blocked keyword found in title: {keyword}")
                        self._handle_blocked_content(title, f"Blocked keyword found: {keyword}")
                        return
                
                # Check domains
                for domain in ADULT_DOMAINS:
                    if domain.lower() in title_lower:
                        print(f"MATCH FOUND! Blocked domain found in title: {domain}")
                        self._handle_blocked_content(title, f"Blocked domain found: {domain}")
                        return
                        
                print("No keywords or domains matched in title")
            except Exception as e:
                print(f"Error checking keywords: {str(e)}")
            
            # Extract URL from title
            url = self._extract_url(title)
            if url:
                print(f"Found URL: {url}")
                # Analyze the URL
                result = self.content_analyzer.analyze_url(url)
                if result.get('is_blocked'):
                    self._handle_blocked_content(url, result.get('reason', 'Blocked URL'))
        except Exception as e:
            print(f"Error checking window: {e}")
            
    def _handle_blocked_content(self, url: str, reason: str):
        """Handle blocked content detection"""
        print(f"BLOCKED: {url} - {reason}")
        self.content_detected.emit(url, reason)
        # Trigger the block screen
        from ..ui.blkScrn import BlockScreen
        block_screen = BlockScreen(
            message="Content blocked for your protection",
            reason=reason,
            countdown_seconds=10,
            redirect_url="https://www.google.com"
        )
        block_screen.exec_()
    
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
