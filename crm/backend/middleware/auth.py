"""
Authentication middleware.
Provides a reusable decorator for route-level authentication enforcement.
Eliminates the duplicated is_authenticated() pattern across all route files.
"""
from functools import wraps
from flask import session, jsonify, current_app


def login_required(f):
    """Decorator that enforces session-based authentication on a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            current_app.logger.warning(
                f"Unauthorized access attempt to {f.__name__}"
            )
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator that enforces admin role access on a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Return the currently authenticated user's ID from the session."""
    return session.get('user_id')


def get_current_username():
    """Return the currently authenticated user's username from the session."""
    return session.get('username')
