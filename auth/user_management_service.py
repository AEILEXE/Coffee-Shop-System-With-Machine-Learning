"""
CAFÉCRAFT USER MANAGEMENT SERVICE

Responsibilities:
- User CRUD operations
- Role and permission management
- Password management
- User audit logging
- Access control enforcement
"""

from database.db import get_db_connection
from utils.security import hash_password, verify_password
from typing import List, Dict, Optional
from datetime import datetime


class UserManagementService:
    """Handle user management operations."""

    def __init__(self, db_path: str = None):
        """Initialize user management service."""
        self.db_path = db_path

    def get_all_users(self) -> List[Dict]:
        """
        Get all system users.

        Returns:
            List of user dicts.
        """
        query = """
            SELECT id, username, full_name, role, is_active, can_pos, 
                   can_inventory, can_reports, can_user_management, created_at
            FROM users
            ORDER BY full_name
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query)
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query)

            return [
                {
                    "id": row[0],
                    "username": row[1],
                    "full_name": row[2],
                    "role": row[3],
                    "is_active": bool(row[4]),
                    "can_pos": bool(row[5]),
                    "can_inventory": bool(row[6]),
                    "can_reports": bool(row[7]),
                    "can_user_management": bool(row[8]),
                    "created_at": row[9],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Get a specific user.

        Args:
            user_id: User ID.

        Returns:
            User dict or None.
        """
        query = """
            SELECT id, username, full_name, role, is_active, can_pos, 
                   can_inventory, can_reports, can_user_management, created_at
            FROM users
            WHERE id = ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    row = db.execute_fetch_one(query, (user_id,))
            else:
                with get_db_connection() as db:
                    row = db.execute_fetch_one(query, (user_id,))

            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "full_name": row[2],
                    "role": row[3],
                    "is_active": bool(row[4]),
                    "can_pos": bool(row[5]),
                    "can_inventory": bool(row[6]),
                    "can_reports": bool(row[7]),
                    "can_user_management": bool(row[8]),
                    "created_at": row[9],
                }
            return None
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            return None

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        can_pos: bool = False,
        can_inventory: bool = False,
        can_reports: bool = False,
        can_user_management: bool = False,
    ) -> Optional[int]:
        """
        Create a new user.

        Args:
            username: Unique username.
            password: Plain text password (will be hashed).
            full_name: User's full name.
            role: User role.
            can_pos: Can access POS module.
            can_inventory: Can access Inventory module.
            can_reports: Can access Reports module.
            can_user_management: Can manage users.

        Returns:
            User ID if successful, None otherwise.
        """
        try:
            password_hash = hash_password(password)

            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()
                cursor.execute(
                    """INSERT INTO users 
                       (username, password_hash, full_name, role, is_active, 
                        can_pos, can_inventory, can_reports, can_user_management)
                       VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)""",
                    (
                        username,
                        password_hash,
                        full_name,
                        role,
                        int(can_pos),
                        int(can_inventory),
                        int(can_reports),
                        int(can_user_management),
                    ),
                )
                db.commit()
                return cursor.lastrowid

        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def update_user(
        self,
        user_id: int,
        full_name: str = None,
        role: str = None,
        can_pos: bool = None,
        can_inventory: bool = None,
        can_reports: bool = None,
        can_user_management: bool = None,
        is_active: bool = None,
    ) -> bool:
        """
        Update user information.

        Args:
            user_id: User ID.
            full_name: New full name.
            role: New role.
            can_pos: POS access.
            can_inventory: Inventory access.
            can_reports: Reports access.
            can_user_management: User management access.
            is_active: Active status.

        Returns:
            True if successful, False otherwise.
        """
        try:
            updates = []
            params = []

            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            if role is not None:
                updates.append("role = ?")
                params.append(role)
            if can_pos is not None:
                updates.append("can_pos = ?")
                params.append(int(can_pos))
            if can_inventory is not None:
                updates.append("can_inventory = ?")
                params.append(int(can_inventory))
            if can_reports is not None:
                updates.append("can_reports = ?")
                params.append(int(can_reports))
            if can_user_management is not None:
                updates.append("can_user_management = ?")
                params.append(int(can_user_management))
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(int(is_active))

            if not updates:
                return True  # Nothing to update

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)

            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()
                cursor.execute(query, params)
                db.commit()
                return True

        except Exception as e:
            print(f"Error updating user {user_id}: {e}")
            return False

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID.
            old_password: Current password.
            new_password: New password.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.db_path:
                db_connection = get_db_connection(self.db_path)
            else:
                db_connection = get_db_connection()

            with db_connection as db:
                cursor = db.get_cursor()

                # Get current password hash
                cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return False

                # Verify old password
                if not verify_password(old_password, result[0]):
                    return False

                # Set new password
                new_hash = hash_password(new_password)
                cursor.execute(
                    "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_hash, user_id),
                )
                db.commit()
                return True

        except Exception as e:
            print(f"Error changing password: {e}")
            return False

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user.

        Args:
            user_id: User ID.

        Returns:
            True if successful, False otherwise.
        """
        return self.update_user(user_id, is_active=False)

    def reactivate_user(self, user_id: int) -> bool:
        """
        Reactivate a user.

        Args:
            user_id: User ID.

        Returns:
            True if successful, False otherwise.
        """
        return self.update_user(user_id, is_active=True)

    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get user's transaction history.

        Args:
            user_id: User ID.
            limit: Max results.

        Returns:
            List of transaction dicts.
        """
        query = """
            SELECT type, COUNT(*), SUM(total_amount), MAX(created_at)
            FROM transactions
            WHERE user_id = ?
            GROUP BY type
            ORDER BY MAX(created_at) DESC
            LIMIT ?
        """
        try:
            if self.db_path:
                with get_db_connection(self.db_path) as db:
                    rows = db.execute_fetch_all(query, (user_id, limit))
            else:
                with get_db_connection() as db:
                    rows = db.execute_fetch_all(query, (user_id, limit))

            return [
                {
                    "type": row[0],
                    "count": row[1],
                    "total_amount": row[2],
                    "last_activity": row[3],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching user activity: {e}")
            return []
