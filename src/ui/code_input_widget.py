from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent

class CodeInputWidget(QWidget):
    code_complete = pyqtSignal(str)  # Emitted when all digits are entered
    
    def __init__(self, parent=None, cell_names=None):
        """Initialize the code input widget
        Args:
            parent: Parent widget
            cell_names: List of 6 QLineEdit names from the UI file
        """
        super().__init__(parent)
        self.cell_names = cell_names or [f"digit_{i+1}" for i in range(6)]
        self.cells = []
        
    def setup_cells(self, dialog):
        """Setup the verification code cells
        Args:
            dialog: The dialog containing the cells (usually self from SignUpDialog)
        """
        # Get references to the line edits
        self.cells = [getattr(dialog, name) for name in self.cell_names]
        
        # Configure each cell
        for i, cell in enumerate(self.cells):
            cell.setMaxLength(1)
            cell.setAlignment(Qt.AlignCenter)
            cell.setStyleSheet("""
                QLineEdit {
                    font-size: 20px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background: white;
                    padding: 5px;
                    min-width: 40px;
                    min-height: 40px;
                }
                QLineEdit:focus {
                    border-color: #2196F3;
                }
            """)
            # Connect signals
            cell.textChanged.connect(lambda text, idx=i: self.on_text_changed(text, idx))
            # Store the original keyPressEvent
            cell.originalKeyPressEvent = cell.keyPressEvent
            # Set new keyPressEvent
            def new_keypress(event, index=i):
                self.handle_key_press(event, index)
            cell.keyPressEvent = new_keypress
            
    def on_text_changed(self, text, cell_index):
        """Handle text changes in cells"""
        if text and cell_index < 5:
            # Move to next cell when a digit is entered
            self.cells[cell_index + 1].setFocus()
        
        # Check if code is complete
        code = self.get_code()
        if len(code) == 6:
            self.code_complete.emit(code)
            
    def handle_key_press(self, event: QKeyEvent, cell_index):
        """Handle key press events in cells"""
        if event.key() == Qt.Key_Backspace:
            # If current cell is empty and not the first cell, move to previous
            if not self.cells[cell_index].text() and cell_index > 0:
                self.cells[cell_index - 1].setFocus()
                self.cells[cell_index - 1].setText("")
            # If current cell has text, just clear it
            else:
                self.cells[cell_index].setText("")
            event.accept()
            return
            
        # For regular key presses, let the QLineEdit handle it normally
        self.cells[cell_index].originalKeyPressEvent(event)
            
    def get_code(self):
        """Get the complete verification code"""
        code = "".join(cell.text() for cell in self.cells)
        # Ensure we have exactly 6 digits
        return code if len(code) == 6 else ""
        
    def clear(self):
        """Clear all cells"""
        for cell in self.cells:
            cell.clear()
        self.cells[0].setFocus()
