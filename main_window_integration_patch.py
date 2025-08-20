"""
Integration patch for main_window.py
This file shows the changes needed to integrate the adult content blocker
with your existing MainWindow class.

INSTRUCTIONS:
1. Add the import at the top of main_window.py
2. Add the initialization in the __init__ method
3. Optionally add the methods at the end of the class
"""

# ========== STEP 1: ADD IMPORT ==========
# Add this import near the top of main_window.py with other imports:

from ..utils.content_blocker_integration import setup_content_blocker_integration

# ========== STEP 2: ADD INITIALIZATION ==========
# Add this code in the MainWindow.__init__ method, after UI is loaded:

def __init__(self, show_on_start=True):
    # ... existing initialization code ...
    
    # Initialize adult content blocker (ADD THIS)
    try:
        self.content_blocker_integration = setup_content_blocker_integration(self)
        if self.content_blocker_integration:
            print("✅ Adult content blocker initialized successfully")
        else:
            print("❌ Failed to initialize adult content blocker")
    except Exception as e:
        print(f"⚠️  Content blocker initialization error: {e}")
        self.content_blocker_integration = None

# ========== STEP 3: OPTIONAL HELPER METHODS ==========
# Add these methods to the MainWindow class for manual control:

def enable_content_blocking(self):
    """Enable adult content blocking"""
    if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
        self.content_blocker_integration.enable_blocking()
        return True
    return False

def disable_content_blocking(self):
    """Disable adult content blocking"""
    if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
        self.content_blocker_integration.disable_blocking()
        return True
    return False

def get_content_blocking_status(self):
    """Get current content blocking status"""
    if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
        return self.content_blocker_integration.get_status()
    return False

def get_content_blocking_logs(self, limit=50):
    """Get content blocking activity logs"""
    if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
        return self.content_blocker_integration.get_block_logs(limit)
    return []

# ========== STEP 4: CLEANUP (OPTIONAL) ==========
# Add this to the __del__ method or create one if it doesn't exist:

def __del__(self):
    """Clean up resources"""
    # ... existing cleanup code ...
    
    # Stop content blocker if active (ADD THIS)
    if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
        try:
            from ..utils.adult_content_blocker import stop_content_blocking
            stop_content_blocking()
        except:
            pass

# ========== COMPLETE INTEGRATION EXAMPLE ==========
"""
Here's how your MainWindow class should look after integration:

class MainWindow(QMainWindow):
    def __init__(self, show_on_start=True):
        super().__init__()
        
        # ... existing UI setup code ...
        loadUi(os.path.join(self.gui_dir, "App GUI.ui"), self)
        
        # ... other initialization ...
        
        # Initialize adult content blocker
        try:
            self.content_blocker_integration = setup_content_blocker_integration(self)
            if self.content_blocker_integration:
                print("✅ Adult content blocker initialized successfully")
        except Exception as e:
            print(f"⚠️  Content blocker initialization error: {e}")
            self.content_blocker_integration = None
    
    # ... rest of your existing methods ...
    
    def enable_content_blocking(self):
        if hasattr(self, 'content_blocker_integration') and self.content_blocker_integration:
            self.content_blocker_integration.enable_blocking()
            return True
        return False
    
    # ... other optional methods ...
"""

# ========== TESTING THE INTEGRATION ==========
"""
After applying the patch, you can test the integration by:

1. Running your main application
2. Going to the settings tab
3. Checking/unchecking the "Block Adult Content" checkbox
4. Adjusting the countdown timer, redirect URL, and block message
5. The content blocker will automatically start/stop based on checkbox state

For testing purposes, you can also run:
python test_content_blocker.py
"""