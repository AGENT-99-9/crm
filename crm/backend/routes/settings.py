"""
Settings routes — per-user settings management.
"""
from flask import Blueprint, request, jsonify, current_app
from middleware.auth import login_required, get_current_user_id
from database.db import get_db
from utils.validators import validate_positive_int, ValidationError

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET'])
@login_required
def get_settings():
    user_id = get_current_user_id()
    db = get_db()
    settings = db.execute(
        'SELECT * FROM settings WHERE user_id = ?', (user_id,)
    ).fetchone()

    if settings:
        return jsonify(dict(settings)), 200

    # Auto-create default settings for this user
    db.execute(
        'INSERT INTO settings (user_id, reminder_before_minutes, dark_mode) VALUES (?, ?, ?)',
        (user_id, 15, 1)
    )
    db.commit()
    settings = db.execute(
        'SELECT * FROM settings WHERE user_id = ?', (user_id,)
    ).fetchone()
    return jsonify(dict(settings)), 200


@settings_bp.route('/', methods=['PUT'])
@login_required
def update_settings():
    user_id = get_current_user_id()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        reminder_mins = validate_positive_int(
            data.get('reminder_before_minutes', 15), 'reminder_before_minutes'
        )
        dark_mode = 1 if data.get('dark_mode') else 0
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400

    db = get_db()
    db.execute('''
        UPDATE settings 
        SET reminder_before_minutes = ?, dark_mode = ?, updated_at = datetime('now')
        WHERE user_id = ?
    ''', (reminder_mins, dark_mode, user_id))
    db.commit()

    current_app.logger.info(f"Settings updated by user {user_id}")
    return jsonify({'message': 'Settings updated successfully'}), 200
