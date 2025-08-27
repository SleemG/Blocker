import sqlite3
from typing import List, Optional, Tuple

class KeywordManager:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def add_keyword(self, user_email: str, keyword: str) -> Tuple[bool, Optional[str]]:
        """Add a blocked keyword for a user"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO blocked_keywords (user_email, keyword) VALUES (?, ?)',
                    (user_email, keyword.lower().strip())
                )
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def remove_keyword(self, user_email: str, keyword: str) -> Tuple[bool, Optional[str]]:
        """Remove a blocked keyword for a user"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM blocked_keywords WHERE user_email = ? AND keyword = ?',
                    (user_email, keyword.lower().strip())
                )
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def get_keywords(self, user_email: str) -> List[str]:
        """Get all blocked keywords for a user"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT keyword FROM blocked_keywords WHERE user_email = ? ORDER BY keyword',
                    (user_email,)
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting keywords: {e}")
            return []

    def clear_keywords(self, user_email: str) -> Tuple[bool, Optional[str]]:
        """Remove all blocked keywords for a user"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM blocked_keywords WHERE user_email = ?',
                    (user_email,)
                )
                conn.commit()
                return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def import_keywords(self, user_email: str, keywords: List[str]) -> Tuple[int, int]:
        """Import a list of keywords. Returns (success_count, fail_count)"""
        success = 0
        failed = 0
        for keyword in keywords:
            result, _ = self.add_keyword(user_email, keyword)
            if result:
                success += 1
            else:
                failed += 1
        return success, failed
