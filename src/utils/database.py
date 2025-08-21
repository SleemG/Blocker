import sqlite3
from typing import Optional, Tuple

class Database:
    def __init__(self, db_path: str = 'app_blocker.db'):
        self.db_path = db_path

    def create_tables(self):
        """Create all necessary database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create settings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_email TEXT NOT NULL,
                        setting_name TEXT NOT NULL,
                        setting_value BOOLEAN NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_email) REFERENCES users (email),
                        PRIMARY KEY (user_email, setting_name)
                    )
                ''')
                
                # Create verification codes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_codes (
                        email TEXT PRIMARY KEY,
                        code TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        username TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create partners table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS partners (
                        user_email TEXT PRIMARY KEY,
                        partner_name TEXT NOT NULL,
                        partner_email TEXT NOT NULL,
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_email) REFERENCES users (email)
                    )
                ''')
                
                # Create blocked items table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blocked_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT,
                        item TEXT,
                        type TEXT CHECK(type IN ('block', 'white')),
                        item_type TEXT CHECK(item_type IN ('website', 'app')),
                        FOREIGN KEY (email) REFERENCES users (email),
                        UNIQUE(email, item)
                    )
                ''')

                # Add focus mode table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS focus_modes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        start_time DATETIME,
                        end_time DATETIME,
                        duration INTEGER,  -- in minutes
                        is_daily BOOLEAN DEFAULT 0,
                        selected_days TEXT,
                        allowed_apps TEXT,
                        allowed_websites TEXT,
                        FOREIGN KEY (user_email) REFERENCES users (email)
                    )
                ''')
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def add_verification_code(self, email: str, code: str) -> Tuple[bool, Optional[str]]:
        """Add a verification code to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO verification_codes (email, code) VALUES (?, ?)',
                             (email, code))
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def verify_code(self, email: str, code: str) -> Tuple[bool, Optional[str]]:
        """Verify a code from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT code, timestamp,
                    (strftime('%s', 'now') - strftime('%s', timestamp)) / 60.0 as minutes_diff
                    FROM verification_codes
                    WHERE email = ?
                ''', (email,))
                
                result = cursor.fetchone()
                
                if not result:
                    return False, "No verification code found"
                    
                stored_code, timestamp, minutes_diff = result
                
                # Check if code is expired (older than 5 minutes)
                if minutes_diff > 5:
                    cursor.execute('DELETE FROM verification_codes WHERE email = ?', (email,))
                    conn.commit()
                    return False, "Verification code has expired"
                    
                # Verify the code
                if code == stored_code:
                    cursor.execute('DELETE FROM verification_codes WHERE email = ?', (email,))
                    conn.commit()
                    return True, None
                else:
                    return False, "Incorrect verification code"
                    
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def add_user(self, email: str, username: str) -> Tuple[bool, Optional[str]]:
        """Add a verified user to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Check if user already exists
                cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    # Update username if user exists
                    cursor.execute('UPDATE users SET username = ? WHERE email = ?', (username, email))
                else:
                    # Add new user
                    cursor.execute('INSERT INTO users (email, username) VALUES (?, ?)', (email, username))
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def get_user_info(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Get user info (email, username) from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT email, username FROM users WHERE email = ?', (email,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None, None

    def add_partner(self, user_email: str, partner_name: str, partner_email: str) -> bool:
        """Add or update accountability partner for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Add or update partner
                cursor.execute('''
                    INSERT OR REPLACE INTO partners (user_email, partner_name, partner_email)
                    VALUES (?, ?, ?)
                ''', (user_email, partner_name, partner_email))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_partner_info(self, user_email: str) -> Optional[Tuple[str, str]]:
        """Get partner info (name, email) for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT partner_name, partner_email 
                    FROM partners 
                    WHERE user_email = ?
                ''', (user_email,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def remove_partner(self, user_email: str) -> bool:
        """Remove accountability partner for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM partners WHERE user_email = ?', (user_email,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def add_item(self, email: str, item: str, type_: str, item_type: str) -> Tuple[bool, Optional[str]]:
        """Add a blocked/whitelisted item to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO blocked_items (email, item, type, item_type) VALUES (?, ?, ?, ?)',
                             (email, item, type_, item_type))
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "Item already exists in list"
            return False, str(e)

    def remove_item(self, email: str, item: str) -> bool:
        """Remove a blocked/whitelisted item from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM blocked_items WHERE email = ? AND item = ?', (email, item))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_items(self, email: str, type_: str, item_type: str) -> list:
        """Get all blocked/whitelisted items for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT item FROM blocked_items WHERE email = ? AND type = ? AND item_type = ?',
                             (email, type_, item_type))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def update_setting(self, user_email: str, setting_name: str, value: bool) -> bool:
        """Update a user setting in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_settings (user_email, setting_name, setting_value)
                    VALUES (?, ?, ?)
                ''', (user_email, setting_name, value))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_setting(self, user_email: str, setting_name: str) -> Optional[bool]:
        """Get a user setting from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT setting_value FROM user_settings
                    WHERE user_email = ? AND setting_name = ?
                ''', (user_email, setting_name))
                result = cursor.fetchone()
                return bool(result[0]) if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_all_settings(self, user_email: str) -> dict:
        """Get all settings for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT setting_name, setting_value FROM user_settings
                    WHERE user_email = ?
                ''', (user_email,))
                return {row[0]: bool(row[1]) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}

    def is_app_in_any_list(self, email: str, app_path: str) -> bool:
        """Check if an app is in any list (blocked or whitelisted)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM blocked_items WHERE email = ? AND item = ?',
                             (email, app_path))
                return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
