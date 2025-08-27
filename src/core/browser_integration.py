import json
import os
import subprocess
import tempfile
import threading
import time
from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import re
import requests
import win32gui
from PyQt5.QtWidgets import QApplication


class BrowserExtensionCommunicator:
    """Handles communication with browser extensions for content monitoring"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.native_messaging_dir = None
        self.setup_native_messaging()
        
    def setup_native_messaging(self):
        """Setup native messaging for Chrome/Edge extensions"""
        try:
            # Create native messaging host
            app_data = os.getenv('APPDATA')
            chrome_dir = os.path.join(app_data, r'Google\Chrome\User Data\NativeMessagingHosts')
            edge_dir = os.path.join(app_data, r'Microsoft\Edge\User Data\NativeMessagingHosts')
            
            for browser_dir in [chrome_dir, edge_dir]:
                if os.path.exists(os.path.dirname(browser_dir)):
                    os.makedirs(browser_dir, exist_ok=True)
                    self.create_native_messaging_manifest(browser_dir)
                    
        except Exception as e:
            print(f"Error setting up native messaging: {e}")
    
    def create_native_messaging_manifest(self, browser_dir: str):
        """Create native messaging manifest file"""
        manifest = {
            "name": "com.blockerhero.contentmonitor",
            "description": "BlockerHero Content Monitor",
            "path": os.path.abspath(__file__),
            "type": "stdio",
            "allowed_origins": [
                "chrome-extension://blockerhero-extension-id/"
            ]
        }
        
        manifest_path = os.path.join(browser_dir, "com.blockerhero.contentmonitor.json")
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            print(f"Error creating manifest: {e}")

class ProxyContentFilter:
    """HTTP/HTTPS proxy for content filtering"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.proxy_port = 8888
        
    def start_proxy(self):
        """Start the content filtering proxy"""
        try:
            from mitmproxy import options, master
            from mitmproxy.addons import core
            import asyncio
            
            # Configure proxy options
            opts = options.Options(listen_port=self.proxy_port)
            m = master.Master(opts)
            m.addons.add(core.Core())
            
            # Run proxy in separate thread
            def run_proxy():
                asyncio.set_event_loop(asyncio.new_event_loop())
                asyncio.get_event_loop().run_until_complete(m.run())
            
            proxy_thread = threading.Thread(target=run_proxy, daemon=True)
            proxy_thread.start()
            
            print(f"Content filtering proxy started on port {self.proxy_port}")
            return True
            
        except ImportError:
            print("mitmproxy not installed. Using alternative monitoring method.")
            return False
        except Exception as e:
            print(f"Error starting proxy: {e}")
            return False

class BrowserContentMonitor:
    """Monitor browser content using window titles and content analysis"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.is_monitoring = False
        self.blocked_websites = []
        self.reload_blocked_websites()
        
    def reload_blocked_websites(self):
        """Reload blocked websites from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT item FROM blocked_items 
                    WHERE email = ? AND type = 'block' AND item_type = 'website'
                ''', (self.user_email,))
                self.blocked_websites = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading blocked websites: {e}")
            self.blocked_websites = []
            
    def should_block_url(self, url: str) -> Tuple[bool, str]:
        """Check if URL should be blocked"""
        try:
            # Reload blocked websites to get latest
            self.reload_blocked_websites()
            
            # Parse the URL
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
                
            # Check against blocked websites
            for blocked_site in self.blocked_websites:
                blocked_domain = blocked_site.lower()
                if blocked_domain.startswith('www.'):
                    blocked_domain = blocked_domain[4:]
                    
                if blocked_domain in domain:
                    return True, f"Website {blocked_site} is blocked"
                    
            return False, ""
            
        except Exception as e:
            print(f"Error checking URL {url}: {e}")
            return False, ""
        
    def start_monitoring(self):
        """Start network monitoring"""
        try:
            import scapy.all as scapy
            from scapy.layers.http import HTTPRequest, HTTPResponse
            
            self.is_monitoring = True
            
            def packet_handler(packet):
                if not self.is_monitoring:
                    return
                    
                if packet.haslayer(HTTPRequest):
                    self.analyze_http_request(packet)
            
            # Start packet capture in separate thread
            def start_capture():
                scapy.sniff(filter="tcp port 80 or tcp port 443", prn=packet_handler)
            
            capture_thread = threading.Thread(target=start_capture, daemon=True)
            capture_thread.start()
            
            print("Network monitoring started")
            return True
            
        except ImportError:
            print("Scapy not installed. Network monitoring not available.")
            return False
        except Exception as e:
            print(f"Error starting network monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.is_monitoring = False
    
    def analyze_http_request(self, packet):
        """Analyze HTTP request for adult content"""
        try:
            from scapy.layers.http import HTTPRequest
            
            if packet.haslayer(HTTPRequest):
                http_layer = packet[HTTPRequest]
                url = f"http://{http_layer.Host.decode()}{http_layer.Path.decode()}"
                
                # Check if adult content blocking is enabled
                if self.is_adult_blocking_enabled():
                    # Analyze URL and trigger block if needed
                    from adult_content_blocker import ContentAnalyzer
                    analyzer = ContentAnalyzer()
                    result = analyzer.analyze_url(url)
                    
                    if result['is_blocked']:
                        self.trigger_block_screen(url, result['reason'])
                        
        except Exception as e:
            print(f"Error analyzing HTTP request: {e}")
    
    def is_adult_blocking_enabled(self) -> bool:
        """Check if adult content blocking is enabled"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                # First check the main adult content blocking setting
                cursor.execute("""
                    SELECT setting_value FROM user_settings 
                    WHERE user_email = ? AND setting_name = 'adult_content_blocking'
                """, (self.user_email,))
                result = cursor.fetchone()
                main_setting = result[0].lower() == 'true' if result else True

                # Then check auto-block setting
                cursor.execute("""
                    SELECT setting_value FROM user_settings 
                    WHERE user_email = ? AND setting_name = 'auto_block_adult'
                """, (self.user_email,))
                result = cursor.fetchone()
                auto_block = result[0].lower() == 'true' if result else True

                return main_setting and auto_block
        except Exception as e:
            print(f"Error checking adult blocking settings: {e}")
            return True  # Default to enabled for safety
    
    def trigger_block_screen(self, url: str, reason: str):
        """Trigger the block screen"""
        try:
            print(f"BLOCK TRIGGERED: {url} - {reason}")
            # Actually show the block screen
            self._show_block_screen(url)
        except Exception as e:
            print(f"Error triggering block screen: {e}")

class DNSFilter:
    """DNS-based content filtering"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.hosts_file_path = r"C:\Windows\System32\drivers\etc\hosts"
        self.hosts_backup_path = r"C:\Windows\System32\drivers\etc\hosts.blockerhero.backup"
        
    def setup_dns_filtering(self):
        """Setup DNS filtering by modifying hosts file"""
        try:
            # Backup original hosts file
            if not os.path.exists(self.hosts_backup_path):
                import shutil
                shutil.copy2(self.hosts_file_path, self.hosts_backup_path)
            
            # Read current hosts file
            with open(self.hosts_file_path, 'r') as f:
                current_content = f.read()
            
            # Add BlockerHero section
            if "# BlockerHero Adult Content Filter" not in current_content:
                adult_domains = self.get_adult_domains()
                
                hosts_entries = ["\n# BlockerHero Adult Content Filter"]
                for domain in adult_domains:
                    hosts_entries.append(f"0.0.0.0 {domain}")
                    hosts_entries.append(f"0.0.0.0 www.{domain}")
                hosts_entries.append("# End BlockerHero Filter\n")
                
                # Append to hosts file (requires admin privileges)
                with open(self.hosts_file_path, 'a') as f:
                    f.write('\n'.join(hosts_entries))
                
                print("DNS filtering enabled")
                return True
                
        except PermissionError:
            print("Administrator privileges required for DNS filtering")
            return False
        except Exception as e:
            print(f"Error setting up DNS filtering: {e}")
            return False
    
    def remove_dns_filtering(self):
        """Remove DNS filtering entries from hosts file"""
        try:
            with open(self.hosts_file_path, 'r') as f:
                lines = f.readlines()
            
            # Remove BlockerHero section
            filtered_lines = []
            skip_section = False
            
            for line in lines:
                if "# BlockerHero Adult Content Filter" in line:
                    skip_section = True
                    continue
                elif "# End BlockerHero Filter" in line:
                    skip_section = False
                    continue
                elif not skip_section:
                    filtered_lines.append(line)
            
            # Write back to hosts file
            with open(self.hosts_file_path, 'w') as f:
                f.writelines(filtered_lines)
            
            print("DNS filtering disabled")
            return True
            
        except Exception as e:
            print(f"Error removing DNS filtering: {e}")
            return False
    
    def get_adult_domains(self) -> List[str]:
        """Get list of adult domains to block"""
        return [
            'pornhub.com', 'xvideos.com', 'redtube.com', 'youporn.com',
            'xhamster.com', 'tube8.com', 'beeg.com', 'spankbang.com',
            'tnaflix.com', 'drtuber.com', 'porn.com', 'sex.com',
            'xnxx.com', 'chaturbate.com', 'cam4.com', 'bongacams.com',
            'stripchat.com', 'livejasmin.com', 'camsoda.com', 'myfreecams.com'
        ]

class RegistryBrowserMonitor:
    """Monitor browser URLs using Windows registry and process monitoring"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.is_monitoring = False
        self.last_check_time = {}
        
    def start_monitoring(self):
        """Start monitoring browser activity"""
        try:
            # Import needed modules
            import win32gui
            import psutil
            
            self.is_monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            print("Registry browser monitoring started")
            return True
        except ImportError as e:
            print(f"Error: Required modules not found - {e}")
            print("Please install pywin32 and psutil: pip install pywin32 psutil")
            return False
        except Exception as e:
            print(f"Error starting monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        print("Registry browser monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                if self.is_adult_blocking_enabled():
                    self._check_browser_activity()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(5)
    
    def _check_browser_activity(self):
        """Check current browser activity"""
        try:
            import psutil
            from win32gui import GetWindowText, GetForegroundWindow
            
            # Get current active window title
            active_window_title = GetWindowText(GetForegroundWindow())
            
            # Check if it's a browser window and extract URL
            url = self._extract_url_from_title(active_window_title)
            if url:
                # First check if the domain is blocked
                blocked, reason = self.should_block_url(url)
                if blocked:
                    print(f"Blocking access to {url}: {reason}")
                    self.trigger_block_screen(url, reason)
                    return
                
                # Then check content for adult material
                from ..core.content_analyzer import ContentAnalyzer
                analyzer = ContentAnalyzer(self.database_path, self.user_email)
                result = analyzer.analyze_webpage(url)
                
                if result.get('is_blocked', False):
                    print(f"Adult content detected at: {url}")
                    reason = result.get('reason', 'Adult content detected')
                    print(f"Attempting to trigger block screen for URL: {url}")
                    # Set the block reason in the database
                    with sqlite3.connect(self.database_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE user_settings 
                            SET setting_value = ? 
                            WHERE user_email = ? AND setting_name = 'last_blocked_url'
                        """, (url, self.user_email))
                        conn.commit()
                    # Show block screen
                    self._show_block_screen_direct(url, reason)
                    print("Block screen trigger completed")
            
            # Get all browser processes
            browser_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if any(browser in proc.info['name'].lower() 
                          for browser in ['chrome', 'firefox', 'edge', 'opera']):
                        browser_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check each browser process
            for proc in browser_processes:
                self._check_browser_process(proc)
                
        except Exception as e:
            print(f"Error checking browser activity: {e}")
    
    def _check_browser_process(self, process):
        """Check a specific browser process"""
        import win32gui
        import win32process
        try:
            # Get process windows
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid == process.pid:
                            title = win32gui.GetWindowText(hwnd)
                            if title and len(title) > 10:  # Filter out empty/short titles
                                windows.append(title)
                    except:
                        pass
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # Analyze window titles for URLs
            for title in windows:
                url = self._extract_url_from_title(title)
                if url:
                    self._analyze_url(url, title)
                    
        except Exception as e:
            print(f"Error checking browser process: {e}")
    
    def _extract_url_from_title(self, title: str) -> Optional[str]:
        """Extract URL from browser window title"""
        import re
        
        # Common patterns for URLs in browser titles
        patterns = [
            r'https?://[^\s\-]+',  # Direct URL
            r'(?:- )?((?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',  # Domain after dash
        ]
        
        title_lower = title.lower()
        
        # Skip if it's just a browser name or common non-URL title
        if any(skip_term in title_lower for skip_term in 
               ['google chrome', 'mozilla firefox', 'microsoft edge', 'new tab', 'blank page']):
            return None
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return None
    
    def _analyze_url(self, url: str, title: str):
        """Analyze URL for adult content"""
        try:
            # Skip if we checked this URL recently
            current_time = time.time()
            if url in self.last_check_time:
                if current_time - self.last_check_time[url] < 10:  # 10 second cooldown
                    return
            
            self.last_check_time[url] = current_time
            
            # Import and use content analyzer
            from adult_content_blocker import ContentAnalyzer
            analyzer = ContentAnalyzer()
            
            # Analyze URL
            result = analyzer.analyze_url(url)
            
            if result['is_blocked']:
                print(f"BLOCKED URL DETECTED: {url}")
                print(f"Reason: {result['reason']}")
                self._trigger_block_screen(url, result['reason'], title)
                return
            
            # Also analyze page title for keywords
            title_result = analyzer._find_adult_keywords(title)
            if title_result:
                reason = f"Adult keywords in page title: {', '.join(title_result[:3])}"
                print(f"BLOCKED TITLE DETECTED: {title}")
                print(f"Reason: {reason}")
                self._trigger_block_screen(url, reason, title)
                
        except Exception as e:
            print(f"Error analyzing URL: {e}")
    
    def _trigger_block_screen(self, url: str, reason: str, title: str):
        """Trigger block screen (communicates with main app)"""
        try:
            # Create a signal file that the main app can monitor
            signal_file = os.path.join(tempfile.gettempdir(), 'blockerhero_signal.json')
            
            signal_data = {
                'timestamp': time.time(),
                'url': url,
                'reason': reason,
                'title': title,
                'user_email': self.user_email
            }
            
            with open(signal_file, 'w') as f:
                json.dump(signal_data, f)
            
            # Also try to show block screen directly
            self._show_block_screen_direct(url, reason)
            
        except Exception as e:
            print(f"Error triggering block screen: {e}")
    
    def _show_block_screen_direct(self, url: str, reason: str):
        """Show block screen directly"""
        try:
            print("Initializing block screen...")
            from PyQt5.QtWidgets import QApplication, QDesktopWidget
            from PyQt5.QtCore import Qt
            from ..ui.blkScrn import BlockScreen
            
            # Get the QApplication instance or create a new one
            app = QApplication.instance()
            if not app:
                print("Creating new QApplication instance")
                app = QApplication([])
            
            print(f"Creating block screen for URL: {url}")
            
            # Create the block screen
            self.block_screen = BlockScreen(user_email=self.user_email)  # Keep reference
            
            # Set the block reason
            if hasattr(self.block_screen, 'blkRsn_lbl'):
                print("Setting block reason label")
                self.block_screen.blkRsn_lbl.setText(f"Blocked URL: {url}")
                self.block_screen.blkRsn_lbl.show()
            
            # Ensure it covers the full screen on the correct monitor
            desktop = QDesktopWidget().screenGeometry()
            self.block_screen.resize(desktop.width(), desktop.height())
            
            print("Showing block screen")
            self.block_screen.show()
            self.block_screen.activateWindow()
            self.block_screen.raise_()
            
            # Force the screen to be modal and grab all input
            self.block_screen.setWindowState(Qt.WindowFullScreen)
            self.block_screen.setWindowFlags(
                Qt.WindowStaysOnTopHint | 
                Qt.FramelessWindowHint |
                Qt.WindowSystemMenuHint
            )
            
            print("Executing block screen modal loop")
            result = self.block_screen.exec_()
            print(f"Block screen closed with result: {result}")
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
            import traceback
            print("Traceback:", traceback.format_exc())
    
    def is_adult_blocking_enabled(self) -> bool:
        """Check if adult content blocking is enabled"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_email = ? AND setting_name = 'checkBox'",
                    (self.user_email,)
                )
                result = cursor.fetchone()
                return bool(result[0]) if result else True
        except Exception as e:
            print(f"Error checking setting: {e}")
            return True
        

class ContentBlockerService:
    """Main service that coordinates content blocking"""
    
    def __init__(self, database_path: str, user_email: str):
        self.database_path = database_path
        self.user_email = user_email
        self.is_running = False
        
        # Initialize browser monitor
        self.browser_monitor = self._setup_browser_monitor()
        
    def _setup_browser_monitor(self):
        """Setup the browser monitor based on available methods"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            
            # Create WebDriver instance
            driver = webdriver.Chrome(options=chrome_options)
            
            return {
                'driver': driver,
                'type': 'selenium'
            }
        except:
            # Fallback to basic URL monitoring
            return {
                'type': 'basic'
            }
    
    def start_all_monitoring(self):
        """Start content monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        print("Starting content blocking service...")
        
        try:
            if self.browser_monitor['type'] == 'selenium':
                # Start Selenium monitoring thread
                self._start_selenium_monitor()
            else:
                # Start basic URL monitoring
                self._start_basic_monitor()
            
            print("Content blocking service started successfully")
            
        except Exception as e:
            print(f"Error starting content blocking service: {e}")
    
    def stop_all_monitoring(self):
        """Stop content monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("Stopping content blocking service...")
        
        try:
            if self.browser_monitor['type'] == 'selenium':
                self.browser_monitor['driver'].quit()
            
            print("Content blocking service stopped")
            
        except Exception as e:
            print(f"Error stopping content blocking service: {e}")
    
    def _start_selenium_monitor(self):
        """Start monitoring with Selenium"""
        def monitor_loop():
            while self.is_running:
                try:
                    # Get current URL
                    current_url = self.browser_monitor['driver'].current_url
                    
                    # Get page content
                    page_source = self.browser_monitor['driver'].page_source
                    
                    # Analyze content
                    if self._analyze_content(current_url, page_source):
                        self._show_block_screen(current_url)
                    
                    time.sleep(1)  # Check every second
                except Exception as e:
                    print(f"Error in selenium monitor: {e}")
                    time.sleep(1)
        
        threading.Thread(target=monitor_loop, daemon=True).start()
    
    def _start_basic_monitor(self):
        """Start basic URL monitoring"""
        def monitor_loop():
            last_url = None
            browser_windows = {}
            
            def enum_window_callback(hwnd, windows):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if not title:  # Skip windows without titles
                            return
                        try:
                            classname = win32gui.GetClassName(hwnd)
                            # Check for common browser window classes
                            if any(browser in classname.lower() for browser in ['chrome', 'firefox', 'edge', 'iexplore']):
                                windows[hwnd] = title
                        except Exception:
                            # If we can't get class name, try to detect browser in title
                            if any(browser in title.lower() for browser in ['chrome', 'firefox', 'edge', 'internet explorer']):
                                windows[hwnd] = title
                except Exception:
                    pass  # Skip any window that causes errors
            
            while self.is_running:
                try:
                    # Get all browser windows
                    current_windows = {}
                    win32gui.EnumWindows(enum_window_callback, current_windows)
                    
                    # Check each browser window
                    for hwnd, title in current_windows.items():
                        # Extract URL from title
                        url = self._extract_url_from_title(title)
                        
                        # Only process if it's a new URL for this window
                        if url and (hwnd not in browser_windows or browser_windows[hwnd] != url):
                            browser_windows[hwnd] = url
                            try:
                                # First check if URL itself is blocked
                                if self._is_blocked_url(url):
                                    print(f"Blocked URL detected: {url}")
                                    self._show_block_screen(url)
                                    continue

                                # Try to get content
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                    'Accept-Language': 'en-US,en;q=0.5',
                                    'DNT': '1',
                                    'Connection': 'keep-alive',
                                    'Upgrade-Insecure-Requests': '1'
                                }
                                
                                response = requests.get(url, headers=headers, timeout=5, verify=True)
                                response.raise_for_status()  # Raise an error for bad status codes
                                
                                # Check content if response is successful
                                if self._analyze_content(url, response.text):
                                    print(f"Adult content detected at: {url}")
                                    self._show_block_screen(url)
                                    
                            except requests.RequestException as e:
                                print(f"Error fetching {url}: {e}")
                                continue
                    
                    # Clean up old window references
                    browser_windows = {hwnd: url for hwnd, url in browser_windows.items() 
                                    if hwnd in current_windows}
                    
                    time.sleep(0.5)  # Check twice per second
                    
                except Exception as e:
                    print(f"Error in basic monitor: {e}")
                    time.sleep(1)
                    browser_windows = {}  # Reset on error
        
        threading.Thread(target=monitor_loop, daemon=True).start()
    
    def _analyze_content(self, url: str, content: str) -> bool:
        """Analyze webpage content comprehensively"""
        try:
            # First check the URL
            if self._is_blocked_url(url):
                return True

            # Parse HTML content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check title
            if soup.title and self._has_adult_content(soup.title.string):
                return True
            
            # Check meta tags
            for meta in soup.find_all('meta'):
                # Check meta description
                if meta.get('name', '').lower() == 'description':
                    if self._has_adult_content(meta.get('content', '')):
                        return True
                
                # Check meta keywords
                if meta.get('name', '').lower() == 'keywords':
                    if self._has_adult_content(meta.get('content', '')):
                        return True
                
                # Check OpenGraph meta tags
                if meta.get('property', '').startswith('og:'):
                    if self._has_adult_content(meta.get('content', '')):
                        return True
            
            # Check all links
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href and self._is_blocked_url(href):
                    return True
                if self._has_adult_content(link.get_text()):
                    return True
            
            # Check image alt text and titles
            for img in soup.find_all('img'):
                if self._has_adult_content(img.get('alt', '')) or self._has_adult_content(img.get('title', '')):
                    return True
            
            # Check main content areas
            content_areas = soup.find_all(['p', 'div', 'article', 'section', 'main'])
            for area in content_areas:
                if self._has_adult_content(area.get_text()):
                    return True
            
            # Check headers
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for header in headers:
                if self._has_adult_content(header.get_text()):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return False
    
    def _is_blocked_url(self, url: str) -> bool:
        """Check if URL is in blocked list"""
        blocked_domains = [
            'pornhub.com', 'xvideos.com', 'redtube.com',
            # Add more domains as needed
        ]
        
        try:
            domain = urlparse(url).netloc
            return any(blocked in domain for blocked in blocked_domains)
        except:
            return False
    
    def _has_adult_content(self, content: str) -> bool:
        """Check content for adult material"""
        if not content:
            return False
            
        # Convert to string if not already
        content = str(content)
        
        # Common adult content patterns
        adult_patterns = {
            # Adult content indicators
            'explicit': [
                r'\b(?:porn|xxx|adult[\s-]content|nsfw)\b',
                r'\b(?:nude|naked|sex|explicit)\b',
                r'\b(?:pornography|erotic|erotica)\b'
            ],
            
            # Age verification related
            'age_verify': [
                r'\b(?:18\+|21\+|adult[\s-]only)\b',
                r'\b(?:age[\s-]verification|verify[\s-]age)\b',
                r'must\s+be\s+(?:18|21)\s+years'
            ],
            
            # Adult website indicators
            'site_indicators': [
                r'\b(?:webcam|cam[\s-]girl|live[\s-]cam)\b',
                r'\b(?:dating|hookup|adult[\s-]dating)\b',
                r'\b(?:adult[\s-]service|escort)\b'
            ],
            
            # Content warnings
            'warnings': [
                r'\b(?:explicit[\s-]content|adult[\s-]material)\b',
                r'\b(?:mature[\s-]content|mature[\s-]audience)\b',
                r'(?:warning|caution)(?:\s+|\:).*adult'
            ]
        }
        
        # Convert content to lowercase for case-insensitive matching
        content = content.lower()
        
        # Check each category of patterns
        for category, patterns in adult_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"Adult content detected: {category} pattern matched")
                    return True
        
        return False

    def _extract_url_from_title(self, title: str) -> str:
        """Extract URL from browser window title"""
        try:
            if not title or len(title) < 3:  # Skip empty or very short titles
                return None

            # Common patterns for URLs in browser titles
            patterns = [
                r'https?://[^\s\-]+',  # Direct URL
                r'(?:[\s\-])((?:www\.)?[a-zA-Z0-9\-]+\.(?:com|org|net|edu|gov|mil|biz|info|io|co|uk|us|ca|au|de|jp|fr|it|es|nl|ru|br|in)[^\s\-]*)',  # Domain with common TLDs
                r'(?:[\s\-])((?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',  # Domain after space/dash
            ]
            
            title_lower = title.lower()
            
            # Skip if it's just a browser name or common non-URL title
            skip_terms = ['google chrome', 'mozilla firefox', 'microsoft edge', 
                         'new tab', 'blank page', 'settings', 'history']
            if any(term in title_lower for term in skip_terms):
                return None
            
            # Try to find URL in title
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    url = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    # Add https if no protocol specified
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    return url
            
            return None
        except Exception as e:
            print(f"Error extracting URL from title: {e}")
            return None
    
    def _show_block_screen(self, url: str):
        """Show block screen"""
        try:
            from src.ui.blkScrn import BlockScreen
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            # Get the main application instance
            app = QApplication.instance()
            if not app:
                return  # We should only show block screen when main app is running
            
            # Create block screen in the main thread using a timer
            def show_block_screen():
                try:
                    # Create and show block screen
                    block_screen = BlockScreen(self.user_email)
                    if hasattr(block_screen, 'blkRsn_lbl'):
                        block_screen.blkRsn_lbl.setText(f"Blocked URL: {url}")
                        block_screen.blkRsn_lbl.show()  # Make sure it's visible
                    block_screen.exec_()  # Show modal dialog
                except Exception as e:
                    print(f"Error creating block screen: {e}")
            
            # Use a QTimer to ensure we run in the main thread
            QTimer.singleShot(0, show_block_screen)
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
    
    def _get_block_settings(self) -> dict:
        """Get blocking settings from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get settings
                settings = {}
                cursor.execute(
                    "SELECT setting_name, setting_value FROM user_settings WHERE user_email = ?",
                    (self.user_email,)
                )
                
                for name, value in cursor.fetchall():
                    settings[name] = value
                
                return {
                    'message': settings.get('blockMessage', 'Access Blocked'),
                    'countdown': int(settings.get('countdownDuration', '60')),
                    'redirect_url': settings.get('redirectUrl', 'https://www.google.com')
                }
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {
                'message': 'Access Blocked',
                'countdown': 60,
                'redirect_url': 'https://www.google.com'
            }
    
    def _start_signal_file_monitoring(self):
        """Monitor signal file for block triggers"""
        def monitor_signal_file():
            signal_file = os.path.join(tempfile.gettempdir(), 'blockerhero_signal.json')
            last_modified = 0
            
            while self.is_running:
                try:
                    if os.path.exists(signal_file):
                        current_modified = os.path.getmtime(signal_file)
                        if current_modified > last_modified:
                            last_modified = current_modified
                            
                            with open(signal_file, 'r') as f:
                                signal_data = json.load(f)
                            
                            # Process the signal
                            self._process_block_signal(signal_data)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error monitoring signal file: {e}")
                    time.sleep(5)
        
        self.signal_file_monitor = threading.Thread(target=monitor_signal_file, daemon=True)
        self.signal_file_monitor.start()
    
    def _process_block_signal(self, signal_data: Dict):
        """Process a block signal"""
        try:
            print(f"Processing block signal: {signal_data['url']}")
            # Here you would communicate with the main PyQt application
            # This could be through Qt signals, shared memory, named pipes, etc.
            
        except Exception as e:
            print(f"Error processing block signal: {e}")

# Integration function for the main application
def setup_content_blocking_service(main_window):
    """Setup the content blocking service in the main window"""
    
    def start_service():
        if not hasattr(main_window, 'content_blocking_service'):
            main_window.content_blocking_service = ContentBlockerService(
                main_window.db.db_path, 
                main_window.user_email
            )
        
        main_window.content_blocking_service.start_all_monitoring()
    
    def stop_service():
        if hasattr(main_window, 'content_blocking_service'):
            main_window.content_blocking_service.stop_all_monitoring()
    
    # Connect to the adult content blocking setting
    def on_adult_content_setting_changed(checked):
        if checked:
            start_service()
        else:
            stop_service()
    
    # Connect to the toggle switch
    if hasattr(main_window, 'checkBox_toggle'):
        main_window.checkBox_toggle.toggled.connect(on_adult_content_setting_changed)
    
    # Start service if adult content blocking is enabled
    adult_blocking_enabled = main_window.db.get_setting(main_window.user_email, 'checkBox')
    if adult_blocking_enabled:
        start_service()
    
    # Add cleanup on window close
    original_close_event = main_window.closeEvent
    
    def enhanced_close_event(event):
        stop_service()
        original_close_event(event)
    
    main_window.closeEvent = enhanced_close_event

if __name__ == "__main__":
    # Test the service
    import sys
    
    if len(sys.argv) > 2:
        database_path = sys.argv[1]
        user_email = sys.argv[2]
        
        service = ContentBlockerService(database_path, user_email)
        service.start_all_monitoring()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping service...")
            service.stop_all_monitoring()
    else:
        print("Usage: python browser_integration.py <database_path> <user_email>")
        print("This script provides browser integration for BlockerHero content filtering.")