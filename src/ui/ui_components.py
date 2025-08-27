import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QAction, 
                            QGraphicsDropShadowEffect, QLabel, QFrame)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtWidgets import QAbstractButton


# Custom Toggle Switch Widget
class ToggleSwitch(QAbstractButton):
    """
    Custom Toggle Switch Widget
    """
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None, width=60, height=30):
        super().__init__(parent)
        self.setCheckable(True)
        
        # Dimensions
        self._width = width
        self._height = height
        self._margin = 3
        
        # Colors
        self._bg_color_off = QColor("#777777")
        self._bg_color_on = QColor("#4CAF50")
        self._circle_color = QColor("#FFFFFF")
        self._disabled_color = QColor("#CCCCCC")
        
        # Animation
        self._circle_position = self._margin
        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)
        
        # Connect signals
        self.clicked.connect(self.start_transition)
        
        # Set size
        self.setFixedSize(self._width, self._height)
    
    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def start_transition(self):
        """Start the toggle animation"""
        self.animation.stop()
        if self.isChecked():
            self.animation.setStartValue(self._margin)
            self.animation.setEndValue(self._width - self._height + self._margin)
        else:
            self.animation.setStartValue(self._width - self._height + self._margin)
            self.animation.setEndValue(self._margin)
        
        self.animation.start()
        self.toggled.emit(self.isChecked())
    
    def paintEvent(self, event):
        """Custom paint event"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Disable pen
        painter.setPen(QPen(Qt.NoPen))
        
        # Background
        if self.isEnabled():
            bg_color = self._bg_color_on if self.isChecked() else self._bg_color_off
        else:
            bg_color = self._disabled_color
            
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, self._width, self._height, self._height/2, self._height/2)
        
        # Circle
        circle_color = self._circle_color if self.isEnabled() else QColor("#EEEEEE")
        painter.setBrush(QBrush(circle_color))
        
        circle_size = self._height - 2 * self._margin
        painter.drawEllipse(int(self._circle_position), self._margin, circle_size, circle_size)
    
    def setChecked(self, checked):
        """Override setChecked to update position without animation"""
        super().setChecked(checked)
        if checked:
            self._circle_position = self._width - self._height + self._margin
        else:
            self._circle_position = self._margin
        self.update()

class SimpleToggleSwitch(QWidget):
    """
    Simpler toggle switch using styled QPushButton
    """
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None, width=50, height=25):
        super().__init__(parent)
        self.setFixedSize(width, height)
        
        self.button = QPushButton(self)
        self.button.setCheckable(True)
        self.button.setFixedSize(width, height)
        
        # Style the button to look like a toggle switch
        self.set_style()
        
        # Connect signal
        self.button.toggled.connect(self.on_toggled)
    
    def set_style(self):
        """Set the toggle switch style"""
        style = """
        QPushButton {
            border: 2px solid #777777;
            border-radius: 12px;
            background-color: #777777;
            color: white;
            font-weight: bold;
            font-size: 10px;
        }
        QPushButton:checked {
            border: 2px solid #4CAF50;
            background-color: #4CAF50;
        }
        QPushButton:hover {
            border: 2px solid #555555;
        }
        QPushButton:checked:hover {
            border: 2px solid #45a049;
            background-color: #45a049;
        }
        QPushButton:disabled {
            border: 2px solid #CCCCCC;
            background-color: #CCCCCC;
        }
        """
        self.button.setStyleSheet(style)
        self.update_text()
    
    def update_text(self):
        """Update button text based on state"""
        if self.button.isChecked():
            self.button.setText("ON")
        else:
            self.button.setText("OFF")
    
    def on_toggled(self, checked):
        """Handle toggle event"""
        self.update_text()
        self.toggled.emit(checked)
    
    def isChecked(self):
        """Return checked state"""
        return self.button.isChecked()
    
    def setChecked(self, checked):
        """Set checked state"""
        self.button.setChecked(checked)
        self.update_text()
    
    def setEnabled(self, enabled):
        """Set enabled state"""
        super().setEnabled(enabled)
        self.button.setEnabled(enabled)

class ModernToggleSwitch(QAbstractButton):
    """
    Modern iOS-style toggle switch
    """
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None, width=50, height=25):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(width, height)
        
        # Properties
        self._width = width
        self._height = height
        self._margin = 2
        
        # Colors
        self._bg_color_off = QColor("#E0E0E0")
        self._bg_color_on = QColor("#2196F3")
        self._circle_color = QColor("#FFFFFF")
        self._border_color_off = QColor("#CCCCCC")
        self._border_color_on = QColor("#2196F3")
        
        # Animation properties
        self._circle_position = self._margin
        self._bg_color = self._bg_color_off
        
        # Animations
        self.position_animation = QPropertyAnimation(self, b"circle_position")
        self.position_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.position_animation.setDuration(150)
        
        self.color_animation = QPropertyAnimation(self, b"bg_color")
        self.color_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.color_animation.setDuration(150)
        
        # Connect signals
        self.clicked.connect(self.start_transition)
    
    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    @pyqtProperty(QColor)
    def bg_color(self):
        return self._bg_color
    
    @bg_color.setter
    def bg_color(self, color):
        self._bg_color = color
        self.update()
    
    def start_transition(self):
        """Start the toggle animation"""
        # Stop any running animations
        self.position_animation.stop()
        self.color_animation.stop()
        
        # Position animation
        if self.isChecked():
            start_pos = self._margin
            end_pos = self._width - self._height + self._margin
        else:
            start_pos = self._width - self._height + self._margin
            end_pos = self._margin
        
        self.position_animation.setStartValue(start_pos)
        self.position_animation.setEndValue(end_pos)
        
        # Color animation
        if self.isChecked():
            self.color_animation.setStartValue(self._bg_color_off)
            self.color_animation.setEndValue(self._bg_color_on)
        else:
            self.color_animation.setStartValue(self._bg_color_on)
            self.color_animation.setEndValue(self._bg_color_off)
        
        # Start animations
        self.position_animation.start()
        self.color_animation.start()
        
        self.toggled.emit(self.isChecked())
    
    def paintEvent(self, event):
        """Custom paint event"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background with border
        border_color = self._border_color_on if self.isChecked() else self._border_color_off
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(self._bg_color))
        
        rect = QRect(0, 0, self._width, self._height)
        painter.drawRoundedRect(rect, self._height/2, self._height/2)
        
        # Circle (thumb)
        painter.setPen(QPen(QColor("#DDDDDD"), 0.5))
        painter.setBrush(QBrush(self._circle_color))
        
        circle_size = self._height - 2 * self._margin - 2
        circle_y = self._margin + 1
        
        painter.drawEllipse(int(self._circle_position), circle_y, circle_size, circle_size)
    
    def setChecked(self, checked):
        """Override setChecked to update position without animation"""
        super().setChecked(checked)
        if checked:
            self._circle_position = self._width - self._height + self._margin
            self._bg_color = self._bg_color_on
        else:
            self._circle_position = self._margin
            self._bg_color = self._bg_color_off
        self.update()

# Demo application
class ToggleSwitchDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toggle Switch Demo")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Custom animated toggle
        layout.addWidget(QLabel("Custom Animated Toggle Switch:"))
        self.toggle1 = ToggleSwitch(width=60, height=30)
        self.toggle1.toggled.connect(lambda checked: print(f"Toggle 1: {checked}"))
        
        toggle1_layout = QHBoxLayout()
        toggle1_layout.addWidget(self.toggle1)
        toggle1_layout.addWidget(QLabel("Enable Feature"))
        toggle1_layout.addStretch()
        
        toggle1_widget = QWidget()
        toggle1_widget.setLayout(toggle1_layout)
        layout.addWidget(toggle1_widget)
        
        # Simple styled toggle
        layout.addWidget(QLabel("Simple Styled Toggle Switch:"))
        self.toggle2 = SimpleToggleSwitch(width=50, height=25)
        self.toggle2.toggled.connect(lambda checked: print(f"Toggle 2: {checked}"))
        
        toggle2_layout = QHBoxLayout()
        toggle2_layout.addWidget(self.toggle2)
        toggle2_layout.addWidget(QLabel("Dark Mode"))
        toggle2_layout.addStretch()
        
        toggle2_widget = QWidget()
        toggle2_widget.setLayout(toggle2_layout)
        layout.addWidget(toggle2_widget)
        
        # Modern iOS-style toggle
        layout.addWidget(QLabel("Modern iOS-style Toggle Switch:"))
        self.toggle3 = ModernToggleSwitch(width=50, height=25)
        self.toggle3.toggled.connect(lambda checked: print(f"Toggle 3: {checked}"))
        
        toggle3_layout = QHBoxLayout()
        toggle3_layout.addWidget(self.toggle3)
        toggle3_layout.addWidget(QLabel("Notifications"))
        toggle3_layout.addStretch()
        
        toggle3_widget = QWidget()
        toggle3_widget.setLayout(toggle3_layout)
        layout.addWidget(toggle3_widget)
        
        # Control buttons
        layout.addWidget(QLabel("Controls:"))
        
        btn_layout = QHBoxLayout()
        
        enable_btn = QPushButton("Toggle All")
        enable_btn.clicked.connect(self.toggle_all)
        btn_layout.addWidget(enable_btn)
        
        disable_btn = QPushButton("Disable All")
        disable_btn.clicked.connect(self.disable_all)
        btn_layout.addWidget(disable_btn)
        
        enable_all_btn = QPushButton("Enable All")
        enable_all_btn.clicked.connect(self.enable_all)
        btn_layout.addWidget(enable_all_btn)
        
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        layout.addWidget(btn_widget)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def toggle_all(self):
        """Toggle all switches"""
        self.toggle1.setChecked(not self.toggle1.isChecked())
        self.toggle2.setChecked(not self.toggle2.isChecked())
        self.toggle3.setChecked(not self.toggle3.isChecked())
    
    def disable_all(self):
        """Disable all switches"""
        self.toggle1.setEnabled(False)
        self.toggle2.setEnabled(False)
        self.toggle3.setEnabled(False)
    
    def enable_all(self):
        """Enable all switches"""
        self.toggle1.setEnabled(True)
        self.toggle2.setEnabled(True)
        self.toggle3.setEnabled(True)



# Custom Floating Button Class

class FloatingButton(QPushButton):
    """
    A floating action button that stays on top of other widgets
    """
    
    # Custom signals
    menuRequested = pyqtSignal()
    settingsRequested = pyqtSignal()
    helpRequested = pyqtSignal()
    
    def __init__(self, parent=None, button_type="notification"):
        super().__init__(parent)
        self.button_type = button_type
        self._setup_button()
        
    def _setup_button(self):
        """Setup the floating button appearance"""
        self.setText("🔔")  # Bell emoji for notifications
        self.setToolTip("Notifications")
        self.setFixedSize(40, 40)
        
        # Apply modern styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                border-radius: 20px;
                color: white;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
        
    def update_position(self, position="top-right"):
        """Update button position relative to parent window"""
        if not self.parentWidget():
            return
            
        parent_rect = self.parentWidget().rect()
        margin = 1  # Distance from window edges
        
        if position == "top-right":
            x = parent_rect.width() - self.width() - margin
            y = margin
        elif position == "top-left":
            x = margin
            y = margin
        elif position == "bottom-right":
            x = parent_rect.width() - self.width() - margin
            y = parent_rect.height() - self.height() - margin
        elif position == "bottom-left":
            x = margin
            y = parent_rect.height() - self.height() - margin
        
        self.move(x, y)
        
    # def _setup_animations(self):
    #     """Setup animations for the button"""
    #     self.animation = QPropertyAnimation(self, b"geometry")
    #     self.animation.setDuration(300)
    #     self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    # def _setup_menu(self):
    #     """Setup context menu for the button"""
    #     self.context_menu = QMenu(self)
        
    #     # Add menu actions
    #     menu_action = QAction("📋 Menu", self)
    #     menu_action.triggered.connect(self.menuRequested.emit)
    #     self.context_menu.addAction(menu_action)
        
    #     settings_action = QAction("⚙️ Settings", self)
    #     settings_action.triggered.connect(self.settingsRequested.emit)
    #     self.context_menu.addAction(settings_action)
        
    #     self.context_menu.addSeparator()
        
    #     help_action = QAction("❓ Help", self)
    #     help_action.triggered.connect(self.helpRequested.emit)
    #     self.context_menu.addAction(help_action)
        
    # def _on_button_clicked(self):
    #     """Handle button click"""
    #     if self.button_type == "menu":
    #         self.show_context_menu()
    #     else:
    #         # Emit appropriate signal based on button type
    #         if self.button_type == "settings":
    #             self.settingsRequested.emit()
    #         elif self.button_type == "help":
    #             self.helpRequested.emit()
    #         else:
    #             self.show_context_menu()
    
    # def show_context_menu(self):
    #     """Show the context menu"""
    #     self.context_menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))
    
    # def update_position(self, position="top-right"):
    #     """Update button position relative to parent"""
    #     if not self.parent_widget:
    #         return
            
    #     parent_rect = self.parent_widget.rect()
        
    #     if position == "top-right":
    #         x = parent_rect.width() - self.width() - self.margin
    #         y = self.margin + 0  # Account for title bar and tabs
    #     elif position == "top-left":
    #         x = self.margin
    #         y = self.margin + 0
    #     elif position == "bottom-right":
    #         x = parent_rect.width() - self.width() - self.margin
    #         y = parent_rect.height() - self.height() - self.margin
    #     elif position == "bottom-left":
    #         x = self.margin
    #         y = parent_rect.height() - self.height() - self.margin
    #     else:  # center
    #         x = (parent_rect.width() - self.width()) // 2
    #         y = (parent_rect.height() - self.height()) // 2
            
    #     self.move(x, y)
        
    # def animate_to_position(self, position="top-right"):
    #     """Animate button to new position"""
    #     if not self.parent_widget:
    #         return
            
    #     parent_rect = self.parent_widget.rect()
    #     current_rect = self.geometry()
        
    #     if position == "top-right":
    #         target_x = parent_rect.width() - self.width() - self.margin
    #         target_y = self.margin + 35
    #     else:
    #         # Add more positions as needed
    #         target_x = current_rect.x()
    #         target_y = current_rect.y()
            
    #     target_rect = QRect(target_x, target_y, self.width(), self.height())
        
    #     self.animation.setStartValue(current_rect)
    #     self.animation.setEndValue(target_rect)
    #     self.animation.start()
        
    # def set_margin(self, margin):
    #     """Set the margin from window edges"""
    #     self.margin = margin
    #     self.update_position()



class FloatingButtonManager:
    """
    Manager class to handle multiple floating buttons
    """
    
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.buttons = {}
        self.default_position = "top-right"
        
    def add_button(self, name, button_type="default", position=None):
        """Add a floating button"""
        if position is None:
            position = self.default_position
            
        button = FloatingButton(self.parent_widget, button_type)
        button.update_position(position)
        button.raise_()
        button.show()
        
        self.buttons[name] = button
        return button
        
    def remove_button(self, name):
        """Remove a floating button"""
        if name in self.buttons:
            self.buttons[name].hide()
            self.buttons[name].deleteLater()
            del self.buttons[name]
            
    def get_button(self, name):
        """Get a floating button by name"""
        return self.buttons.get(name)
        
    def update_all_positions(self):
        """Update positions of all buttons when parent resizes"""
        for button in self.buttons.values():
            button.update_position()
            
    def hide_all(self):
        """Hide all floating buttons"""
        for button in self.buttons.values():
            button.hide()
            
    def show_all(self):
        """Show all floating buttons"""
        for button in self.buttons.values():
            button.show()
            button.raise_()


class CustomNotification(QFrame):
    """
    Custom notification widget that can float over other widgets
    """
    
    def __init__(self, parent=None, message="", notification_type="info"):
        super().__init__(parent)
        self.parent_widget = parent
        self.notification_type = notification_type
        self.setup_ui(message)
        
    def setup_ui(self, message):
        """Setup the notification UI"""
        self.setFixedSize(300, 80)
        self.setFrameStyle(QFrame.StyledPanel)
        
        # Create layout and add message label
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
        
        layout = QVBoxLayout()
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.message_label)
        self.setLayout(layout)
        
        # Style based on notification type
        self.apply_styling()
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide_notification)
        
    def apply_styling(self):
        """Apply styling based on notification type"""
        if self.notification_type == "success":
            bg_color = "#4CAF50"
        elif self.notification_type == "warning":
            bg_color = "#FF9800"
        elif self.notification_type == "error":
            bg_color = "#F44336"
        else:  # info
            bg_color = "#2196F3"
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: none;
            }}
            QLabel {{
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        
    def show_notification(self, duration=3000):
        """Show the notification for specified duration"""
        if self.parent_widget:
            # Position at top-center of parent
            parent_rect = self.parent_widget.rect()
            x = (parent_rect.width() - self.width()) // 2
            y = 50
            self.move(x, y)
            
        self.show()
        self.raise_()
        
        # Start hide timer
        self.hide_timer.start(duration)
        
    def hide_notification(self):
        """Hide the notification"""
        self.hide_timer.stop()
        self.hide()


class FloatingPanel(QFrame):
    """
    A floating panel that can contain multiple widgets
    """
    
    def __init__(self, parent=None, title="Panel"):
        super().__init__(parent)
        self.parent_widget = parent
        self.title = title
        self.is_collapsed = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the floating panel UI"""
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
        
        self.setFixedSize(250, 200)
        self.setFrameStyle(QFrame.StyledPanel)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title bar
        title_layout = QHBoxLayout()
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold; color: white;")
        
        self.collapse_btn = QPushButton("−")
        self.collapse_btn.setFixedSize(20, 20)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.collapse_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.content_widget)
        
        self.setLayout(main_layout)
        
        # Styling
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(50, 50, 50, 200);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
            }
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
        
    def add_widget(self, widget):
        """Add a widget to the panel content"""
        self.content_layout.addWidget(widget)
        
    def toggle_collapse(self):
        """Toggle panel collapse state"""
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.content_widget.hide()
            self.collapse_btn.setText("+")
            self.setFixedHeight(40)
        else:
            self.content_widget.show()
            self.collapse_btn.setText("−")
            self.setFixedHeight(200)
            
    def position_panel(self, position="center"):
        """Position the panel relative to parent"""
        if not self.parent_widget:
            return
            
        parent_rect = self.parent_widget.rect()
        
        if position == "center":
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
        elif position == "top-left":
            x = 20
            y = 60
        # Add more positions as needed
        
        self.move(x, y)

