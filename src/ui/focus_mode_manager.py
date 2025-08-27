import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
                             QPushButton, QListWidget, QMessageBox, QDialog,
                             QTimeEdit, QLineEdit, QRadioButton, QDialogButtonBox,
                             QScrollArea, QFrame, QListWidgetItem, QFileDialog)
from PyQt5.QtCore import QTime, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
from .ui_components import ToggleSwitch
from PyQt5.uic import loadUi
from datetime import datetime
import sqlite3
from typing import List, Tuple, Optional


class FocusModeData:
    """Data class to store focus mode information"""
    def __init__(self):
        self.id = None  # Database ID
        self.title = ""
        self.start_time = QTime(9, 0)  # Default 9:00 AM
        self.end_time = QTime(17, 0)   # Default 5:00 PM
        self.is_daily = True
        self.selected_days = []
        self.allowed_apps = []
        self.allowed_websites = []
        self.user_email = ""
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.toString('HH:mm:ss'),
            'end_time': self.end_time.toString('HH:mm:ss'),
            'is_daily': self.is_daily,
            'selected_days': ','.join(self.selected_days),  # Store as comma-separated string
            'allowed_apps': '|'.join(self.allowed_apps),    # Store as pipe-separated string
            'allowed_websites': '|'.join(self.allowed_websites),
            'user_email': self.user_email
        }

class CreateFocusModeDialog(QDialog):
    """Dialog for creating a new focus mode timer"""
    
    def __init__(self, parent=None, existing_apps=None, existing_websites=None):
        super().__init__(parent)
        self.setWindowTitle("Create Focus Mode Timer")
        self.setModal(True)
        self.setFixedSize(500, 750)
        
        # Get existing data for validation
        self.existing_apps = existing_apps or []
        self.existing_websites = existing_websites or []
        
        # Apply the same stylesheet as parent
        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())
        
        # Initialize UI components
        self.setup_ui()
        self.setup_connections()
        
        # Initialize data
        self.focus_data = FocusModeData()
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QGridLayout(self)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Create main widget for scroll area
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Title input
        self.title_lineEdit = QLineEdit()
        self.title_lineEdit.setPlaceholderText("Title (Optional)")
        self.title_lineEdit.setMinimumHeight(45)
        self.title_lineEdit.setFont(QFont("Arial", 9))
        scroll_layout.addWidget(self.title_lineEdit, 0, 0)
        
        # Separator line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setLineWidth(1)
        scroll_layout.addWidget(line1, 1, 0)
        
        # Timer group box
        self.setup_timer_group()
        scroll_layout.addWidget(self.timer_grpBx, 2, 0)
        
        # Separator line
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setLineWidth(1)
        scroll_layout.addWidget(line2, 3, 0)
        
        # Allowed apps group
        self.setup_apps_group()
        scroll_layout.addWidget(self.allwedApps_grpBx, 4, 0)
        
        # Separator line
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setLineWidth(1)
        scroll_layout.addWidget(line3, 5, 0)
        
        # Allowed websites group
        self.setup_websites_group()
        scroll_layout.addWidget(self.groupBox_4, 6, 0)
        
        # Button box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.setFont(QFont("Arial", 9))
        scroll_layout.addWidget(self.buttonBox, 7, 0)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 0, 0)

        # set style for checked buttons
        for btn in self.day_buttons.values():
            btn.setStyleSheet("""
                QPushButton{
                    color: #FFF;
                    border: none;
                    font-size: 12px;
                    margin: 2px 0;
                    padding: 2px;
                    text-align: center;
                        }
                QPushButton:hover {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    padding: 2px;
                }
                QPushButton:checked {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    border: 1px solid #1976D2;
                    border-radius: 4px;
                    padding: 2px;
                }
            """)
    
    def setup_timer_group(self):
        """Setup timer configuration group"""
        self.timer_grpBx = QGroupBox("Set Timer")
        self.timer_grpBx.setFont(QFont("Arial", 9))
        self.timer_grpBx.setMinimumSize(452, 175)
        layout = QGridLayout(self.timer_grpBx)
        
        # From time
        form_lbl = QLabel("From")
        form_lbl.setFont(QFont("Arial", 9))
        layout.addWidget(form_lbl, 0, 0)
        
        self.start_timeEdit = QTimeEdit(QTime(9, 0))
        self.start_timeEdit.setMaximumWidth(90)
        self.start_timeEdit.setFont(QFont("Arial", 9))
        layout.addWidget(self.start_timeEdit, 0, 1, 1, 2)
        
        # To time
        to_lbl = QLabel("To")
        to_lbl.setFont(QFont("Arial", 9))
        layout.addWidget(to_lbl, 0, 4)
        
        self.end_timeEdit = QTimeEdit(QTime(17, 0))
        self.end_timeEdit.setMaximumWidth(90)
        self.end_timeEdit.setFont(QFont("Arial", 9))
        layout.addWidget(self.end_timeEdit, 0, 5, 1, 2)
        
        # Daily/Custom radio buttons
        self.daily_radio = QRadioButton("Daily")
        self.daily_radio.setChecked(True)
        self.daily_radio.setFont(QFont("Arial", 9))
        layout.addWidget(self.daily_radio, 1, 0, 1, 2)
        
        self.custom_radio = QRadioButton("Custom")
        self.custom_radio.setFont(QFont("Arial", 9))
        layout.addWidget(self.custom_radio, 1, 5, 1, 2)
        
        # Day buttons - matching your original layout
        days = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        self.day_buttons = {}
        self.default_checked = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        
        for i, day in enumerate(days):
            btn = QPushButton(day)
            btn.setCheckable(True)
            btn.setMinimumSize(50, 50)
            btn.setMaximumSize(60, 50)
            btn.setFont(QFont("Arial", 8))
            if day in self.default_checked:
                btn.setChecked(True)
            btn.setEnabled(False)  # Disable the buttons since they should all be checked
            self.day_buttons[day] = btn
            layout.addWidget(btn, 2, i)
    
    def setup_apps_group(self):
        """Setup allowed apps group"""
        self.allwedApps_grpBx = QGroupBox("Allowed Apps")
        self.allwedApps_grpBx.setFont(QFont("Arial", 9))
        layout = QGridLayout(self.allwedApps_grpBx)
        
        self.allowedApps_lstWdgt = QListWidget()
        self.allowedApps_lstWdgt.setFont(QFont("Arial", 9))
        layout.addWidget(self.allowedApps_lstWdgt, 0, 0)
        
        self.addApps_btn = QPushButton("Add from PC")
        self.addApps_btn.setFont(QFont("Arial", 9))
        layout.addWidget(self.addApps_btn, 1, 0)
    
    def setup_websites_group(self):
        """Setup allowed websites group"""
        self.groupBox_4 = QGroupBox("Allowed Websites")
        self.groupBox_4.setFont(QFont("Arial", 9))
        layout = QGridLayout(self.groupBox_4)
        
        self.allowedWeb_lstWdgt = QListWidget()
        self.allowedWeb_lstWdgt.setFont(QFont("Arial", 9))
        layout.addWidget(self.allowedWeb_lstWdgt, 0, 0)
        
        # Add website input and button
        website_widget = QWidget()
        website_layout = QHBoxLayout(website_widget)
        
        self.website_lineEdit = QLineEdit()
        self.website_lineEdit.setPlaceholderText("Enter website URL or keyword")
        self.website_lineEdit.setFont(QFont("Arial", 9))
        
        self.addWeb_btn = QPushButton("Add")
        self.addWeb_btn.setFont(QFont("Arial", 9))
        
        website_layout.addWidget(self.website_lineEdit)
        website_layout.addWidget(self.addWeb_btn)
        
        layout.addWidget(website_widget, 1, 0)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.buttonBox.accepted.connect(self.accept_dialog)
        self.buttonBox.rejected.connect(self.reject)
        
        self.addApps_btn.clicked.connect(self.add_apps)
        self.addWeb_btn.clicked.connect(self.add_website)
        self.website_lineEdit.returnPressed.connect(self.add_website)
        
        # Radio button connections
        self.daily_radio.toggled.connect(self.on_daily_toggled)
        self.custom_radio.toggled.connect(self.on_custom_toggled)
    
    def on_daily_toggled(self, checked):
        """Handle daily radio button toggle"""
        if checked:
            # When daily is selected, check all day buttons
            for btn in self.day_buttons.values():
                btn.setChecked(True)
                btn.setEnabled(False)  # Disable the buttons since they should all be checked
    
    def on_custom_toggled(self, checked):
        """Handle custom radio button toggle"""
        if checked:
            # When custom is selected, uncheck all day buttons and enable them
            for btn in self.day_buttons.values():
                btn.setChecked(False)
                btn.setEnabled(True)  # Enable buttons to allow selection
    
    def add_apps(self):
        """Add applications using the same method as main window"""
        if hasattr(self.parent(), 'get_installed_apps'):
            apps = self.parent().get_installed_apps()
            
            # Use ProgramSelectorDialog from app_selector
            from .app_selector import ProgramSelectorDialog
            dialog = ProgramSelectorDialog(self)
            
            if dialog.exec_() == QDialog.Accepted:
                for program in dialog.selected_programs:
                    app_name = program['name']
                    
                    # Check for duplicates
                    existing_items = [self.allowedApps_lstWdgt.item(i).text() 
                                    for i in range(self.allowedApps_lstWdgt.count())]
                    
                    if app_name not in existing_items:
                        # Create item and set icon
                        item = QListWidgetItem(app_name)
                        
                        # Try to get icon
                        if program.get('icon_path'):
                            icon_path = program['icon_path'].split(',')[0].strip('"')
                            if os.path.exists(icon_path):
                                from .app_selector import IconExtractor
                                icon = IconExtractor.get_file_icon(icon_path, 32)
                                if icon:
                                    item.setIcon(icon)
                        
                        self.allowedApps_lstWdgt.addItem(item)
        else:
            # Fallback to file dialog
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Select Applications", 
                "", 
                "Executable Files (*.exe);;All Files (*)"
            )
            
            for file_path in files:
                if file_path not in [self.allowedApps_lstWdgt.item(i).text() 
                                   for i in range(self.allowedApps_lstWdgt.count())]:
                    self.allowedApps_lstWdgt.addItem(file_path)
    
    def add_website(self):
        """Add website to the list"""
        website = self.website_lineEdit.text().strip()
        if website:
            existing_items = [self.allowedWeb_lstWdgt.item(i).text() 
                            for i in range(self.allowedWeb_lstWdgt.count())]
            if website not in existing_items:
                self.allowedWeb_lstWdgt.addItem(website)
                self.website_lineEdit.clear()
            else:
                QMessageBox.information(self, "Duplicate Item", "This website is already in the list.")
    
    def accept_dialog(self):
        """Handle OK button click"""
        # Validate input
        if not self.validate_input():
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            'Confirm Focus Mode Creation',
            'Are you sure you want to create this Focus Mode timer?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.collect_data()
            self.accept()
    
    def validate_input(self):
        """Validate user input"""
        start_time = self.start_timeEdit.time()
        end_time = self.end_timeEdit.time()
        
        if start_time >= end_time:
            QMessageBox.warning(
                self, 
                "Invalid Time Range", 
                "End time must be later than start time."
            )
            return False
        
        if self.custom_radio.isChecked():
            selected_days = [day for day, btn in self.day_buttons.items() if btn.isChecked()]
            if not selected_days:
                QMessageBox.warning(
                    self, 
                    "No Days Selected", 
                    "Please select at least one day for custom schedule."
                )
                return False
        
        return True
    
    def collect_data(self):
        """Collect data from the form"""
        self.focus_data.title = self.title_lineEdit.text().strip() or f"Focus Mode {datetime.now().strftime('%H:%M')}"
        self.focus_data.start_time = self.start_timeEdit.time()
        self.focus_data.end_time = self.end_timeEdit.time()
        self.focus_data.is_daily = self.daily_radio.isChecked()
        
        if not self.focus_data.is_daily:
            self.focus_data.selected_days = [day for day, btn in self.day_buttons.items() if btn.isChecked()]
        else:
            self.focus_data.selected_days = list(self.day_buttons.keys())
        
        # Collect apps
        self.focus_data.allowed_apps = [
            self.allowedApps_lstWdgt.item(i).text() 
            for i in range(self.allowedApps_lstWdgt.count())
        ]
        
        # Collect websites
        self.focus_data.allowed_websites = [
            self.allowedWeb_lstWdgt.item(i).text() 
            for i in range(self.allowedWeb_lstWdgt.count())
        ]

class FocusModeGroupBox(QGroupBox):
    """Custom group box for displaying focus mode data"""
    
    delete_requested = pyqtSignal(object)
    selected = pyqtSignal(bool)
    timer_toggled = pyqtSignal(bool)
    
    def __init__(self, focus_data, parent=None):
        super().__init__(parent)
        self.focus_data = focus_data
        self.is_selected = False
        self.apps_list = None  # Store reference to apps list
        self.registry_apps = {}  # Store program data
        
        # Initialize program loader for icons
        from .app_selector import ProgramLoader
        self._program_loader = ProgramLoader()
        self._program_loader.programs_loaded.connect(self._on_programs_loaded)
        
        self.setup_ui()
        self.setMouseTracking(True)
        self.setup_style()
        
        # Start loading program data
        self._program_loader.start()
        
    def mousePressEvent(self, event):
        """Handle mouse press to toggle selection"""
        self.is_selected = not self.is_selected
        self.update_selection_style()
        self.selected.emit(self.is_selected)
        super().mousePressEvent(event)
    
    def setup_style(self):
        """Set up modern style for the group box"""
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
            }
            QGroupBox::title {
                background-color: transparent;
                padding: 8px 8px;
                color: #424242;

            }
            
            QLabel {
                color: #616161;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 2px;
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
    
    def update_selection_style(self):
        """Update the style based on selection state"""
        base_style = """
            FocusModeGroupBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
            }
            QGroupBox::title {
                background-color: transparent;
                color: #424242;
            }
            QLabel {
                color: #616161;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 2px;
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QGroupBox#apps_group, QGroupBox#websites_group {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
        """
        if self.is_selected:
            selection_style = """
                FocusModeGroupBox {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 8px;
                }
            """
            self.setStyleSheet(base_style + selection_style)
        else:
            self.setStyleSheet(base_style)
    
    def setup_ui(self):
        """Setup the group box UI"""
        self.setTitle(self.focus_data.title)
        self.setMinimumHeight(200)  # Increased minimum height
        self.setMaximumHeight(250)  # Increased maximum height
        self.setFont(QFont("Arial", 9))
        
        # Create main layout as horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 20, 12, 12)
        self.main_layout.setSpacing(20)
        
        # Left section - time info
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        
        duration_text = f"⏱ {self.focus_data.start_time.toString('hh:mm')} - {self.focus_data.end_time.toString('hh:mm')}"
        duration_lbl = QLabel(duration_text)
        duration_lbl.setFont(QFont("Arial", 9))
        left_layout.addWidget(duration_lbl)
        
        if self.focus_data.is_daily:
            days_text = "📅 Daily"
        else:
            days_text = f"📅 {', '.join(self.focus_data.selected_days)}"
        days_lbl = QLabel(days_text)
        days_lbl.setFont(QFont("Arial", 9))
        left_layout.addWidget(days_lbl)
        
        left_layout.addStretch()  # Add stretch to keep labels at top
        self.main_layout.addWidget(left_widget, 2)  # 1 stretch factor
        
        # Middle section - apps and websites
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(12)

        # Allowed Apps group
        if self.focus_data.allowed_apps:
            apps_group = QGroupBox("🖥 Allowed Apps")
            apps_group.setObjectName("apps_group")
            apps_group.setFont(QFont("Arial", 9))
            apps_group.setMinimumHeight(130)  # Set minimum height
            apps_layout = QVBoxLayout(apps_group)
            apps_layout.setContentsMargins(8, 16, 8, 8)
            
            apps_list = QListWidget()
            apps_list.setFont(QFont("Arial", 9))
            
            self.apps_list = apps_list  # Store reference to update later
            for app in self.focus_data.allowed_apps:
                app_name = os.path.basename(app) if app.endswith('.exe') else app
                item = QListWidgetItem(app_name)
                apps_list.addItem(item)
            
            apps_layout.addWidget(apps_list)
            middle_layout.addWidget(apps_group)
        
        # Allowed Websites group
        if self.focus_data.allowed_websites:
            websites_group = QGroupBox("🌐 Allowed Websites")
            websites_group.setObjectName("websites_group")
            websites_group.setFont(QFont("Arial", 9))
            websites_group.setMinimumHeight(130)  # Set minimum height
            websites_layout = QVBoxLayout(websites_group)
            websites_layout.setContentsMargins(8, 16, 8, 8)
            
            websites_list = QListWidget()
            websites_list.setFont(QFont("Arial", 9))
            
            for website in self.focus_data.allowed_websites:
                websites_list.addItem(website)
            
            websites_layout.addWidget(websites_list)
            middle_layout.addWidget(websites_group)
        
        # Add middle section to main layout with stretch factor of 2
        self.main_layout.addWidget(middle_widget, 8)
        
        # Right section - toggle switch
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.toggle_switch = ToggleSwitch()
        self.toggle_switch.toggled.connect(self.on_toggle_changed)
        right_layout.addWidget(self.toggle_switch, alignment=Qt.AlignTop | Qt.AlignRight)
        
        self.main_layout.addWidget(right_widget, 1)  # 1 stretch factor
        
    def on_toggle_changed(self, checked):
        """Handle toggle switch state changes"""
        self.timer_toggled.emit(checked)
        
    def _on_programs_loaded(self, apps):
        """Handle loaded program data"""
        if not self.apps_list:
            return
            
        # Process each app
        self.registry_apps = {}
        for app in apps:
            self.registry_apps[app['name']] = app
            
        # Update icons for existing items
        for i in range(self.apps_list.count()):
            item = self.apps_list.item(i)
            app_name = item.text()
            
            # Try to get program data
            if app_name in self.registry_apps:
                app_data = self.registry_apps[app_name]
                if app_data.get('icon_path'):
                    icon_path = app_data['icon_path'].split(',')[0].strip('"')
                    if os.path.exists(icon_path):
                        from .app_selector import IconExtractor
                        icon = IconExtractor.get_file_icon(icon_path, 32)
                        if icon:
                            item.setIcon(icon)
            elif app_name.endswith('.exe') and os.path.exists(app_name):
                from .app_selector import IconExtractor
                icon = IconExtractor.get_file_icon(app_name, 32)
                if icon:
                    item.setIcon(icon)

class FocusModeDatabase:
    """Database handler for focus mode data"""
    
    def __init__(self, db_path: str = 'app_blocker.db'):
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        """Create focus mode table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS focus_modes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        title TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        is_daily BOOLEAN NOT NULL,
                        selected_days TEXT,
                        allowed_apps TEXT,
                        allowed_websites TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_email) REFERENCES users (email)
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def add_focus_mode(self, focus_data: FocusModeData) -> Tuple[bool, Optional[str]]:
        """Add a focus mode to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO focus_modes (user_email, title, start_time, end_time, is_daily, 
                                           selected_days, allowed_apps, allowed_websites)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    focus_data.user_email,
                    focus_data.title,
                    focus_data.start_time.toString('HH:mm:ss'),
                    focus_data.end_time.toString('HH:mm:ss'),
                    focus_data.is_daily,
                    ','.join(focus_data.selected_days),
                    '|'.join(focus_data.allowed_apps),
                    '|'.join(focus_data.allowed_websites)
                ))
                
                focus_data.id = cursor.lastrowid
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)
    
    def get_focus_modes(self, user_email: str) -> List[FocusModeData]:
        """Get all focus modes for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, start_time, end_time, is_daily, 
                           selected_days, allowed_apps, allowed_websites
                    FROM focus_modes WHERE user_email = ?
                    ORDER BY created_at DESC
                ''', (user_email,))
                
                focus_modes = []
                for row in cursor.fetchall():
                    focus_data = FocusModeData()
                    focus_data.id = row[0]
                    focus_data.title = row[1]
                    focus_data.start_time = QTime.fromString(row[2], 'HH:mm:ss')
                    focus_data.end_time = QTime.fromString(row[3], 'HH:mm:ss')
                    focus_data.is_daily = bool(row[4])
                    focus_data.selected_days = row[5].split(',') if row[5] else []
                    focus_data.allowed_apps = row[6].split('|') if row[6] else []
                    focus_data.allowed_websites = row[7].split('|') if row[7] else []
                    focus_data.user_email = user_email
                    focus_modes.append(focus_data)
                
                return focus_modes
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def remove_focus_mode(self, focus_mode_id: int) -> bool:
        """Remove a focus mode from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM focus_modes WHERE id = ?', (focus_mode_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

class FocusModeManager:
    """Manager class for focus mode functionality"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.focus_modes = []
        self.selected_modes = set()
        
        # Initialize database
        self.db = FocusModeDatabase(main_window.db.db_path)
        
        # Get UI elements from your main window
        self.scroll_area = main_window.scrollArea
        self.scroll_content = main_window.scrollAreaWidgetContents
        self.add_btn = main_window.add_focus_btn
        self.remove_btn = main_window.remove_focus_btn
        
        # Remove the green border styling
        self.scroll_content.setStyleSheet("")
        
        # Setup connections
        self.setup_connections()
        
        # Handle existing layout or create new one
        self._setup_layout()
        
        # Load existing data when user is available
        if hasattr(main_window, 'user_email') and main_window.user_email:
            self.load_data()
            self.refresh_ui()
    
    def _setup_layout(self):
        """Setup or get the layout for the scroll content widget"""
        existing_layout = self.scroll_content.layout()
        
        if existing_layout is None:
            # No layout exists, create a new one
            layout = QVBoxLayout()
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(10)
            layout.setAlignment(Qt.AlignTop)
            self.scroll_content.setLayout(layout)
        else:
            # Layout already exists, just configure it
            existing_layout.setContentsMargins(6, 6, 6, 6)
            existing_layout.setSpacing(10)
            existing_layout.setAlignment(Qt.AlignTop)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.add_btn.clicked.connect(self.add_focus_mode)
        self.remove_btn.clicked.connect(self.remove_selected_focus_mode)
    
    def load_data(self):
        """Load focus modes from database"""
        if hasattr(self.main_window, 'user_email') and self.main_window.user_email:
            self.focus_modes = self.db.get_focus_modes(self.main_window.user_email)
    
    def add_focus_mode(self):
        """Add a new focus mode"""
        if not hasattr(self.main_window, 'user_email') or not self.main_window.user_email:
            QMessageBox.warning(
                self.main_window,
                "Not Logged In",
                "Please log in to create focus modes."
            )
            return
        
        # Get existing data for validation
        existing_apps = self.main_window.db.get_items(self.main_window.user_email, type_='block', item_type='app')
        existing_websites = self.main_window.db.get_items(self.main_window.user_email, type_='block', item_type='website')
        
        dialog = CreateFocusModeDialog(self.main_window, existing_apps, existing_websites)
        
        if dialog.exec_() == QDialog.Accepted:
            focus_data = dialog.focus_data
            focus_data.user_email = self.main_window.user_email
            
            success, error = self.db.add_focus_mode(focus_data)
            if success:
                # Insert at the beginning of the list
                self.focus_modes.insert(0, focus_data)
                self.refresh_ui()
                
                # Show success message using main window's method
                self.main_window.show_status_message(
                    f"Focus Mode '{focus_data.title}' created successfully!"
                )
                
                QMessageBox.information(
                    self.main_window,
                    "Focus Mode Created",
                    f"Focus Mode '{focus_data.title}' has been created successfully!"
                )
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Database Error",
                    f"Failed to create focus mode: {error}"
                )
    
    def remove_focus_mode(self, focus_group_box):
        """Remove a specific focus mode"""
        focus_data = focus_group_box.focus_data
        
        reply = QMessageBox.question(
            self.main_window,
            'Delete Focus Mode',
            f'Are you sure you want to delete "{focus_data.title}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.remove_focus_mode(focus_data.id):
                self.focus_modes.remove(focus_data)
                self.refresh_ui()
                
                self.main_window.show_status_message(
                    f"Focus Mode '{focus_data.title}' deleted successfully!"
                )
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Database Error",
                    "Failed to delete focus mode from database."
                )
    
    def remove_selected_focus_mode(self):
        """Remove all selected focus modes"""
        if not self.selected_modes:
            QMessageBox.information(
                self.main_window,
                "No Selection",
                "Please select one or more focus modes to remove."
            )
            return
        
        selected_count = len(self.selected_modes)
        message = f"Are you sure you want to delete {selected_count} selected focus mode{'s' if selected_count > 1 else ''}?"
        reply = QMessageBox.question(
            self.main_window,
            'Delete Focus Modes',
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            for focus_data in list(self.selected_modes):  # Create a copy since we'll modify the set
                if self.db.remove_focus_mode(focus_data.id):
                    self.focus_modes.remove(focus_data)
                    self.selected_modes.remove(focus_data)
                    success_count += 1
            
            if success_count > 0:
                self.refresh_ui()
                self.main_window.show_status_message(
                    f"Successfully deleted {success_count} focus mode{'s' if success_count > 1 else ''}!"
                )
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Database Error",
                    "Failed to delete focus modes from database."
                )
    
    def refresh_ui(self):
        """Refresh the focus mode display"""
        layout = self.scroll_content.layout()
        
        # Clear existing focus mode widgets
        for i in reversed(range(layout.count())):
            child = layout.itemAt(i).widget()
            if isinstance(child, (FocusModeGroupBox, QLabel)):
                child.setParent(None)
        
        # If there are no focus modes, show a message
        if not self.focus_modes:
            no_timers_label = QLabel("No timers")
            no_timers_label.setAlignment(Qt.AlignCenter)
            no_timers_label.setFont(QFont("Arial", 11))
            no_timers_label.setStyleSheet("color: #757575; margin: 20px;")
            layout.addWidget(no_timers_label)
        else:
            # Add focus mode group boxes
            for focus_data in self.focus_modes:
                group_box = FocusModeGroupBox(focus_data)
                group_box.delete_requested.connect(self.remove_focus_mode)
                group_box.selected.connect(lambda checked, box=group_box: self.on_focus_mode_selected(box, checked))
                layout.addWidget(group_box)
                
                # Restore selection state if it was previously selected
                if focus_data in self.selected_modes:
                    group_box.is_selected = True
                    group_box.update_selection_style()
                
    def on_focus_mode_selected(self, group_box, is_selected):
        """Handle focus mode selection"""
        if is_selected:
            self.selected_modes.add(group_box.focus_data)
        else:
            self.selected_modes.discard(group_box.focus_data)
        
    
    
    def on_user_loaded(self):
        """Called when user data is loaded"""
        self.load_data()
        self.refresh_ui()