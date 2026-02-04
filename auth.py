"""
CAFÉCRAFT AUTH MODULE

TASK FOR COPILOT:
Implement secure user authentication and role-based access control.

REQUIREMENTS:
- Hash passwords using SHA-256
- Roles: admin, manager, cashier, inventory_staff
- Session-based authentication
- Admin-only user management

FUNCTIONS TO GENERATE:
- create_user(username, password, role, full_name)
- update_user(user_id, data)
- delete_user(user_id)
- authenticate_user(username, password)
- role_required(allowed_roles)
"""
import sqlite3
from functools import wraps
from database import get_connection, hash_password, verify_user

# Simple in-memory session store for the running application
_SESSION = {"user": None}


def _validate_password_rules(password):
	"""Validate password rules:
	- Minimum 12 characters
	- At least 1 lowercase letter
	- At least 1 uppercase letter
	- At least 1 number
	- At least 1 special character
	"""
	if not isinstance(password, str):
		return False, 'Password must be a string'
	if len(password) < 12:
		return False, 'Password must be at least 12 characters long'
	if not any(c.islower() for c in password):
		return False, 'Password must contain at least one lowercase letter'
	if not any(c.isupper() for c in password):
		return False, 'Password must contain at least one uppercase letter'
	if not any(c.isdigit() for c in password):
		return False, 'Password must contain at least one number'
	special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
	if not any(c in special_chars for c in password):
		return False, 'Password must contain at least one special character'
	return True, ''


def create_user(username, password, role, full_name, permissions=None):
	"""Create a new user. Returns the inserted user id."""
	# Expanded roles to include owner and employee
	allowed_roles = ('owner', 'admin', 'manager', 'cashier', 'inventory_staff', 'employee')
	if role not in allowed_roles:
		raise ValueError("Invalid role")
	ok, msg = _validate_password_rules(password)
	if not ok:
		raise ValueError(msg)

	# Set default permissions based on role
	if permissions is None:
		permissions = {
			'can_pos': 1 if role in ('owner', 'admin', 'cashier', 'employee') else 0,
			'can_inventory': 1 if role in ('owner', 'admin', 'cashier', 'inventory_staff') else 0,
			'can_reports': 1 if role in ('owner', 'admin', 'manager') else 0,
			'can_user_management': 1 if role in ('owner', 'admin') else 0
		}

	conn = get_connection()
	cursor = conn.cursor()
	pwd_hash = hash_password(password)
	try:
		cursor.execute(
			"INSERT INTO users (username, password_hash, full_name, role, can_pos, can_inventory, can_reports, can_user_management) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
			(username, pwd_hash, full_name, role, permissions['can_pos'], permissions['can_inventory'], permissions['can_reports'], permissions['can_user_management'])
		)
		conn.commit()
		return cursor.lastrowid
	finally:
		conn.close()


def update_user(user_id, data):
	"""Update user fields. `data` is a dict that may contain username, password, full_name, role."""
	allowed_roles = ('owner', 'admin', 'manager', 'cashier', 'inventory_staff', 'employee')
	set_clauses = []
	params = []

	if 'username' in data:
		set_clauses.append('username = ?')
		params.append(data['username'])
	if 'password' in data:
		ok, msg = _validate_password_rules(data['password'])
		if not ok:
			raise ValueError(msg)
		set_clauses.append('password_hash = ?')
		params.append(hash_password(data['password']))
	if 'full_name' in data:
		set_clauses.append('full_name = ?')
		params.append(data['full_name'])
	if 'role' in data:
		if data['role'] not in allowed_roles:
			raise ValueError('Invalid role')
		set_clauses.append('role = ?')
		params.append(data['role'])
	if 'can_pos' in data:
		set_clauses.append('can_pos = ?')
		params.append(data['can_pos'])
	if 'can_inventory' in data:
		set_clauses.append('can_inventory = ?')
		params.append(data['can_inventory'])
	if 'can_reports' in data:
		set_clauses.append('can_reports = ?')
		params.append(data['can_reports'])
	if 'can_user_management' in data:
		set_clauses.append('can_user_management = ?')
		params.append(data['can_user_management'])

	if not set_clauses:
		return False

	params.append(user_id)
	sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"

	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute(sql, tuple(params))
	conn.commit()
	conn.close()
	return True


def delete_user(user_id):
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
	conn.commit()
	conn.close()
	return True


def authenticate_user(username, password):
	"""Authenticate and set session. Returns user dict on success or None."""
	user = verify_user(username, password)
	if user:
		user_obj = {"id": user[0], "name": user[1], "role": user[2]}
		_SESSION['user'] = user_obj
		return user_obj
	return None


def logout_user():
	_SESSION['user'] = None


def get_current_user():
	return _SESSION.get('user')


def role_required(allowed_roles):
	"""Decorator to guard functions. `allowed_roles` can be a string or iterable."""
	if isinstance(allowed_roles, str):
		allowed = {allowed_roles}
	else:
		allowed = set(allowed_roles)

	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			user = get_current_user()
			if not user or user.get('role') not in allowed:
				raise PermissionError('User does not have required role')
			return func(*args, **kwargs)
		return wrapper
	return decorator
