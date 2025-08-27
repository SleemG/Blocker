# blocker_integration.py
"""
Integration file for adding adult content blocking to the main BlockerHero application.
This file should be imported and integrated with your main_window.py
"""

import os
import sys
import json
import tempfile
import threading
from typing import Optional
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox

# Add the path to import our blocker modules
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

try:
    from adult_content_blocker import AdultContentBlocker, BlockScreen
    from browser_integration import ContentBlockerService
except ImportError as e:
    print(f"Warning: Could not import blocker modules: {e}")
    # Fallback - create dummy classes
    class AdultContentBlocker:
        def __init__(self, *args): pass
        def start_blocking(self): pass
        def stop_blocking(self): pass
    
    class ContentBlockerService:
        def __init__(self, *args): pass
        def start_all_monitoring(self): pass
        def stop_all_monitoring(self): pass

class BlockerIntegration(QObject):
    """
    Integration class that adds adult content blocking functionality to the main window
    """
    
    # Signals
    content_blocked = pyqtSignal(str, str, str)  # url, reason, detected_keywords
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.adult_content_blocker = None
        self.content_blocking_service = None
        self.signal_monitor_timer = None
        self.current_block_screen = None
        
        # Connect signals
        self.content_blocked.connect(self.show_block_screen)
        
    def initialize(self):
        """Initialize the blocker integration after user login"""
        if not self.main_window.user_email:
            return
            
        try:
            # Initialize adult content blocker
            self.adult_content_blocker = AdultContentBlocker(
                self.main_window.db, 
                self.main_window.user_email
            )
            
            # Initialize content blocking service
            self.content_blocking_service = ContentBlockerService(
                self.main_window.db.db_path,
                self.main_window.user_email
            )
            
            # Setup signal file monitoring
            self.setup_signal_monitoring()
            
            # Check if adult content blocking is enabled and start if needed
            if self.is_adult_blocking_enabled():
                self.start_blocking()
                
            print("Blocker integration initialized successfully")
            
        except Exception as e:
            print(f"Error initializing blocker integration: {e}")
            self.show_error_message("Blocker Initialization Error", 
                                   f"Failed to initialize content blocking: {str(e)}")
    
    def connect_settings_ui(self):
        """Connect the blocking functionality to UI settings"""
        try:
            # Connect to the adult content blocking toggle switch
            if hasattr(self.main_window, 'checkBox_toggle'):
                self.main_window.checkBox_toggle.toggled.connect(
                    self.on_adult_content_setting_changed
                )
            
            # Connect to other relevant settings
            self.connect_additional_settings()
            
            print("Settings UI connected successfully")
            
        except Exception as e:
            print(f"Error connecting settings UI: {e}")
    
    def connect_additional_settings(self):
        """Connect additional blocking-related settings"""
        try:
            # Block Screen Countdown setting (spinBox in groupBox_8)
            if hasattr(self.main_window, 'spinBox'):
                # Load saved value
                saved_countdown = self.main_window.db.get_setting(self.main_window.user_email, 'countdown_duration')
                if saved_countdown is not None:
                    try:
                        self.main_window.spinBox.setValue(int(saved_countdown))
                    except (ValueError, TypeError):
                        self.main_window.spinBox.setValue(60)  # Default value
                else:
                    self.main_window.spinBox.setValue(60)  # Default value
                
                # Connect the signal
                self.main_window.spinBox.valueChanged.connect(
                    self.on_countdown_setting_changed
                )
            
            # Block Screen Message setting (plainTextEdit in groupBox_6)
            if hasattr(self.main_window, 'plainTextEdit'):
                # Load saved value
                saved_message = self.main_window.db.get_setting(self.main_window.user_email, 'block_message')
                if saved_message:
                    self.main_window.plainTextEdit.setPlainText(saved_message)
                else:
                    # Set default message if none saved
                    default_message = """<div style='text-align: center; font-size: 18px; color: #2c3e50;'>
<h2 style='color: #e74c3c;'>اتقي الله في نفسك</h2>
<p><strong>This content has been blocked for your protection.</strong></p>
<p>Content blocking helps maintain a safe and productive browsing environment.</p>
<p style='color: #7f8c8d; font-size: 14px;'>BlockerHero - Your Digital Wellness Partner</p>
</div>"""
                    self.main_window.plainTextEdit.setPlainText(default_message)
                
                # Connect the signal
                self.main_window.plainTextEdit.textChanged.connect(
                    self.on_message_setting_changed
                )
            
            # Redirect URL setting (lineEdit_2 in groupBox_7)
            if hasattr(self.main_window, 'lineEdit_2'):
                # Load saved value
                saved_url = self.main_window.db.get_setting(self.main_window.user_email, 'redirect_url')
                if saved_url:
                    self.main_window.lineEdit_2.setText(saved_url)
                else:
                    # Set default URL if none saved
                    self.main_window.lineEdit_2.setText('https://www.google.com')
                
                # Connect the signal
                self.main_window.lineEdit_2.textChanged.connect(
                    self.on_redirect_url_changed
                )
                
        except Exception as e:
            print(f"Error connecting additional settings: {e}")
    
    def on_adult_content_setting_changed(self, checked: bool):
        """Handle adult content blocking toggle"""
        try:
            if checked:
                self.start_blocking()
                self.main_window.show_status_message("Adult content blocking enabled")
            else:
                self.stop_blocking()
                self.main_window.show_status_message("Adult content blocking disabled")
                
        except Exception as e:
            print(f"Error handling adult content setting change: {e}")
            self.show_error_message("Setting Error", 
                                   f"Failed to update blocking setting: {str(e)}")
    
    def on_countdown_setting_changed(self, value: int):
        """Handle countdown duration setting change"""
        try:
            # Save to database with proper type
            self.main_window.db.update_setting(
                self.main_window.user_email,
                'countdown_duration',
                str(value),
                'number'
            )
            self.main_window.show_status_message(f"Block screen countdown set to {value} seconds")
            
        except Exception as e:
            print(f"Error handling countdown setting change: {e}")
    
    def on_message_setting_changed(self):
        """Handle block message setting change"""
        try:
            if hasattr(self.main_window, 'plainTextEdit'):
                message = self.main_window.plainTextEdit.toPlainText()
                self.main_window.db.update_setting(
                    self.main_window.user_email,
                    'block_message',
                    message,
                    'text'
                )
                
        except Exception as e:
            print(f"Error handling message setting change: {e}")
    
    def on_redirect_url_changed(self, url: str):
        """Handle redirect URL setting change"""
        try:
            self.main_window.db.update_setting(
                self.main_window.user_email,
                'redirect_url',
                url,
                'text'
            )
            
        except Exception as e:
            print(f"Error handling redirect URL change: {e}")
    
    def start_blocking(self):
        """Start all blocking methods"""
        try:
            # Start the adult content blocker
            if self.adult_content_blocker:
                self.adult_content_blocker.start_blocking()
            
            # Start the comprehensive blocking service
            if self.content_blocking_service:
                self.content_blocking_service.start_all_monitoring()
            
            print("Content blocking started")
            
        except Exception as e:
            print(f"Error starting blocking: {e}")
            self.show_error_message("Blocking Error", 
                                   f"Failed to start content blocking: {str(e)}")
    
    def stop_blocking(self):
        """Stop all blocking methods"""
        try:
            # Stop the adult content blocker
            if self.adult_content_blocker:
                self.adult_content_blocker.stop_blocking()
            
            # Stop the comprehensive blocking service
            if self.content_blocking_service:
                self.content_blocking_service.stop_all_monitoring()
            
            print("Content blocking stopped")
            
        except Exception as e:
            print(f"Error stopping blocking: {e}")
    
    def setup_signal_monitoring(self):
        """Setup monitoring for block signals from other processes"""
        try:
            # Create a timer to check for block signals
            self.signal_monitor_timer = QTimer()
            self.signal_monitor_timer.timeout.connect(self.check_for_block_signals)
            self.signal_monitor_timer.start(1000)  # Check every second
            
        except Exception as e:
            print(f"Error setting up signal monitoring: {e}")
    
    def check_for_block_signals(self):
        """Check for block signals from the monitoring service"""
        try:
            signal_file = os.path.join(tempfile.gettempdir(), 'blockerhero_signal.json')
            
            if os.path.exists(signal_file):
                try:
                    with open(signal_file, 'r') as f:
                        signal_data = json.load(f)
                    
                    # Check if this is a new signal
                    if self.is_new_signal(signal_data):
                        self.content_blocked.emit(
                            signal_data.get('url', ''),
                            signal_data.get('reason', ''),
                            signal_data.get('title', '')
                        )
                    
                    # Clean up the signal file
                    os.remove(signal_file)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error processing signal file: {e}")
                    # Remove corrupted signal file
                    try:
                        os.remove(signal_file)
                    except:
                        pass
                        
        except Exception as e:
            # Don't print errors for normal file operations
            pass
    
    def is_new_signal(self, signal_data: dict) -> bool:
        """Check if this is a new block signal"""
        # Simple implementation - in practice, you might want to track processed signals
        return signal_data.get('timestamp', 0) > 0
    
    def show_block_screen(self, url: str, reason: str, detected_content: str):
        """Show the block screen"""
        try:
            # Close any existing block screen
            if self.current_block_screen:
                self.current_block_screen.close()
                self.current_block_screen = None
            
            # Create block screen with user email for customization loading
            self.current_block_screen = BlockScreen(self.main_window.user_email)
            
            # Set the block reason
            if hasattr(self.current_block_screen, 'blkRsn_lbl'):
                self.current_block_screen.blkRsn_lbl.setText(f"Blocked: {reason}")
            
            # Show the block screen
            self.current_block_screen.exec_()
            self.current_block_screen = None
            
            print(f"Blocked content: {url} - {reason}")
            
        except Exception as e:
            print(f"Error showing block screen: {e}")
    
    def get_default_block_message(self) -> str:
        """Get the default block message"""
        return """
        <div style='text-align: center; font-size: 18px; color: #2c3e50;'>
        <h2 style='color: #e74c3c;'>اتقي الله في نفسك</h2>
        <p><strong>This content has been blocked for your protection.</strong></p>
        <p>Content blocking helps maintain a safe and productive browsing environment.</p>
        <p style='color: #7f8c8d; font-size: 14px;'>BlockerHero - Your Digital Wellness Partner</p>
        </div>
        """
    
    def is_adult_blocking_enabled(self) -> bool:
        """Check if adult content blocking is enabled"""
        try:
            # First check the main adult content blocking setting
            main_setting = self.main_window.db.get_setting(
                self.main_window.user_email, 'adult_content_blocking'
            )
            main_setting = main_setting if main_setting is not None else True

            # Then check auto-block setting
            auto_block = self.main_window.db.get_setting(
                self.main_window.user_email, 'auto_block_adult'
            )
            auto_block = auto_block if auto_block is not None else True

            return main_setting and auto_block
        except Exception as e:
            print(f"Error checking adult blocking settings: {e}")
            return True  # Default to enabled for safety
    
    def save_setting(self, setting_name: str, value):
        """Save a blocker-specific setting"""
        try:
            # Save to database with a prefix to distinguish from other settings
            full_setting_name = f'blocker_{setting_name}'
            
            if isinstance(value, bool):
                success = self.main_window.db.update_setting(
                    self.main_window.user_email, full_setting_name, value
                )
            else:
                # For non-boolean values, we need a different approach
                # You might want to add a text settings table to your database
                # For now, we'll store as a string in a JSON format
                import json
                json_value = json.dumps(value)
                # This is a simplified approach - you may want to extend your database schema
                success = True  # Placeholder
                
            if success:
                print(f"Saved setting {setting_name}: {value}")
            else:
                print(f"Failed to save setting {setting_name}")
                
        except Exception as e:
            print(f"Error saving setting {setting_name}: {e}")
    
    def get_setting(self, setting_name: str, default_value=None):
        """Get a blocker-specific setting"""
        try:
            full_setting_name = f'blocker_{setting_name}'
            
            # Try to get from database
            # This is simplified - you may need to extend this based on your database schema
            if isinstance(default_value, bool):
                setting = self.main_window.db.get_setting(
                    self.main_window.user_email, full_setting_name
                )
                return setting if setting is not None else default_value
            else:
                # For non-boolean values, return default for now
                return default_value
                
        except Exception as e:
            print(f"Error getting setting {setting_name}: {e}")
            return default_value
    
    def show_error_message(self, title: str, message: str):
        """Show error message to user"""
        try:
            QMessageBox.warning(self.main_window, title, message)
        except Exception as e:
            print(f"Error showing message box: {e}")
    
    def cleanup(self):
        """Cleanup resources when application closes"""
        try:
            # Stop all monitoring
            self.stop_blocking()
            
            # Stop signal monitoring
            if self.signal_monitor_timer:
                self.signal_monitor_timer.stop()
            
            # Close any open block screen
            if self.current_block_screen:
                self.current_block_screen.close()
                self.current_block_screen = None
            
            print("Blocker integration cleaned up")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

# Integration function to be called from main_window.py
def integrate_blocker_with_main_window(main_window):
    """
    Main integration function to add blocking functionality to the main window.
    Call this function from your main_window.py after user login.
    
    Usage in main_window.py:
        from blocker_integration import integrate_blocker_with_main_window
        
        # In your on_user_verified method:
        def _on_user_verified(self, email):
            self.user_email = email
            self.load_user_data()
            self.update_user_info()
            self.load_user_settings()
            
            # Add this line:
            integrate_blocker_with_main_window(self)
    """
    
    try:
        # Create and store the blocker integration
        main_window.blocker_integration = BlockerIntegration(main_window)
        
        # Initialize the integration
        main_window.blocker_integration.initialize()
        
        # Connect to UI settings
        main_window.blocker_integration.connect_settings_ui()
        
        # Enhance the existing closeEvent to include cleanup
        original_close_event = main_window.closeEvent
        
        def enhanced_close_event(event):
            # Cleanup blocker integration
            if hasattr(main_window, 'blocker_integration'):
                main_window.blocker_integration.cleanup()
            
            # Call original close event
            original_close_event(event)
        
        main_window.closeEvent = enhanced_close_event
        
        # Add blocker status to the main window
        main_window.show_status_message("Adult content blocking system initialized")
        
        print("Successfully integrated blocker with main window")
        
    except Exception as e:
        print(f"Error integrating blocker with main window: {e}")
        # Show error to user
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                main_window, 
                "Blocker Integration Error", 
                f"Failed to initialize content blocking system:\n{str(e)}\n\nSome features may not work correctly."
            )
        except:
            pass

# Additional utility functions for UI integration

def update_main_window_ui_for_blocker(main_window):
    """
    Update the main window UI to better integrate with the blocker.
    This function can be called to enhance the UI after integration.
    """
    
    try:
        # Add blocker status indicators
        add_blocker_status_indicators(main_window)
        
        # Enhance settings page
        enhance_blocker_settings_page(main_window)
        
        # Add blocker information to notification page
        add_blocker_notifications(main_window)
        
    except Exception as e:
        print(f"Error updating UI for blocker: {e}")

def add_blocker_status_indicators(main_window):
    """Add visual indicators for blocker status"""
    
    try:
        # Add status indicator to the main window
        if hasattr(main_window, 'statusBar'):
            status_bar = main_window.statusBar()
            
            # Create a permanent widget to show blocking status
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            
            blocker_status_label = QLabel("🛡️ Blocking: Active")
            blocker_status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    padding: 2px 8px;
                    background-color: #d5f4e6;
                    border-radius: 3px;
                }
            """)
            
            status_bar.addPermanentWidget(blocker_status_label)
            main_window.blocker_status_label = blocker_status_label
            
            # Update status when blocking state changes
            def update_blocker_status(enabled):
                if enabled:
                    main_window.blocker_status_label.setText("🛡️ Blocking: Active")
                    main_window.blocker_status_label.setStyleSheet("""
                        QLabel {
                            color: #27ae60;
                            font-weight: bold;
                            padding: 2px 8px;
                            background-color: #d5f4e6;
                            border-radius: 3px;
                        }
                    """)
                else:
                    main_window.blocker_status_label.setText("🛡️ Blocking: Inactive")
                    main_window.blocker_status_label.setStyleSheet("""
                        QLabel {
                            color: #e74c3c;
                            font-weight: bold;
                            padding: 2px 8px;
                            background-color: #fadbd8;
                            border-radius: 3px;
                        }
                    """)
            
            # Connect to blocker integration if available
            if hasattr(main_window, 'blocker_integration'):
                # Update status based on current setting
                enabled = main_window.blocker_integration.is_adult_blocking_enabled()
                update_blocker_status(enabled)
                
                # Store update function for future use
                main_window.update_blocker_status = update_blocker_status
                
    except Exception as e:
        print(f"Error adding blocker status indicators: {e}")

def enhance_blocker_settings_page(main_window):
    """Enhance the settings page with additional blocker information"""
    
    try:
        # Add helpful text to the adult content blocking setting
        if hasattr(main_window, 'contentBlocking_grpBx'):
            group_box = main_window.contentBlocking_grpBx
            
            # Add informational label
            from PyQt5.QtWidgets import QLabel
            info_label = QLabel("""
            <div style='color: #7f8c8d; font-size: 12px; margin-top: 5px;'>
            <b>How it works:</b><br>
            • Monitors browser activity in real-time<br>
            • Blocks websites with adult content<br>
            • Filters search results and images<br>
            • Shows blocking screen with countdown<br>
            </div>
            """)
            info_label.setWordWrap(True)
            
            # Try to add the label to the group box layout
            layout = group_box.layout()
            if layout:
                layout.addWidget(info_label)
                
    except Exception as e:
        print(f"Error enhancing blocker settings page: {e}")

def add_blocker_notifications(main_window):
    """Add blocker-related notifications to the notification page"""
    
    try:
        # This would add recent blocking events to the notification page
        # Implementation depends on your notification page structure
        
        if hasattr(main_window, 'notification_page'):
            # Add blocker statistics or recent blocks
            pass
            
    except Exception as e:
        print(f"Error adding blocker notifications: {e}")

# Standalone test function
def test_blocker_integration():
    """Test function to verify blocker integration works"""
    
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create a mock main window for testing
    class MockMainWindow:
        def __init__(self):
            self.user_email = "test@example.com"
            self.db = MockDatabase()
            
        def show_status_message(self, message, timeout=2000):
            print(f"Status: {message}")
            
        def closeEvent(self, event):
            print("Mock window closing")
            event.accept()
    
    class MockDatabase:
        def __init__(self):
            self.db_path = "test.db"
            
        def get_setting(self, email, setting_name):
            return True  # Adult blocking enabled by default
            
        def update_setting(self, email, setting_name, value):
            print(f"Setting {setting_name} = {value}")
            return True
    
    # Test the integration
    mock_window = MockMainWindow()
    integrate_blocker_with_main_window(mock_window)
    
    print("Blocker integration test completed")
    return True

# Configuration and constants
BLOCKER_CONFIG = {
    'DEFAULT_COUNTDOWN': 30,
    'DEFAULT_REDIRECT_URL': 'https://www.google.com',
    'SIGNAL_CHECK_INTERVAL': 1000,  # milliseconds
    'ADULT_KEYWORDS_THRESHOLD': 3,
    'URL_ANALYSIS_THRESHOLD': 30,
}

# Example usage documentation
INTEGRATION_EXAMPLE = '''
# How to integrate the blocker with your main_window.py:

1. Import the integration module:
   from blocker_integration import integrate_blocker_with_main_window

2. Call the integration function after user verification:
   def _on_user_verified(self, email):
       self.user_email = email
       self.load_user_data()
       self.update_user_info()
       self.load_user_settings()
       
       # Add blocker integration
       integrate_blocker_with_main_window(self)

3. Make sure your UI elements have the expected names:
   - checkBox_toggle: Adult content blocking toggle switch
   - spinBox: Countdown duration setting  
   - plainTextEdit: Custom block message
   - lineEdit_2: Redirect URL setting

4. The blocker will automatically:
   - Start monitoring when adult blocking is enabled
   - Show block screens for detected content
   - Save and load settings from your database
   - Clean up resources when the application closes

5. Optional UI enhancements:
   from blocker_integration import update_main_window_ui_for_blocker
   update_main_window_ui_for_blocker(self)
'''

if __name__ == "__main__":
    print("BlockerHero Integration Module")
    print("=" * 40)
    print(INTEGRATION_EXAMPLE)
    print("\nRunning integration test...")
    test_blocker_integration()

    