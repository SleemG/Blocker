import sqlite3
from src.utils.database import Database

def set_default_settings(db, user_email):
    """Set default settings for a user"""
    default_settings = {
        # Block screen settings
        'countdown_duration': ('60', 'number'),
        'block_message': '(اتقي الله في نفسك)',
        'redirect_url': ('https://www.google.com', 'text'),
        
        # Protection settings
        'checkBox_6': ('true', 'boolean'),  # Uninstall protection
        'adult_content_blocking': ('true', 'boolean'),
        'auto_block_adult': ('true', 'boolean')
    }
    
    for setting_name, (value, setting_type) in default_settings.items():
        db.update_setting(user_email, setting_name, value, setting_type)
    print(f"Default settings set for user: {user_email}")

def migrate_database():
    """
    Migrate the database to the new schema that includes setting_type column
    """
    print("Starting database migration...")
    db = Database()
    
    # Backup existing settings if needed
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_email FROM user_settings")
            users = [row[0] for row in cursor.fetchall()]
    except:
        users = []
    
    # Drop all existing tables
    print("Dropping existing tables...")
    db.drop_tables()
    
    # Create tables with new schema
    print("Creating tables with new schema...")
    db.create_tables()
    
    # Restore settings with proper types for each user
    for user_email in users:
        print(f"Restoring settings for user: {user_email}")
        set_default_settings(db, user_email)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
