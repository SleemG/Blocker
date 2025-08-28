import winreg
import os
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QListWidgetItem, QDialog, QWidget,
                           QVBoxLayout, QHBoxLayout, QDialogButtonBox, QListWidget, QFileDialog, 
                           QLineEdit, QPushButton, QGroupBox, QStackedWidget, QLabel, QGridLayout)
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .signup_dialog import SignUpDialog
from ..utils.database import Database
from ..utils.helpers import fade_in_widget, slide_widget

from .focus_mode_manager import FocusModeManager

from .ui_components import (FloatingButton, FloatingButtonManager, 
                          CustomNotification, FloatingPanel, ToggleSwitch)
from .partner_dialog import PartnerDialog
from .app_selector import ProgramLoader, ProgramListItem

from ..core.adult_content_blocker import integrate_with_main_window


class MainWindow(QMainWindow):
    def __init__(self, show_on_start=True):
        super().__init__()
        self._program_loader = None  # Store program loader reference

        # Get the absolute path to the GUI folder relative to this script
        gui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "GUI")
        
        loadUi(os.path.join(gui_dir, "App GUI.ui"), self)
        
        # Load and combine all stylesheets with proper priority
        stylesheets = []
        
        # First load the base styles
        with open(os.path.join(gui_dir, "modern_style.qss"), "r") as f:
            stylesheets.append(f.read())
        
        # Then load settings styles
        with open(os.path.join(gui_dir, "settings.qss"), "r") as f:
            stylesheets.append(f.read())
            
        # Finally load SignUp styles to take precedence
        with open(os.path.join(gui_dir, "SignUp.qss"), "r") as f:
            stylesheets.append(f.read())
            
        # Combine all stylesheets and apply them
        self.setStyleSheet("\n".join(stylesheets))
        # Initialize variables
        self.db = Database()
        self.user_email = None
        self.show_on_start = show_on_start
        
        # Create database tables
        self.db.create_tables()
        
        # Initialize focus mode manager
        self.focus_mode_manager = None  # Will be initialized after user login

        # Connect signals for navigation
        self.blockList_btn.clicked.connect(self.show_block_list_page)
        self.whiteList_btn.clicked.connect(self.show_white_list_page)
        
        # Connect Block List buttons for websites tab
        self.blkLstAdd_btn1.clicked.connect(lambda: self.add_website(self.blkLst_lineEdit, self.listWidget))
        self.blkLstRmv_btn1.clicked.connect(lambda: self.remove_website(self.listWidget))
        
        # Connect Block List buttons for apps tab
        self.blkLstAdd_btn2.clicked.connect(lambda: self.show_app_selection_dialog(self.listWidget_2))
        self.blkLstRmv_btn2.clicked.connect(lambda: self.remove_website(self.listWidget_2))
        
        # Connect White List buttons for websites tab
        self.whtLstAdd_btn1.clicked.connect(lambda: self.add_website(self.whtLst_lineEdit, self.listWidget_3))
        self.whtLstRmv_btn1.clicked.connect(lambda: self.remove_website(self.listWidget_3))
        
        # Connect White List buttons for apps tab
        self.whtLstAdd_btn2.clicked.connect(lambda: self.show_app_selection_dialog(self.listWidget_4))
        self.whtLstRmv_btn2.clicked.connect(lambda: self.remove_website(self.listWidget_4))
        
        # Initialize UI state
        self.tabWidget.setCurrentIndex(0)  # Set to first tab
        self.blockList_btn.setChecked(True)
        self.whiteList_btn.setChecked(False)
        self.stackedWidget_blkLst.setCurrentWidget(self.BlockList_page)

        # Configure list widgets
        self.setup_list_widgets()
        
        # Setup settings tab
        self.setup_settings_connections()

        # Define settings and their default states
        self.settings_toggles = {
            'checkBox': {'label': 'Block Adult Content', 'default': True},
            'checkBox_2': {'label': 'Filter Search Results', 'default': True},
            'checkBox_3': {'label': 'Block Image/Video Search', 'default': False},
            'checkBox_4': {'label': 'Block YouTube Shorts', 'default': False},
            'checkBox_5': {'label': 'Block Telegram Search', 'default': False},
            'checkBox_6': {'label': 'Uninstall Protection', 'default': True},
            'checkBox_7': {'label': 'Block Unsupported Browsers', 'default': True},
            'checkBox_11': {'label': 'Block New Installed Apps', 'default': False}
        }

        # Convert checkboxes to toggle switches and connect signals
        for checkbox_name, settings in self.settings_toggles.items():
            toggle = self.convert_checkbox_to_toggle(checkbox_name, settings['label'])
            if toggle:
                # Connect the signal to a handler that knows which setting was changed
                toggle.toggled.connect(lambda checked, name=checkbox_name: 
                    self.on_setting_changed(name, checked))

        # Add floating button
        self.floating_btn = FloatingButton(self, "notification")
        self.floating_btn.clicked.connect(self.show_notification_page)
        self.floating_btn.update_position("top-right")
        self.floating_btn.show()
        
        # Connect back button from notification page
        self.goBack_btn.clicked.connect(self.show_app_page)
        
        # Connect partner buttons
        if hasattr(self, 'addPartner_btn'):
            self.addPartner_btn.clicked.connect(self.show_partner_dialog)

    def initialize_user(self):
        """Check for existing verified user or show signup dialog"""
        # First check if we have a verified user
        existing_user = self.db.get_verified_user()
        if existing_user:
            # We have a verified user, load their data directly
            self._on_user_verified(existing_user)
        else:
            # No verified user, show signup dialog
            self.signup_dialog = SignUpDialog(self)  # Keep reference to prevent garbage collection
            self.signup_dialog.code_verified.connect(self._on_user_verified)
            self.signup_dialog.show()
        
    def _on_user_verified(self, email):
        """Called when user verification is successful"""
        self.user_email = email
        self.load_user_data()
        self.update_user_info()
        self.load_user_settings()  # Load saved settings
        integrate_with_main_window(self)

        # Cleanup dialog
        if hasattr(self, 'signup_dialog'):
            self.signup_dialog.deleteLater()
            del self.signup_dialog
            
        # Ensure proper widget visibility after login
        self.show()
        self.raise_()
        self.activateWindow()
        
    def show_account_details(self):
        """Switch to account details page"""
        # Switch to settings tab first
        if hasattr(self, 'tabWidget') and hasattr(self, 'settings_tab'):
            self.tabWidget.setCurrentWidget(self.settings_tab)
        
        # Then switch to account details in settings stacked widget
        if hasattr(self, 'settings_stackedWidget') and hasattr(self, 'accountDetails_page'):
            current_index = self.settings_stackedWidget.indexOf(self.accountDetails_page)
            if current_index != -1:
                self.settings_stackedWidget.setCurrentIndex(current_index)

    def on_user_verified(self, email):
        """Handle verified user"""
        self.user_email = email
        self.load_user_data()
        self.update_user_info()

        # Initialize focus mode manager for the verified user
        if not self.focus_mode_manager:
            self.focus_mode_manager = FocusModeManager(self)
        
        # Update account details page
        self.update_account_details()

            
    def closeEvent(self, event):
        """Handle window close event"""
        if self._program_loader:
            self._program_loader.stop()
            self._program_loader.deleteLater()
        event.accept()
        
    def update_user_info(self):
        """Update user information in settings tab"""
        if self.user_email:
            user_info = self.db.get_user_info(self.user_email)
            if user_info and user_info[0] and user_info[1]:  # Check if we have both email and username
                email, username = user_info
                self.username_lbl.setText(f"Hello {username}")
                # self.email_lbl.setText(email)
                
                # Update account details, blocked/whitelisted apps, and partner info
                self.update_account_details()
                self.load_saved_apps()
                self.update_partner_info()  # Load partner info
            else: 
                self.username_lbl.setText("Unknown")
                # self.email_lbl.setText(self.user_email or "Unknown")
                
    def load_saved_apps(self):
        """Load and display saved apps from the database"""
        # Clear existing items
        self.listWidget_2.clear()  # Block list
        self.listWidget_4.clear()  # White list
        
        # Get apps from database
        blocked_apps = self.db.get_items(self.user_email, 'block', 'app')
        whitelisted_apps = self.db.get_items(self.user_email, 'white', 'app')
        
        # Load apps from registry to get program info
        registry_apps = {}
        self._blocked_apps = blocked_apps
        self._whitelisted_apps = whitelisted_apps
        
        # Clean up old program loader if it exists
        if self._program_loader:
            self._program_loader.stop()
            self._program_loader.deleteLater()
            
        self._program_loader = ProgramLoader()
        self._program_loader.programs_loaded.connect(self._on_programs_loaded)
        self._program_loader.start()  # Start loading in background
        
    def _on_programs_loaded(self, apps):
        """Handle loaded program data"""
        registry_apps = {}
        # Process each app
        for app in apps:
            app_path = app['icon_path'].split(',')[0].strip('"') if app['icon_path'] else app['install_location']
            if app_path:
                registry_apps[app_path] = app
                
        # Now add the apps to the lists
        self._populate_app_lists(self._blocked_apps, self._whitelisted_apps, registry_apps)
        
    def _populate_app_lists(self, blocked_apps, whitelisted_apps, registry_apps):
        """Populate the app lists with program data"""
        # Clear existing items
        self.listWidget_2.clear()
        self.listWidget_4.clear()
        
        # Add blocked apps
        for app_path in blocked_apps:
            if app_path in registry_apps:
                item = QListWidgetItem()
                program_widget = ProgramListItem(registry_apps[app_path])
                item.setSizeHint(program_widget.sizeHint())
                self.listWidget_2.addItem(item)
                self.listWidget_2.setItemWidget(item, program_widget)
            else:
                # Fallback for apps not found in registry
                item = QListWidgetItem(app_path)
                self.listWidget_2.addItem(item)
        
        # Add whitelisted apps
        for app_path in whitelisted_apps:
            if app_path in registry_apps:
                item = QListWidgetItem()
                program_widget = ProgramListItem(registry_apps[app_path])
                item.setSizeHint(program_widget.sizeHint())
                self.listWidget_4.addItem(item)
                self.listWidget_4.setItemWidget(item, program_widget)
            else:
                # Fallback for apps not found in registry
                item = QListWidgetItem(app_path)
                self.listWidget_4.addItem(item)
                self.listWidget_4.addItem(item)
                self.listWidget_4.setItemWidget(item, program_widget)


    def update_account_details(self):
        """Update the account details page with user information"""
        user_info = self.db.get_user_info(self.user_email)
        if user_info and user_info[0] and user_info[1]:
            email, username = user_info
            
            # Update user details in the UI
            if hasattr(self, 'userDetails_grbx'):
                # Update group box title with username
                self.userDetails_grbx.setTitle(f"{username}")
                
                # Update email label
                user_label = self.userDetails_grbx.findChild(QLabel, "label_7")
                email_label = self.userDetails_grbx.findChild(QLabel, "label_8")
                login_time_label = self.userDetails_grbx.findChild(QLabel, "label_11")

                if user_label:
                    user_label.setText(f"User Name: {username}")
                else:
                    user_label.setText(f"User Name: Developper")

                if email_label:
                    email_label.setText(f"Email: {email}")
                else:
                    email_label.setText(f"Email: dev@example.com")
                
                login_time_label.setText(f"Last Login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")               
                login_time_label.setStyleSheet("color: #09c; font-size: 14px;")
            
            # Make sure we're on the settings tab
            # if hasattr(self, 'tabWidget'):
            #     self.tabWidget.setCurrentWidget(self.settings_tab)
            
            # Switch to account details page in settings
            # if hasattr(self, 'settings_stackedWidget'):
            #     self.settings_stackedWidget.setCurrentWidget(self.accountDetails_page)

    def load_user_data(self):
        """Load user's blocked and whitelisted items into all list widgets"""
        # Clear all lists first
        self.listWidget.clear()   # Block list - websites
        self.listWidget_2.clear() # Block list - apps
        self.listWidget_3.clear() # White list - websites
        self.listWidget_4.clear() # White list - apps
            
        # Load blocked websites
        for item in self.db.get_items(self.user_email, 'block', 'website'):
            self.listWidget.addItem(item)
            
        # Load blocked apps
        for item in self.db.get_items(self.user_email, 'block', 'app'):
            self.listWidget_2.addItem(item)
            
        # Load whitelisted websites
        for item in self.db.get_items(self.user_email, 'white', 'website'):
            self.listWidget_3.addItem(item)  # Website whitelist goes to listWidget_3
            
        # Load whitelisted apps
        for item in self.db.get_items(self.user_email, 'white', 'app'):
            self.listWidget_4.addItem(item)  # App whitelist goes to listWidget_4

        # Initialize focus mode manager after user data is loaded
        if not self.focus_mode_manager:
            self.focus_mode_manager = FocusModeManager(self)
        else:
            self.focus_mode_manager.on_user_loaded()

            
    def show_block_list_page(self):
        """Show the block list page"""
        # Update button states
        self.blockList_btn.setChecked(True)
        self.whiteList_btn.setChecked(False)
        # # Switch to block list page
        self.stackedWidget_blkLst.setCurrentWidget(self.BlockList_page)
        
        fade_in_widget(self.BlockList_page)

    def show_white_list_page(self):
        """Show the white list page"""
        # Update button states
        self.whiteList_btn.setChecked(True)
        self.blockList_btn.setChecked(False)

        self.stackedWidget_blkLst.setCurrentWidget(self.WhiteList_page)

        fade_in_widget(self.WhiteList_page)

    def show_notification_page(self):
        """Show the notification page with slide right animation"""
        self.stackedWidget_2.setCurrentWidget(self.notification_page)
        slide_widget(self.notification_page, direction="right")

    def show_app_page(self):
        """Show the main app page with slide left animation"""
        self.stackedWidget_2.setCurrentWidget(self.app_page)
        slide_widget(self.app_page, direction="left")

    def add_website(self, line_edit, list_widget):
        """Add a website/keyword to the specified list"""
        text = line_edit.text().strip()
        if text:
            # Determine if this is for block list or white list
            list_type = 'block' if list_widget in [self.listWidget, self.listWidget_2] else 'white'
            success, message = self.db.add_item(self.user_email, text, list_type, 'website')
            if success:
                list_widget.addItem(text)  # Add to the correct list widget
                line_edit.clear()
                self.show_status_message(f"Added website/keyword to {list_type}list: {text}")
            else:
                QMessageBox.warning(self, "Cannot Add Item", message)
                self.show_status_message(message, 2000)
        else:
            self.show_status_message("Please enter a website or keyword", 2000)

    def remove_website(self, list_widget):
        """Remove selected website or app from list"""
        selected_items = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            if widget and hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
                selected_items.append((i, item, widget))
                
        if not selected_items:
            # Fall back to old selection method for websites
            selected_items = [(list_widget.row(item), item, None) for item in list_widget.selectedItems()]
            
        if not selected_items:
            self.show_status_message("Please select items to remove", 2000)
            return
            
        success_count = 0
        # Remove items in reverse order to maintain indices
        for i, item, widget in reversed(selected_items):
            # Determine list type based on which list widget is being used
            list_type = 'block'
            if list_widget == self.listWidget_3 or list_widget == self.listWidget_4:
                list_type = 'white'
                
            # Get item text and type
            if widget and hasattr(widget, 'program_data'):
                # For program items
                item_text = widget.program_data['icon_path'].split(',')[0].strip('"') \
                    if widget.program_data['icon_path'] else widget.program_data['install_location']
                item_type = 'app'
            else:
                # For website items
                item_text = item.text()
                item_type = 'website'
            
            # Remove from database first - only need email and item
            if self.db.remove_item(self.user_email, item_text):
                list_widget.takeItem(i)
                success_count += 1
                
        if success_count > 0:
            self.show_status_message(
                f"Removed {success_count} {'item' if success_count == 1 else 'items'}")
        else:
            self.show_status_message("Failed to remove items", 2000)
    
    def show_status_message(self, message, timeout=2000):
        """Show a status message in the statusbar"""
        self.statusBar().showMessage(message, timeout)
        
    def setup_list_widgets(self):
        """Configure list widgets for better appearance and behavior"""
        list_widgets = [self.listWidget_2, self.listWidget_4]  # App list widgets
        for list_widget in list_widgets:
            list_widget.setAlternatingRowColors(True)
            list_widget.setSelectionMode(QListWidget.NoSelection)  # Selection is handled by checkboxes
            
            
    def get_installed_apps(self):
        """Get list of installed applications"""
        apps = []
        # Check both 32-bit and 64-bit registry
        for hkey in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for flag in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
                try:
                    reg_key = winreg.OpenKey(hkey, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall", 
                                           0, winreg.KEY_READ | flag)
                    
                    for i in range(winreg.QueryInfoKey(reg_key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(reg_key, i)
                            subkey = winreg.OpenKey(reg_key, subkey_name)
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                if display_name and install_location:
                                    # Look for the .exe file in the install location
                                    for root, _, files in os.walk(install_location):
                                        for file in files:
                                            if file.lower().endswith('.exe'):
                                                exe_path = os.path.join(root, file)
                                                apps.append((display_name, exe_path))
                                                break
                            except (WindowsError, KeyError):
                                continue
                            finally:
                                winreg.CloseKey(subkey)
                        except WindowsError:
                            continue
                except WindowsError:
                    continue
                finally:
                    try:
                        winreg.CloseKey(reg_key)
                    except WindowsError:
                        continue
        return sorted(set(apps))  # Remove duplicates and sort
        
    def load_user_settings(self):
        """Load user's saved settings and update toggle switches"""
        # Load block screen timer value
        if hasattr(self, 'spinBox'):
            timer_value = self.db.get_setting(self.user_email, 'block_screen_timer')
            if timer_value is not None:
                try:
                    self.spinBox.setValue(int(timer_value))
                    print(f"Loaded block screen timer value: {timer_value}")
                except (ValueError, TypeError):
                    print(f"Invalid block screen timer value: {timer_value}")
                    self.spinBox.setValue(30)  # Default value
            else:
                # Save default value if none exists
                print("Setting default block screen timer value")
                self.db.update_setting(self.user_email, 'block_screen_timer', '30', 'number')
                
        # Load redirect URL value
        if hasattr(self, 'lineEdit_2'):
            redirect_url = self.db.get_setting(self.user_email, 'redirect_url')
            if redirect_url:
                print(f"Loading saved redirect URL: {redirect_url}")
                self.lineEdit_2.setText(redirect_url)
            else:
                # Save default value if none exists
                default_url = "https://www.google.com"
                print(f"Setting default redirect URL: {default_url}")
                self.lineEdit_2.setText(default_url)
                self.db.update_setting(self.user_email, 'redirect_url', default_url)
                
        # Load block screen message
        if hasattr(self, 'plainTextEdit'):
            message = self.db.get_setting(self.user_email, 'block_screen_message')
            if message:
                print(f"Loading saved block screen message")
                self.plainTextEdit.setPlainText(message)
            else:
                # Save default message if none exists
                default_message = """<div style='text-align: center; font-size: 18px; color: #2c3e50;'>
<h2>اتقي الله في نفسك</h2>
<p>This content has been blocked for your protection.</p>
<p>Content blocking helps maintain a safe browsing environment.</p>
</div>"""
                print("Setting default block screen message")
                self.plainTextEdit.setPlainText(default_message)
                self.db.update_setting(self.user_email, 'block_screen_message', default_message)
        if not self.user_email:
            return

        # For each setting, load its value and update the toggle
        for checkbox_name, settings in self.settings_toggles.items():
            # Get saved value or use default
            saved_value = self.db.get_setting(self.user_email, checkbox_name)
            value = saved_value if saved_value is not None else settings['default']
            
            # Update the toggle switch
            toggle = getattr(self, f"{checkbox_name}_toggle", None)
            if toggle:
                # Temporarily disconnect the signal to prevent triggering the change handler
                toggle.blockSignals(True)
                toggle.setChecked(value)
                toggle.blockSignals(False)

    def show_app_selection_dialog(self, list_widget):
        """Show dialog to select applications to block/whitelist"""
        from .app_selector import ProgramSelectorDialog, ProgramListItem
        dialog = ProgramSelectorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Determine if this is for block list or white list
            list_type = 'block' if list_widget == self.listWidget_2 else 'white'
            
            # Track existing programs to avoid duplicates
            existing_programs = set()
            target_list = self.listWidget_2 if list_type == 'block' else self.listWidget_4
            
            for i in range(target_list.count()):
                item = target_list.item(i)
                widget = target_list.itemWidget(item)
                if widget and hasattr(widget, 'program_data'):
                    existing_programs.add(widget.program_data['name'])
            
            for program in dialog.selected_programs:
                if program['name'] in existing_programs:
                    continue
                    
                app_path = program['icon_path'].split(',')[0].strip('"') if program['icon_path'] else program['install_location']
                if not app_path:
                    continue

                success, message = self.db.add_item(self.user_email, app_path, list_type, 'app')
                if success:
                    item = QListWidgetItem()
                    program_widget = ProgramListItem(program)
                    item.setSizeHint(program_widget.sizeHint())
                    target_list.addItem(item)
                    target_list.setItemWidget(item, program_widget)
                else:
                    QMessageBox.warning(self, "Cannot Add App", message)
                    
    def add_whitelist_apps(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Applications", "", "Applications (*.exe)")
        if files:
            count = 0
            for file in files:
                app_name = os.path.basename(file)
                # Check for duplicates and cross-list conflicts
                if not self.db.is_app_in_any_list(self.user_email, file):
                    item = QListWidgetItem(QIcon(file), app_name)
                    item.setData(Qt.UserRole, file)
                    self.listWidget_4.addItem(item)  # <-- Correct widget for whitelist apps
                    self.db.add_item(self.user_email, file, 'white', 'app')
                    count += 1
                else:
                    self.show_status_message(f"App '{app_name}' already exists in a list", 2000)
            self.show_status_message(f"Added {count} {'application' if count == 1 else 'applications'} to whitelist")
        else:
            self.show_status_message("No applications selected", 2000)
        
    def on_menu_requested(self, pos):
        """Handle floating button menu request"""
        panel = FloatingPanel(self)
        panel.move(pos)
        panel.show()

    def setup_settings_connections(self):
        """Setup signal connections for settings tab"""
        # Connect spinbox value changed signal
        if hasattr(self, 'spinBox'):
            self.spinBox.valueChanged.connect(self.on_countdown_value_changed)
            
        # Connect redirect URL line edit
        if hasattr(self, 'lineEdit_2'):
            self.lineEdit_2.textChanged.connect(self.on_redirect_url_changed)
            
        # Connect block screen message
        if hasattr(self, 'plainTextEdit'):
            self.plainTextEdit.textChanged.connect(self.on_block_message_changed)
            
    def on_block_message_changed(self):
        """Handle changes to the block screen message"""
        message = self.plainTextEdit.toPlainText()
        print(f"Saving new block screen message: {message}")
        success = self.db.update_setting(self.user_email, 'block_screen_message', message)
        if success:
            print("Successfully saved block screen message")
            self.show_status_message("Block screen message updated", 2000)
        else:
            print("Failed to save block screen message")
            self.show_status_message("Failed to update block screen message", 2000)
            # Revert to old value
            old_message = self.db.get_setting(self.user_email, 'block_screen_message')
            if old_message:
                self.plainTextEdit.setPlainText(old_message)
            
    def on_redirect_url_changed(self, url: str):
        """Handle changes to the redirect URL"""
        if not url:
            url = "https://www.google.com"
        # Ensure URL has http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        print(f"Saving new redirect URL: {url}")
        success = self.db.update_setting(self.user_email, 'redirect_url', url)
        if success:
            print("Successfully saved redirect URL")
            self.show_status_message(f"Redirect URL updated", 2000)
        else:
            print("Failed to save redirect URL")
            self.show_status_message("Failed to update redirect URL", 2000)
            # Revert to old value
            old_url = self.db.get_setting(self.user_email, 'redirect_url')
            if old_url:
                self.lineEdit_2.setText(old_url)

    def on_countdown_value_changed(self, value):
        """Handle changes to the countdown spinbox value"""
        print(f"Saving new countdown value: {value}")
        success = self.db.update_setting(self.user_email, 'block_screen_timer', str(value), 'number')
        if success:
            print(f"Successfully saved countdown value: {value}")
            self.show_status_message(f"Block screen countdown updated to {value} seconds", 2000)
        else:
            print("Failed to save countdown value")
            self.show_status_message("Failed to update countdown value", 2000)
            # Revert to old value
            old_value = self.db.get_setting(self.user_email, 'block_screen_timer')
            if old_value:
                try:
                    self.spinBox.setValue(int(old_value))
                except (ValueError, TypeError):
                    self.spinBox.setValue(30)    
        # Connect the buttons to show their respective pages
        self.general_btn.clicked.connect(lambda: self.show_settings_page('general'))
        self.accountDetails_btn.clicked.connect(lambda: self.show_settings_page('account'))
        self.accPartners_btn.clicked.connect(lambda: self.show_settings_page('partners'))

        # Set initial active button
        self.general_btn.setChecked(True)
        self.settings_stackedWidget.setCurrentWidget(self.general_page)
        

    def show_settings_page(self, page_type):
        """
        Show the selected settings page and update button states
        """
        # Reset all button states
        self.general_btn.setChecked(False)
        self.accountDetails_btn.setChecked(False)
        self.accPartners_btn.setChecked(False)
        
        # Set the active page and button state
        if page_type == 'general':
            self.settings_stackedWidget.setCurrentWidget(self.general_page)
            self.general_btn.setChecked(True)
        elif page_type == 'account':
            self.settings_stackedWidget.setCurrentWidget(self.accountDetails_page)
            self.accountDetails_btn.setChecked(True)
        elif page_type == 'partners':
            self.settings_stackedWidget.setCurrentWidget(self.accPartners_page)
            self.accPartners_btn.setChecked(True)


    def convert_checkbox_to_toggle(self, checkbox_name, label_text):
        """Convert a checkbox to a toggle switch with label"""
        if hasattr(self, checkbox_name):
            # Get the original checkbox
            old_checkbox = getattr(self, checkbox_name)
            parent_layout = old_checkbox.parent().layout()
            
            # Create new widget to hold the horizontal layout
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create label with original text
            label = QLabel(label_text)
            label.setStyleSheet("color: #424242; font-size: 14px;")
            
            # Create toggle switch
            toggle = ToggleSwitch(width=50, height=25)
            toggle.setChecked(old_checkbox.isChecked())
            
            # Add to horizontal layout
            h_layout.addWidget(label)
            h_layout.addStretch()
            h_layout.addWidget(toggle)
            
            # Get the index of the old checkbox in its parent layout
            index = parent_layout.indexOf(old_checkbox)
            
            # Remove old checkbox and add new container
            old_checkbox.hide()
            parent_layout.removeWidget(old_checkbox)
            parent_layout.insertWidget(index, container)
            old_checkbox.deleteLater()
            
            # Store the toggle switch
            setattr(self, f"{checkbox_name}_toggle", toggle)
            return toggle
            
        return None

    def toggle_autostart(self, enabled):
        """Handle autostart toggle"""
        self.show_status_message(
            f"Autostart {'enabled' if enabled else 'disabled'}"
        )
        # TODO: Implement autostart functionality
        
    def toggle_notifications(self, enabled):
        """Handle notifications toggle"""
        self.show_status_message(
            f"Notifications {'enabled' if enabled else 'disabled'}"
        )
        # TODO: Implement notifications functionality
        
    def toggle_sound(self, enabled):
        """Handle sound toggle"""
        self.show_status_message(
            f"Sound {'enabled' if enabled else 'disabled'}"
        )
        # TODO: Implement sound functionality
        
    def show_partner_dialog(self):
        """Show dialog to add accountability partner"""
        dialog = PartnerDialog(self)
        dialog.partner_verified.connect(lambda email, name: self.update_partner_info())
        dialog.exec_()  # Use exec_() for modal dialogs
        
    def update_partner_info(self):
        """Update partner information in the UI"""
        if self.user_email:
            partner_info = self.db.get_partner_info(self.user_email)
            if partner_info and len(partner_info) == 2:
                partner_name, partner_email = partner_info
                
                # Update partner info in UI
                if hasattr(self, 'partnerInfo_grbx'):
                    name_label = self.partnerInfo_grbx.findChild(QLabel, "label_5")
                    email_label = self.partnerInfo_grbx.findChild(QLabel, "label_6")
                    
                    if name_label:
                        name_label.setText(f"Name: {partner_name}")
                    if email_label:
                        email_label.setText(f"Email: {partner_email}")
                        
    def on_setting_changed(self, setting_name, checked):
        """Handle changes to toggle switches in settings"""
        # Update the setting in the database
        success = self.db.update_setting(self.user_email, setting_name, str(checked), 'boolean')
        
        if success:
            # Show a status message
            setting_label = self.settings_toggles[setting_name]['label']
            self.show_status_message(
                f"{setting_label} {'enabled' if checked else 'disabled'}")
            
            # If this is a critical setting that requires partner approval
            critical_settings = ['checkBox_6']  # Uninstall Protection
            if setting_name in critical_settings:
                # Show setting change request dialog
                from .settings_change_dialog import SettingsChangeDialog
                dialog = SettingsChangeDialog(
                    self, 
                    setting_name=setting_name,
                    current_value=str(checked)
                )
                dialog.exec_()
        else:
            # Revert the toggle if the update failed
            toggle = getattr(self, f"{setting_name}_toggle", None)
            if toggle:
                toggle.setChecked(not checked)
            self.show_status_message("Failed to update setting", 2000)

    def on_partner_added(self):
        """Called when a partner is successfully added"""
        self.update_partner_info()
        self.tabWidget.setCurrentWidget(self.settings_tab)
        self.settings_stackedWidget.setCurrentWidget(self.accPartners_page)
        self.accPartners_btn.setChecked(True)


