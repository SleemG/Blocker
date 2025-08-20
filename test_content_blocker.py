#!/usr/bin/env python3
"""
Test script for the Adult Content Blocker
This script demonstrates how to use the content blocking system.
"""

import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QCheckBox, QSpinBox, QLineEdit, QPlainTextEdit, 
                           QLabel, QPushButton, QGroupBox, QTabWidget, QTextEdit,
                           QMessageBox, QListWidget, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Import the content blocker
try:
    from src.utils.adult_content_blocker import (get_blocker_instance, start_content_blocking, 
                                               stop_content_blocking, is_content_blocking_active, BlockScreen)
    from src.utils.content_blocker_integration import setup_content_blocker_integration
except ImportError as e:
    print(f"Error: Could not import content blocker: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements_content_blocker.txt")
    sys.exit(1)


class TestMainWindow(QMainWindow):
    """Test window to demonstrate content blocker integration"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adult Content Blocker - Test Interface")
        self.setGeometry(100, 100, 900, 700)
        
        # Create UI elements that match the original UI structure
        self.setup_ui()
        self.setup_content_blocker()
        self.setup_status_updates()
        
    def setup_ui(self):
        """Setup the test UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget to organize interface
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)
        
        # Create main control tab
        self.create_control_tab()
        
        # Create testing tab
        self.create_testing_tab()
        
        # Create logs tab
        self.create_logs_tab()
        
    def create_control_tab(self):
        """Create the main control tab"""
        control_tab = QWidget()
        self.tab_widget.addTab(control_tab, "Content Blocking Controls")
        
        layout = QVBoxLayout(control_tab)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Adult Content Blocker Control Panel")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Content blocking section
        blocking_group = QGroupBox("Content Blocking Settings")
        blocking_layout = QVBoxLayout(blocking_group)
        
        # Content blocking checkbox (matches UI: checkBox)
        self.checkBox = QCheckBox("Block Adult Content")
        self.checkBox.setChecked(True)
        self.checkBox.setStyleSheet("font-size: 14px; padding: 5px;")
        blocking_layout.addWidget(self.checkBox)
        
        layout.addWidget(blocking_group)
        
        # Block screen customization section
        screen_group = QGroupBox("Block Screen Customization")
        screen_layout = QVBoxLayout(screen_group)
        
        # Countdown spinbox (matches UI: spinBox)
        countdown_layout = QHBoxLayout()
        countdown_layout.addWidget(QLabel("Block Screen Countdown:"))
        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(300)
        self.spinBox.setValue(10)
        self.spinBox.setSuffix(" seconds")
        countdown_layout.addWidget(self.spinBox)
        countdown_layout.addStretch()
        screen_layout.addLayout(countdown_layout)
        
        # Redirect URL (matches UI: lineEdit_2)
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Redirect URL:"))
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setText("https://google.com")
        self.lineEdit_2.setPlaceholderText("https://google.com")
        url_layout.addWidget(self.lineEdit_2)
        screen_layout.addLayout(url_layout)
        
        # Block message (matches UI: plainTextEdit)
        screen_layout.addWidget(QLabel("Block Screen Message:"))
        self.plainTextEdit = QPlainTextEdit()
        self.plainTextEdit.setPlainText("🚫 CONTENT BLOCKED\n\nThis content has been blocked to protect you from inappropriate material.\n\nPlease use the internet responsibly.")
        self.plainTextEdit.setMaximumHeight(120)
        screen_layout.addWidget(self.plainTextEdit)
        
        layout.addWidget(screen_group)
        
        # Status section
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Status: Content blocking disabled")
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.stats_label = QLabel("Statistics: No blocks recorded yet")
        self.stats_label.setStyleSheet("font-size: 12px; color: #7f8c8d; padding: 5px;")
        status_layout.addWidget(self.stats_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def create_testing_tab(self):
        """Create the testing tab"""
        test_tab = QWidget()
        self.tab_widget.addTab(test_tab, "Testing & Demo")
        
        layout = QVBoxLayout(test_tab)
        layout.setSpacing(15)
        
        # Testing section
        test_group = QGroupBox("Test Functions")
        test_layout = QVBoxLayout(test_group)
        
        # Test block screen button
        self.test_block_btn = QPushButton("🚫 Test Block Screen")
        self.test_block_btn.clicked.connect(self.test_block_screen)
        self.test_block_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        test_layout.addWidget(self.test_block_btn)
        
        # Test website analysis
        self.test_website_btn = QPushButton("🌐 Test Website Analysis")
        self.test_website_btn.clicked.connect(self.test_website_analysis)
        self.test_website_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_layout.addWidget(self.test_website_btn)
        
        # Test keyword detection
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("Test Text:"))
        self.test_text_input = QLineEdit()
        self.test_text_input.setPlaceholderText("Enter text to test for adult content...")
        keyword_layout.addWidget(self.test_text_input)
        
        self.test_keyword_btn = QPushButton("🔍 Test Keywords")
        self.test_keyword_btn.clicked.connect(self.test_keyword_detection)
        self.test_keyword_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        keyword_layout.addWidget(self.test_keyword_btn)
        
        test_layout.addLayout(keyword_layout)
        
        layout.addWidget(test_group)
        
        # Results section
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Demo section
        demo_group = QGroupBox("Demonstration")
        demo_layout = QVBoxLayout(demo_group)
        
        demo_info = QLabel("""
        <b>How to test the content blocker:</b><br>
        1. Enable "Block Adult Content" in the Controls tab<br>
        2. Use the test buttons above to simulate different scenarios<br>
        3. Check the Logs tab to see blocking activity<br>
        4. The block screen will appear when inappropriate content is detected<br><br>
        <b>Note:</b> Full browser and application monitoring requires additional setup and permissions.
        """)
        demo_info.setStyleSheet("color: #34495e; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        demo_info.setWordWrap(True)
        demo_layout.addWidget(demo_info)
        
        layout.addWidget(demo_group)
        
        layout.addStretch()
        
    def create_logs_tab(self):
        """Create the logs tab"""
        logs_tab = QWidget()
        self.tab_widget.addTab(logs_tab, "Activity Logs")
        
        layout = QVBoxLayout(logs_tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh Logs")
        refresh_btn.clicked.connect(self.refresh_logs)
        controls_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Logs display
        self.logs_list = QListWidget()
        self.logs_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.logs_list)
        
    def setup_content_blocker(self):
        """Setup content blocker integration"""
        try:
            # Setup integration using the integration module
            self.content_blocker_integration = setup_content_blocker_integration(self)
            
            if self.content_blocker_integration:
                # Connect status changes
                self.content_blocker_integration.status_changed.connect(self.on_status_changed)
                self.add_result("✅ Content blocker integration setup successful")
            else:
                self.add_result("❌ Failed to setup content blocker integration")
                
        except Exception as e:
            self.add_result(f"❌ Error setting up content blocker: {e}")
            
    def setup_status_updates(self):
        """Setup periodic status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Update every 2 seconds
        
    def on_status_changed(self, enabled):
        """Handle status change"""
        if enabled:
            self.status_label.setText("Status: ✅ Content blocking ENABLED")
            self.status_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #d5f4e6; color: #27ae60; border-radius: 5px; font-weight: bold;")
        else:
            self.status_label.setText("Status: ❌ Content blocking DISABLED")
            self.status_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #fadbd8; color: #e74c3c; border-radius: 5px; font-weight: bold;")
            
    def update_status(self):
        """Update status information"""
        try:
            if hasattr(self, 'content_blocker_integration'):
                # Update statistics
                logs = self.content_blocker_integration.get_block_logs(10)
                self.stats_label.setText(f"Statistics: {len(logs)} recent blocks recorded")
        except Exception as e:
            pass
            
    def test_block_screen(self):
        """Test the block screen functionality"""
        try:
            self.add_result("🧪 Testing block screen...")
            
            # Update settings first
            if hasattr(self, 'content_blocker_integration'):
                self.content_blocker_integration.update_blocker_settings()
                
            # Create and show test block screen
            block_screen = BlockScreen("Website", "test-adult-site.com", "Adult content detected (TEST MODE)")
            block_screen.show()
            
            self.add_result("✅ Block screen test initiated")
            
        except Exception as e:
            self.add_result(f"❌ Error showing test block screen: {e}")
            
    def test_website_analysis(self):
        """Test website content analysis"""
        try:
            self.add_result("🧪 Testing website analysis...")
            
            blocker = get_blocker_instance()
            
            # Test URLs
            test_urls = [
                "https://google.com",
                "https://example.com", 
                "adult-content-site.com"  # This would be blocked
            ]
            
            for url in test_urls:
                is_blocked = blocker._is_domain_blocked(url)
                result = "🚫 BLOCKED" if is_blocked else "✅ ALLOWED"
                self.add_result(f"   {url}: {result}")
                
            self.add_result("✅ Website analysis test completed")
            
        except Exception as e:
            self.add_result(f"❌ Error testing website analysis: {e}")
            
    def test_keyword_detection(self):
        """Test keyword detection"""
        try:
            test_text = self.test_text_input.text()
            if not test_text:
                self.add_result("❌ Please enter text to test")
                return
                
            self.add_result(f"🧪 Testing text: '{test_text}'")
            
            blocker = get_blocker_instance()
            contains_adult_content = blocker._contains_adult_content(test_text)
            
            result = "🚫 BLOCKED (contains adult content)" if contains_adult_content else "✅ ALLOWED (clean content)"
            self.add_result(f"   Result: {result}")
            
        except Exception as e:
            self.add_result(f"❌ Error testing keyword detection: {e}")
            
    def refresh_logs(self):
        """Refresh the logs display"""
        try:
            self.logs_list.clear()
            
            if hasattr(self, 'content_blocker_integration'):
                logs = self.content_blocker_integration.get_block_logs(50)
                
                if logs:
                    for log in logs:
                        timestamp, content_type, source, reason, app = log
                        log_text = f"[{timestamp}] {content_type}: {source} - {reason}"
                        self.logs_list.addItem(log_text)
                else:
                    self.logs_list.addItem("No blocking events recorded yet")
            else:
                self.logs_list.addItem("Content blocker not initialized")
                
        except Exception as e:
            self.logs_list.addItem(f"Error loading logs: {e}")
            
    def clear_logs(self):
        """Clear all logs"""
        try:
            if hasattr(self, 'content_blocker_integration'):
                self.content_blocker_integration.clear_block_logs()
                self.refresh_logs()
                self.add_result("🗑️ Logs cleared")
            else:
                self.add_result("❌ Content blocker not initialized")
        except Exception as e:
            self.add_result(f"❌ Error clearing logs: {e}")
            
    def add_result(self, text):
        """Add result to the results display"""
        current_time = time.strftime("%H:%M:%S")
        self.results_text.append(f"[{current_time}] {text}")
        
        # Auto-scroll to bottom
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Main function"""
    print("🛡️ Adult Content Blocker Test Application")
    print("=" * 60)
    print("This application demonstrates the adult content blocking functionality.")
    print("\n📋 Features:")
    print("  • Toggle content blocking on/off")
    print("  • Configure countdown timer")
    print("  • Set redirect URL")
    print("  • Customize block message")
    print("  • Test block screen display")
    print("  • Monitor blocking activity")
    print("\n⚠️  Note: Full monitoring requires additional system permissions and dependencies.")
    print("   Install requirements: pip install -r requirements_content_blocker.txt")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Adult Content Blocker Test")
    app.setOrganizationName("Content Safety Tools")
    
    # Apply modern styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ecf0f1;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin: 10px 0;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #2c3e50;
        }
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #bdc3c7;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
    """)
    
    # Create and show main window
    window = TestMainWindow()
    window.show()
    
    # Run application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()