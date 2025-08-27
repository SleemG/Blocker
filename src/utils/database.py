import sqlite3
from typing import Optional, Tuple

class Database:
    def __init__(self, db_path: str = 'app_blocker.db'):
        self.db_path = db_path

    def drop_tables(self):
        """Drop all tables to reset the database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                # Drop each table
                for table in tables:
                    if table[0] not in ['sqlite_sequence']:  # Skip SQLite internal tables
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                conn.commit()
                print("Successfully dropped all tables")
        except sqlite3.Error as e:
            print(f"Error dropping tables: {e}")

    def create_tables(self):
        """Create all necessary database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create settings table with support for all value types
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_email TEXT NOT NULL,
                        setting_name TEXT NOT NULL,
                        setting_value TEXT NOT NULL,
                        setting_type TEXT CHECK(setting_type IN ('boolean', 'text', 'number')),
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_email) REFERENCES users (email),
                        PRIMARY KEY (user_email, setting_name)
                    )
                ''')
                
                # Create blocked keywords table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blocked_keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_email) REFERENCES users (email),
                        UNIQUE(user_email, keyword)
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

    def get_verified_user(self) -> Optional[str]:
        """Get the most recently logged in verified user's email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT email 
                    FROM users 
                    ORDER BY created_at DESC
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting verified user: {e}")
            return None

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
                    # Add default keywords
                    default_keywords = [
                        'porn', 'xxx', 'adult content', 'nsfw',
                        'nude', 'naked', 'sex', 'explicit',
                        'adult', 'mature', '18+'
                    ]
                    for keyword in default_keywords:
                        cursor.execute(
                            'INSERT OR IGNORE INTO blocked_keywords (user_email, keyword) VALUES (?, ?)',
                            (email, keyword)
                        )
                    # Add default settings
                    cursor.execute('''
                        INSERT OR REPLACE INTO user_settings 
                        (user_email, setting_name, setting_value, setting_type)
                        VALUES (?, 'strict_keyword_matching', 'true', 'boolean')
                    ''', (email,))
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
                result = cursor.fetchone()
                return result if result else None
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

    def update_setting(self, user_email: str, setting_name: str, value: str, value_type: str = 'text') -> bool:
        """Update a user setting in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_settings 
                    (user_email, setting_name, setting_value, setting_type)
                    VALUES (?, ?, ?, ?)
                ''', (user_email, setting_name, str(value), value_type))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def add_blocked_website(self, user_email: str, website: str) -> bool:
        """Add a website to the blocked list"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_items 
                    (email, item, type, item_type)
                    VALUES (?, ?, 'block', 'website')
                ''', (user_email, website.lower().strip()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_blocked_websites(self, user_email: str) -> list:
        """Get list of blocked websites for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT item FROM blocked_items 
                    WHERE email = ? AND type = 'block' AND item_type = 'website'
                ''', (user_email,))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def get_setting(self, user_email: str, setting_name: str) -> Optional[str]:
        """Get a user setting from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT setting_value, setting_type FROM user_settings
                    WHERE user_email = ? AND setting_name = ?
                ''', (user_email, setting_name))
                result = cursor.fetchone()
                if not result:
                    return None
                value, value_type = result
                if value_type == 'boolean':
                    return value.lower() == 'true'
                elif value_type == 'number':
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        print(f"Error converting setting value to number: {value}")
                        return None
                return value
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_all_settings(self, user_email: str) -> dict:
        """Get all settings for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT setting_name, setting_value, setting_type FROM user_settings
                    WHERE user_email = ?
                ''', (user_email,))
                settings = {}
                for name, value, value_type in cursor.fetchall():
                    if value_type == 'boolean':
                        settings[name] = value.lower() == 'true'
                    elif value_type == 'number':
                        try:
                            settings[name] = float(value)
                        except ValueError:
                            settings[name] = value
                    else:
                        settings[name] = value
                return settings
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
