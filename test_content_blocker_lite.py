#!/usr/bin/env python3
"""
Lightweight Test Application for Adult Content Blocker
This version avoids heavy dependencies and focuses on core functionality.
"""

import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QCheckBox, QSpinBox, QLineEdit, QPlainTextEdit, 
                           QLabel, QPushButton, QGroupBox, QTabWidget, QTextEdit,
                           QMessageBox, QListWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Import the optimized content blocker
try:
    from src.utils.adult_content_blocker_optimized import (
        get_optimized_blocker_instance, 
        start_optimized_content_blocking, 
        stop_optimized_content_blocking, 
        is_optimized_content_blocking_active,
        OptimizedBlockScreen
    )
    BLOCKER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Could not import optimized content blocker: {e}")
    print("Make sure the file src/utils/adult_content_blocker_optimized.py exists")
    BLOCKER_AVAILABLE = False


class LiteContentBlockerIntegration:
    """Lightweight integration for content blocker"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        if BLOCKER_AVAILABLE:
            self.blocker = get_optimized_blocker_instance()
        else:
            self.blocker = None
        self.setup_ui_connections()
        
    def setup_ui_connections(self):
        """Setup UI connections"""
        try:
            if hasattr(self.main_window, 'checkBox') and self.blocker:
                self.main_window.checkBox.toggled.connect(self.on_adult_content_toggle)
                
            if hasattr(self.main_window, 'spinBox') and self.blocker:
                self.main_window.spinBox.valueChanged.connect(self.update_blocker_settings)
                
            if hasattr(self.main_window, 'lineEdit_2') and self.blocker:
                self.main_window.lineEdit_2.textChanged.connect(self.update_blocker_settings)
                
            if hasattr(self.main_window, 'plainTextEdit') and self.blocker:
                self.main_window.plainTextEdit.textChanged.connect(self.update_blocker_settings)
                
            self.update_blocker_settings()
            
        except Exception as e:
            print(f"Error setting up connections: {e}")
            
    def on_adult_content_toggle(self, checked):
        """Handle toggle"""
        if not self.blocker:
            return
            
        try:
            if checked:
                self.update_blocker_settings()
                start_optimized_content_blocking()
                print("✅ Content blocking enabled")
            else:
                stop_optimized_content_blocking()
                print("❌ Content blocking disabled")
        except Exception as e:
            print(f"Error toggling: {e}")
            
    def update_blocker_settings(self):
        """Update settings"""
        if not self.blocker:
            return
            
        try:
            if hasattr(self.main_window, 'spinBox'):
                self.blocker.default_countdown = self.main_window.spinBox.value()
                
            if hasattr(self.main_window, 'lineEdit_2'):
                url = self.main_window.lineEdit_2.text()
                if url:
                    self.blocker.default_redirect_url = url
                    
            if hasattr(self.main_window, 'plainTextEdit'):
                message = self.main_window.plainTextEdit.toPlainText()
                if message:
                    self.blocker.default_block_message = message
        except Exception as e:
            print(f"Error updating settings: {e}")
            
    def get_status(self):
        """Get status"""
        if self.blocker:
            return is_optimized_content_blocking_active()
        return False
        
    def get_block_logs(self, limit=50):
        """Get logs"""
        if not self.blocker:
            return []
            
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
            print(f"Error getting logs: {e}")
            return []


class LiteTestMainWindow(QMainWindow):
    """Lightweight test window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adult Content Blocker - Lite Test")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
        self.setup_content_blocker()
        self.setup_status_updates()
        
    def setup_ui(self):
        """Setup UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)
        
        self.create_control_tab()
        self.create_testing_tab()
        
    def create_control_tab(self):
        """Create control tab"""
        control_tab = QWidget()
        self.tab_widget.addTab(control_tab, "Controls")
        
        layout = QVBoxLayout(control_tab)
        
        # Title
        title = QLabel("Adult Content Blocker - Lite Version")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Status
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        if BLOCKER_AVAILABLE:
            status_text = "✅ Content blocker loaded successfully"
            status_color = "#27ae60"
        else:
            status_text = "❌ Content blocker not available"
            status_color = "#e74c3c"
            
        system_status = QLabel(status_text)
        system_status.setStyleSheet(f"color: {status_color}; font-weight: bold; padding: 10px;")
        status_layout.addWidget(system_status)
        
        self.status_label = QLabel("Status: Content blocking disabled")
        self.status_label.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Controls
        controls_group = QGroupBox("Content Blocking Settings")
        controls_layout = QVBoxLayout(controls_group)
        
        # Main checkbox
        self.checkBox = QCheckBox("Block Adult Content")
        self.checkBox.setChecked(False)
        self.checkBox.setStyleSheet("font-size: 14px; padding: 5px;")
        controls_layout.addWidget(self.checkBox)
        
        # Settings
        settings_layout = QVBoxLayout()
        
        # Countdown
        countdown_layout = QHBoxLayout()
        countdown_layout.addWidget(QLabel("Countdown:"))
        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(60)
        self.spinBox.setValue(10)
        self.spinBox.setSuffix(" sec")
        countdown_layout.addWidget(self.spinBox)
        countdown_layout.addStretch()
        settings_layout.addLayout(countdown_layout)
        
        # Redirect URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Redirect URL:"))
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setText("https://google.com")
        url_layout.addWidget(self.lineEdit_2)
        settings_layout.addLayout(url_layout)
        
        # Message
        settings_layout.addWidget(QLabel("Block Message:"))
        self.plainTextEdit = QPlainTextEdit()
        self.plainTextEdit.setPlainText("🚫 Content Blocked\n\nThis content has been blocked for your protection.")
        self.plainTextEdit.setMaximumHeight(80)
        settings_layout.addWidget(self.plainTextEdit)
        
        controls_layout.addLayout(settings_layout)
        layout.addWidget(controls_group)
        
        layout.addStretch()
        
    def create_testing_tab(self):
        """Create testing tab"""
        test_tab = QWidget()
        self.tab_widget.addTab(test_tab, "Testing")
        
        layout = QVBoxLayout(test_tab)
        
        # Test buttons
        test_group = QGroupBox("Test Functions")
        test_layout = QVBoxLayout(test_group)
        
        # Test block screen
        self.test_block_btn = QPushButton("🚫 Test Block Screen")
        self.test_block_btn.clicked.connect(self.test_block_screen)
        self.test_block_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        test_layout.addWidget(self.test_block_btn)
        
        # Test keyword detection
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("Test Text:"))
        self.test_text_input = QLineEdit()
        self.test_text_input.setPlaceholderText("Enter text to test...")
        keyword_layout.addWidget(self.test_text_input)
        
        self.test_keyword_btn = QPushButton("Test")
        self.test_keyword_btn.clicked.connect(self.test_keyword_detection)
        keyword_layout.addWidget(self.test_keyword_btn)
        
        test_layout.addLayout(keyword_layout)
        layout.addWidget(test_group)
        
        # Results
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Info
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
        <b>Lite Version Features:</b><br>
        • Optimized performance (no heavy dependencies)<br>
        • Essential content blocking functionality<br>
        • Lightweight keyword detection<br>
        • Simple domain blocking<br>
        • Full-screen block screen<br><br>
        <b>Missing in Lite Version:</b><br>
        • Advanced browser integration (Selenium)<br>
        • Full OCR capabilities (optional)<br>
        • Complex web scraping<br><br>
        This version focuses on core functionality without performance issues.
        """)
        info_text.setStyleSheet("color: #34495e; padding: 10px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
    def setup_content_blocker(self):
        """Setup content blocker"""
        try:
            if BLOCKER_AVAILABLE:
                self.content_blocker_integration = LiteContentBlockerIntegration(self)
                self.add_result("✅ Content blocker integration successful")
            else:
                self.content_blocker_integration = None
                self.add_result("❌ Content blocker not available")
        except Exception as e:
            self.add_result(f"❌ Setup error: {e}")
            
    def setup_status_updates(self):
        """Setup status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(3000)  # Every 3 seconds
        
    def update_status(self):
        """Update status"""
        try:
            if self.content_blocker_integration and self.content_blocker_integration.get_status():
                self.status_label.setText("Status: ✅ Content blocking ENABLED")
                self.status_label.setStyleSheet("padding: 10px; background-color: #d5f4e6; color: #27ae60; border-radius: 5px; font-weight: bold;")
            else:
                self.status_label.setText("Status: ❌ Content blocking DISABLED")
                self.status_label.setStyleSheet("padding: 10px; background-color: #fadbd8; color: #e74c3c; border-radius: 5px; font-weight: bold;")
        except:
            pass
            
    def test_block_screen(self):
        """Test block screen"""
        try:
            if not BLOCKER_AVAILABLE:
                self.add_result("❌ Blocker not available")
                return
                
            self.add_result("🧪 Testing block screen...")
            
            # Update settings
            if self.content_blocker_integration:
                self.content_blocker_integration.update_blocker_settings()
                
            # Show test block screen
            blocker = get_optimized_blocker_instance()
            block_screen = OptimizedBlockScreen("Website", "test-site.com", "Adult content detected (TEST)", blocker)
            block_screen.show()
            
            self.add_result("✅ Block screen test initiated")
            
        except Exception as e:
            self.add_result(f"❌ Block screen test error: {e}")
            
    def test_keyword_detection(self):
        """Test keyword detection"""
        try:
            if not BLOCKER_AVAILABLE:
                self.add_result("❌ Blocker not available")
                return
                
            test_text = self.test_text_input.text()
            if not test_text:
                self.add_result("❌ Please enter text to test")
                return
                
            self.add_result(f"🧪 Testing: '{test_text}'")
            
            blocker = get_optimized_blocker_instance()
            contains_adult_content = blocker._contains_adult_content(test_text)
            
            result = "🚫 BLOCKED" if contains_adult_content else "✅ ALLOWED"
            self.add_result(f"   Result: {result}")
            
        except Exception as e:
            self.add_result(f"❌ Test error: {e}")
            
    def add_result(self, text):
        """Add result to display"""
        current_time = time.strftime("%H:%M:%S")
        self.results_text.append(f"[{current_time}] {text}")
        
        # Auto-scroll
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Main function"""
    print("🛡️ Adult Content Blocker - Lite Test Application")
    print("=" * 50)
    
    if BLOCKER_AVAILABLE:
        print("✅ Optimized content blocker loaded successfully")
        print("📋 Features available:")
        print("  • Lightweight keyword detection")
        print("  • Simple domain blocking")
        print("  • Full-screen block screen")
        print("  • Basic application monitoring")
    else:
        print("❌ Content blocker not available")
        print("⚠️  Please check that src/utils/adult_content_blocker_optimized.py exists")
        
    print("\n🚀 Starting lite test application...")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Apply simple styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ecf0f1;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 5px 0;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2c3e50;
        }
    """)
    
    # Create and show window
    window = LiteTestMainWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()