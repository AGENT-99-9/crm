"""
Authentication routes.
Handles login, logout, and session status checks.
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import check_password_hash
from database.db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    from werkzeug.security import generate_password_hash
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters', 'field': 'username'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters', 'field': 'password'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        return jsonify({'error': 'Username already exists', 'field': 'username'}), 400

    password_hash = generate_password_hash(password)
    cur = db.execute(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        (username, password_hash, 'user')
    )
    user_id = cur.lastrowid
    
    # Initialize settings for new user
    db.execute('INSERT INTO settings (user_id, reminder_before_minutes, dark_mode) VALUES (?, ?, ?)', (user_id, 15, 1))
    db.commit()
    
    # Log user in
    session.clear()
    session['user_id'] = user_id
    session['username'] = username
    session['role'] = 'user'
    current_app.logger.info(f"New user registered: {username}")
    
    return jsonify({
        'message': 'Registered successfully',
        'user': {'id': user_id, 'username': username, 'role': 'user'}
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ? AND is_active = 1', (username,)
    ).fetchone()

    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        current_app.logger.info(f"User '{username}' logged in successfully")

        # Audit
        db.execute(
            'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
            (user['id'], 'LOGIN', 'user', user['id'], f"User logged in")
        )
        db.commit()

        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'display_name': user['display_name'] or user['username'],
                'role': user['role']
            }
        }), 200

    current_app.logger.warning(f"Failed login attempt for username: '{username}'")
    return jsonify({'error': 'Invalid username or password'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    username = session.get('username', 'unknown')
    session.clear()
    current_app.logger.info(f"User '{username}' logged out")
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_me():
    if 'user_id' in session:
        return jsonify({
            'id': session['user_id'],
            'username': session['username'],
            'role': session.get('role', 'user')
        }), 200
    return jsonify({'error': 'Not authenticated'}), 401
