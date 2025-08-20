"""
Content Blocker Integration Module
Handles integration between the UI and the adult content blocker
"""

from PyQt5.QtCore import QObject, pyqtSignal
from .adult_content_blocker import (get_blocker_instance, start_content_blocking, 
                                  stop_content_blocking, is_content_blocking_active)


class ContentBlockerIntegration(QObject):
    """Integration class for content blocker with UI"""
    
    status_changed = pyqtSignal(bool)  # Emitted when blocker status changes
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.blocker = get_blocker_instance()
        self.setup_ui_connections()
        self.load_settings()
        
    def setup_ui_connections(self):
        """Setup connections between UI elements and content blocker"""
        try:
            # Connect the adult content blocking checkbox
            if hasattr(self.main_window, 'checkBox'):  # The "Block Adult Content" checkbox
                self.main_window.checkBox.toggled.connect(self.on_adult_content_toggle)
                print("Connected adult content blocking checkbox")
                
            # Connect settings changes
            if hasattr(self.main_window, 'spinBox'):
                self.main_window.spinBox.valueChanged.connect(self.update_blocker_settings)
                print("Connected countdown spinbox")
                
            if hasattr(self.main_window, 'lineEdit_2'):
                self.main_window.lineEdit_2.textChanged.connect(self.update_blocker_settings)
                print("Connected redirect URL field")
                
            if hasattr(self.main_window, 'plainTextEdit'):
                self.main_window.plainTextEdit.textChanged.connect(self.update_blocker_settings)
                print("Connected block message field")
                
            # Update the blocker with current UI settings
            self.update_blocker_settings()
            
        except Exception as e:
            print(f"Error setting up content blocker UI connections: {e}")
            
    def on_adult_content_toggle(self, checked):
        """Handle adult content blocking checkbox toggle"""
        try:
            if checked:
                # Update blocker settings before starting
                self.update_blocker_settings()
                start_content_blocking()
                print("✅ Adult content blocking enabled")
            else:
                stop_content_blocking()
                print("❌ Adult content blocking disabled")
                
            self.status_changed.emit(checked)
            
        except Exception as e:
            print(f"Error toggling adult content blocking: {e}")
            
    def update_blocker_settings(self):
        """Update blocker settings from UI"""
        try:
            # Update countdown time from spinBox
            if hasattr(self.main_window, 'spinBox'):
                countdown_time = self.main_window.spinBox.value()
                self.blocker.default_countdown = countdown_time
                print(f"Updated countdown time: {countdown_time} seconds")
                
            # Update redirect URL from lineEdit_2
            if hasattr(self.main_window, 'lineEdit_2'):
                redirect_url = self.main_window.lineEdit_2.text()
                if redirect_url:
                    self.blocker.default_redirect_url = redirect_url
                    print(f"Updated redirect URL: {redirect_url}")
                    
            # Update block message from plainTextEdit
            if hasattr(self.main_window, 'plainTextEdit'):
                block_message = self.main_window.plainTextEdit.toPlainText()
                if block_message:
                    self.blocker.default_block_message = block_message
                    print("Updated block message")
                    
        except Exception as e:
            print(f"Error updating blocker settings: {e}")
            
    def load_settings(self):
        """Load saved settings and apply them"""
        try:
            # Check if adult content blocking should be enabled by default
            if hasattr(self.main_window, 'checkBox'):
                is_checked = self.main_window.checkBox.isChecked()
                if is_checked:
                    self.update_blocker_settings()
                    start_content_blocking()
                    print("Auto-started content blocking (checkbox was checked)")
                    
        except Exception as e:
            print(f"Error loading content blocker settings: {e}")
            
    def get_status(self):
        """Get current blocking status"""
        return is_content_blocking_active()
        
    def enable_blocking(self):
        """Enable content blocking"""
        if hasattr(self.main_window, 'checkBox'):
            self.main_window.checkBox.setChecked(True)
        else:
            self.on_adult_content_toggle(True)
            
    def disable_blocking(self):
        """Disable content blocking"""
        if hasattr(self.main_window, 'checkBox'):
            self.main_window.checkBox.setChecked(False)
        else:
            self.on_adult_content_toggle(False)
            
    def get_block_logs(self, limit=100):
        """Get recent block logs"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.blocker.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, content_type, content_source, block_reason, app_name
                FROM block_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            logs = cursor.fetchall()
            conn.close()
            return logs
        except Exception as e:
            print(f"Error getting block logs: {e}")
            return []
            
    def clear_block_logs(self):
        """Clear all block logs"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.blocker.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM block_logs')
            conn.commit()
            conn.close()
            print("Block logs cleared")
        except Exception as e:
            print(f"Error clearing block logs: {e}")


def setup_content_blocker_integration(main_window):
    """Setup content blocker integration for the main window"""
    try:
        integration = ContentBlockerIntegration(main_window)
        main_window.content_blocker_integration = integration
        print("🛡️ Content blocker integration setup complete")
        return integration
    except Exception as e:
        print(f"Error setting up content blocker integration: {e}")
        return None