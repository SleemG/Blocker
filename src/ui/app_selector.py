import winreg
import ctypes
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QListWidget, QCheckBox, QScrollArea, QLabel,
                           QWidget, QLineEdit, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class IconExtractor:
    """Extract icons from executable files"""
    
    @staticmethod
    def get_file_icon(file_path, size=32):
        """Extract icon from file using Windows API"""
        try:
            # Get file info including icon
            shell32 = ctypes.windll.shell32
            
            # Get icon handle
            large_icons = ctypes.c_void_p()
            small_icons = ctypes.c_void_p()
            
            result = shell32.ExtractIconExW(
                ctypes.c_wchar_p(file_path),
                0, 
                ctypes.byref(large_icons) if size > 16 else None,
                ctypes.byref(small_icons) if size <= 16 else None,
                1
            )
            
            if result > 0:
                # Convert to QIcon
                if size > 16 and large_icons:
                    return IconExtractor._hicon_to_qicon(large_icons.value)
                elif size <= 16 and small_icons:
                    return IconExtractor._hicon_to_qicon(small_icons.value)
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _hicon_to_qicon(hicon):
        """Convert Windows HICON to QIcon"""
        try:
            from PyQt5.QtWinExtras import QtWin
            pixmap = QtWin.fromHICON(hicon)
            return QIcon(pixmap)
        except ImportError:
            # Fallback if QtWinExtras not available
            return None

class ProgramLoader(QThread):
    """Thread to load programs in background"""
    programs_loaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.all_programs = []  # Store programs list as instance variable
        self._running = True

    def stop(self):
        """Stop the thread safely"""
        self._running = False
        self.wait()  # Wait for thread to finish
        
    def __del__(self):
        """Clean up thread when object is destroyed"""
        self._running = False
        self.wait()
    
    def run(self):
        programs = []
        if not self._running:
            return
            
        # Registry paths for installed programs
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        seen_programs = set()
        
        for hkey, subkey_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    
                                    # Skip system components and updates
                                    skip_terms = ['update', 'hotfix', 'security', 'kb', 
                                                'redistributable', 'runtime', 'driver',
                                                'language pack', 'service pack']
                                    
                                    if any(term in display_name.lower() for term in skip_terms):
                                        continue
                                    
                                    if display_name.lower() in seen_programs:
                                        continue
                                    
                                    seen_programs.add(display_name.lower())
                                    
                                    # Try to get additional info
                                    install_location = ""
                                    display_icon = ""
                                    estimated_size = ""
                                    install_date = ""
                                    
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    except FileNotFoundError:
                                        pass
                                    
                                    try:
                                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                    except FileNotFoundError:
                                        pass
                                    
                                    try:
                                        size_value = winreg.QueryValueEx(subkey, "EstimatedSize")[0]
                                        estimated_size = f"{size_value / 1024:.1f} MB" if size_value else ""
                                    except (FileNotFoundError, TypeError):
                                        pass
                                    
                                    try:
                                        install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                        if len(install_date) == 8:  # Format: YYYYMMDD
                                            install_date = f"{install_date[4:6]}/{install_date[6:8]}/{install_date[:4]}"
                                    except (FileNotFoundError, ValueError):
                                        pass
                                    
                                    programs.append({
                                        'name': display_name,
                                        'icon_path': display_icon,
                                        'install_location': install_location,
                                        'size': estimated_size,
                                        'install_date': install_date
                                    })
                                    
                                except FileNotFoundError:
                                    continue
                        except OSError:
                            continue
            except OSError:
                continue
        
        # Sort programs by name
        programs.sort(key=lambda x: x['name'].lower())
        self.all_programs = programs  # Store programs in instance variable
        self.programs_loaded.emit(programs)

class ProgramSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Programs")
        self.setGeometry(200, 200, 700, 600)
        self.selected_programs = []
        self.all_programs = []
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Select programs to add:")
        title_label.setFont(QFont("Arial", 10))
        layout.addWidget(title_label)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search programs...")
        self.search_box.textChanged.connect(self.filter_programs)
        layout.addWidget(self.search_box)
        
        # Loading label
        self.loading_label = QLabel("Loading programs...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)
        
        # Scroll area for programs
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVisible(False)  # Hide until programs are loaded
        layout.addWidget(self.scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_selection)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Start loading programs
        self.program_loader = ProgramLoader()
        self.program_loader.programs_loaded.connect(self.on_programs_loaded)
        self.program_loader.start()
    
    def on_programs_loaded(self, programs):
        """Handle loaded programs"""
        self.all_programs = programs
        self.loading_label.setVisible(False)
        self.scroll_area.setVisible(True)
        self.display_programs(programs)
    
    def display_programs(self, programs):
        """Display programs in the scroll area"""
        # Clear existing widgets
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for program in programs:
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout()
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            
            # Get icon
            icon = None
            if program['icon_path']:
                # Extract icon path from registry value
                icon_path = program['icon_path'].split(',')[0].strip('"')
                if os.path.exists(icon_path):
                    icon = IconExtractor.get_file_icon(icon_path, 29)
            
            # Icon label
            icon_label = QLabel()
            icon_label.setFixedSize(29, 29)
            if icon:
                icon_label.setPixmap(icon.pixmap(29, 29))
            else:
                icon_label.setStyleSheet("""
                    background-color: #404040;
                    border: 1px solid #666666;
                    border-radius: 3px;
                """)
            checkbox_layout.addWidget(icon_label)
            
            # Checkbox
            checkbox = QCheckBox(program['name'])
            checkbox.program_data = program
            checkbox_layout.addWidget(checkbox)
            
            checkbox_layout.addStretch()
            checkbox_widget.setLayout(checkbox_layout)
            self.scroll_layout.addWidget(checkbox_widget)
        
        # Add stretch to push checkboxes to top
        self.scroll_layout.addStretch()
    
    def filter_programs(self, text):
        """Filter programs based on search text"""
        if not text:
            filtered_programs = self.all_programs
        else:
            filtered_programs = [p for p in self.all_programs 
                               if text.lower() in p['name'].lower()]
        self.display_programs(filtered_programs)
    
    def accept_selection(self):
        """Get selected programs and close dialog"""
        self.selected_programs = []
        
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'layout'):
                for j in range(widget.layout().count()):
                    item_widget = widget.layout().itemAt(j).widget()
                    if isinstance(item_widget, QCheckBox) and item_widget.isChecked():
                        self.selected_programs.append(item_widget.program_data)
        
        self.accept()

class ProgramListItem(QWidget):
    def __init__(self, program_data):
        super().__init__()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)  # Increased vertical margins
        layout.setSpacing(10)  # Add space between elements
        
        # Container for checkbox and icon
        left_container = QHBoxLayout()
        left_container.setSpacing(5)  # Space between checkbox and icon
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(20, 20)
        left_container.addWidget(self.checkbox)
        
        # Program icon
        icon_label = QLabel()
        icon_label.setFixedSize(29, 29)
        
        # Try to get icon
        icon = None
        if program_data.get('icon_path'):
            icon_path = program_data['icon_path'].split(',')[0].strip('"')
            if os.path.exists(icon_path):
                icon = IconExtractor.get_file_icon(icon_path, 29)
        
        if icon:
            icon_label.setPixmap(icon.pixmap(29, 29))
        else:
            # Default icon placeholder
            icon_label.setStyleSheet("""
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 3px;
            """)
        
        left_container.addWidget(icon_label)
        layout.addLayout(left_container)
        
        # Program name
        name_label = QLabel(program_data['name'])
        name_label.setFont(QFont("Arial", 9))
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(name_label)
        
        # Info container for size and date
        info_container = QHBoxLayout()
        info_container.setSpacing(15)  # Space between size and date
        
        # Size
        size = program_data.get('size', '')
        if size:
            size_label = QLabel(size)
            size_label.setFont(QFont("Arial", 9))
            size_label.setMinimumWidth(80)
            size_label.setAlignment(Qt.AlignRight)
            info_container.addWidget(size_label)
        
        # Install date
        install_date = program_data.get('install_date', '')
        if install_date:
            date_label = QLabel(install_date)
            date_label.setFont(QFont("Arial", 9))
            date_label.setMinimumWidth(80)
            date_label.setAlignment(Qt.AlignRight)
            info_container.addWidget(date_label)
        
        layout.addLayout(info_container)
        
        # Set the layout
        self.setLayout(layout)
        self.program_data = program_data
        
        # Set minimum height for the item
        self.setMinimumHeight(50)
        
        # Set object name for stylesheet
        self.setObjectName("programListItem")
        
        # Style the widget
        self.setStyleSheet("""
            QWidget#programListItem {
                border-radius: 4px;
            }
            QWidget#programListItem:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
    
    def sizeHint(self):
        """Override sizeHint to ensure consistent height"""
        size = super().sizeHint()
        size.setHeight(50)  # Fixed height for all items
        return size
        
    def mousePressEvent(self, event):
        """Handle mouse clicks anywhere on the item"""
        if event.button() == Qt.LeftButton:
            # Toggle the checkbox
            self.checkbox.setChecked(not self.checkbox.isChecked())
            event.accept()
        else:
            super().mousePressEvent(event)
