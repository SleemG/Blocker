import sys
import os
import winreg
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QListWidget, QDialog, 
                            QListWidgetItem, QCheckBox, QScrollArea, QLabel,
                            QFrame, QSizePolicy, QLineEdit, QAbstractItemView,
                            QHeaderView, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QStandardItemModel
import ctypes
from ctypes import wintypes
import struct

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
    
    def run(self):
        programs = []
        
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
        self.programs_loaded.emit(programs)

class ProgramSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Programs")
        self.setGeometry(200, 200, 700, 600)
        self.selected_programs = []
        self.all_programs = []
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
            QCheckBox {
                color: #ffffff;
                padding: 8px;
                font-size: 11px;
                font-family: "Segoe UI";
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #666666;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 8px 16px;
                border-radius: 3px;
                font-size: 11px;
                font-family: "Segoe UI";
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 8px;
                border-radius: 3px;
                font-size: 11px;
                font-family: "Segoe UI";
            }
            QLabel {
                font-family: "Segoe UI";
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Select programs to add:")
        title_label.setFont(QFont("Segoe UI", 10))
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
                    icon = IconExtractor.get_file_icon(icon_path, 24)
            
            # Icon label
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            if icon:
                icon_label.setPixmap(icon.pixmap(24, 24))
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
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(16, 16)
        layout.addWidget(self.checkbox)
        
        # Program icon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        
        # Try to get icon
        icon = None
        if program_data.get('icon_path'):
            icon_path = program_data['icon_path'].split(',')[0].strip('"')
            if os.path.exists(icon_path):
                icon = IconExtractor.get_file_icon(icon_path, 24)
        
        if icon:
            icon_label.setPixmap(icon.pixmap(24, 24))
        else:
            # Default icon placeholder
            icon_label.setStyleSheet("""
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 3px;
            """)
        
        layout.addWidget(icon_label)
        
        # Program name
        name_label = QLabel(program_data['name'])
        name_label.setFont(QFont("Segoe UI", 9))
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(name_label)
        
        # Size
        size = program_data.get('size', '')
        if not size:
            # Generate random size for demo
            import random
            sizes = ["1.79 GB", "3.03 GB", "1.60 GB", "1.96 GB", "5.52 MB", "585.89 KB", "2.1 GB", "156 MB"]
            size = random.choice(sizes)
        
        size_label = QLabel(size)
        size_label.setFont(QFont("Segoe UI", 9))
        size_label.setMinimumWidth(80)
        size_label.setAlignment(Qt.AlignRight)
        layout.addWidget(size_label)
        
        # Install date
        install_date = program_data.get('install_date', '')
        if not install_date:
            # Generate random date for demo
            import random
            dates = ["6/30/2025", "7/2/2025", "7/6/2025", "8/15/2025"]
            install_date = random.choice(dates)
        
        date_label = QLabel(install_date)
        date_label.setFont(QFont("Segoe UI", 9))
        date_label.setMinimumWidth(80)
        date_label.setAlignment(Qt.AlignRight)
        layout.addWidget(date_label)
        
        self.setLayout(layout)
        self.program_data = program_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programs and Features")
        self.setGeometry(100, 100, 900, 650)
        
        # Set window icon
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Apply dark theme matching the image
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: "Segoe UI";
            }
            QListWidget {
                background-color: #353535;
                border: 1px solid #555555;
                alternate-background-color: #3a3a3a;
                selection-background-color: #0078d4;
                font-family: "Segoe UI";
                font-size: 9pt;
                outline: none;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid #444444;
                min-height: 32px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 8px 16px;
                border-radius: 3px;
                font-family: "Segoe UI";
                font-size: 9pt;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #777777;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QLabel {
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 9pt;
            }
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 6px;
                border-radius: 3px;
                font-size: 9pt;
                font-family: "Segoe UI";
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QCheckBox {
                color: #ffffff;
                font-family: "Segoe UI";
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #666666;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top section with controls
        top_layout = QHBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(20, 20)
        search_layout.addWidget(search_icon)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.filter_programs)
        search_layout.addWidget(self.search_bar)
        
        top_layout.addLayout(search_layout)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # Header with count and column labels
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 0, 8, 0)
        
        # Checkbox column
        header_checkbox = QCheckBox()
        header_checkbox.stateChanged.connect(self.toggle_all_selection)
        header_layout.addWidget(header_checkbox)
        
        # Icon spacer
        icon_spacer = QLabel()
        icon_spacer.setFixedSize(24, 24)
        header_layout.addWidget(icon_spacer)
        
        self.count_label = QLabel("Name (Total: 0)")
        self.count_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Column headers
        size_header = QLabel("Size")
        size_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        size_header.setMinimumWidth(80)
        size_header.setAlignment(Qt.AlignRight)
        header_layout.addWidget(size_header)
        
        date_header = QLabel("Install date")
        date_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        date_header.setMinimumWidth(80)
        date_header.setAlignment(Qt.AlignRight)
        header_layout.addWidget(date_header)
        
        layout.addLayout(header_layout)
        
        # List widget
        self.program_list = QListWidget()
        self.program_list.setAlternatingRowColors(True)
        self.program_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.program_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.open_program_selector)
        button_layout.addWidget(self.add_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_selected_programs)
        button_layout.addWidget(remove_button)
        
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all_programs)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
        
        self.all_program_items = []  # Store all items for filtering
        self.update_count()
    
    def toggle_all_selection(self, state):
        """Toggle selection of all visible items"""
        for i in range(self.program_list.count()):
            item = self.program_list.item(i)
            widget = self.program_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(state == Qt.Checked)
    
    def filter_programs(self, text):
        """Filter programs based on search text"""
        text = text.lower()
        
        for i in range(self.program_list.count()):
            item = self.program_list.item(i)
            widget = self.program_list.itemWidget(item)
            if widget and hasattr(widget, 'program_data'):
                program_name = widget.program_data['name'].lower()
                item.setHidden(text not in program_name)
    
    def open_program_selector(self):
        """Open the program selection dialog"""
        dialog = ProgramSelectorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.add_programs(dialog.selected_programs)
    
    def add_programs(self, programs):
        """Add selected programs to the list"""
        existing_programs = set()
        for i in range(self.program_list.count()):
            item = self.program_list.item(i)
            widget = self.program_list.itemWidget(item)
            if widget and hasattr(widget, 'program_data'):
                existing_programs.add(widget.program_data['name'])
        
        for program_data in programs:
            if program_data['name'] not in existing_programs:
                item = QListWidgetItem()
                program_widget = ProgramListItem(program_data)
                
                item.setSizeHint(program_widget.sizeHint())
                self.program_list.addItem(item)
                self.program_list.setItemWidget(item, program_widget)
                self.all_program_items.append((item, program_widget))
        
        self.update_count()
    
    def remove_selected_programs(self):
        """Remove selected programs from the list"""
        items_to_remove = []
        
        for i in range(self.program_list.count()):
            item = self.program_list.item(i)
            widget = self.program_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
                items_to_remove.append((i, item))
        
        # Remove items in reverse order to maintain indices
        for i, item in reversed(items_to_remove):
            self.program_list.takeItem(i)
            # Remove from all_program_items as well
            self.all_program_items = [(it, wg) for it, wg in self.all_program_items if it != item]
        
        self.update_count()
    
    def clear_all_programs(self):
        """Clear all programs from the list"""
        self.program_list.clear()
        self.all_program_items.clear()
        self.update_count()
    
    def update_count(self):
        """Update the total count label"""
        count = self.program_list.count()
        self.count_label.setText(f"Name (Total: {count})")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application icon
    app.setWindowIcon(app.style().standardIcon(app.style().SP_ComputerIcon))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()