"""
Reminders routes — fetches upcoming events within the user's reminder window.
"""
from flask import Blueprint, jsonify
from middleware.auth import login_required, get_current_user_id
from database.db import get_db
from datetime import datetime, timedelta

reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('/', methods=['GET'])
@login_required
def get_reminders():
    user_id = get_current_user_id()
    db = get_db()

    # Get user-specific settings
    settings = db.execute(
        'SELECT * FROM settings WHERE user_id = ?', (user_id,)
    ).fetchone()
    reminder_mins = settings['reminder_before_minutes'] if settings else 15

    now = datetime.now()
    window_start = now.strftime('%Y-%m-%dT%H:%M')
    window_end = (now + timedelta(minutes=reminder_mins)).strftime('%Y-%m-%dT%H:%M')

    # Appointments in window
    appointments = db.execute('''
        SELECT a.*, c.name as client_name 
        FROM appointments a 
        LEFT JOIN clients c ON a.client_id = c.id
        WHERE a.user_id = ? AND a.is_deleted = 0
          AND a.appointment_datetime >= ? AND a.appointment_datetime <= ? 
          AND a.status != 'Completed'
    ''', (user_id, window_start, window_end)).fetchall()

    # Follow-ups in window
    followups = db.execute('''
        SELECT f.*, c.name as client_name 
        FROM followups f
        LEFT JOIN clients c ON f.client_id = c.id
        WHERE f.user_id = ? AND f.is_deleted = 0
          AND f.followup_date >= ? AND f.followup_date <= ? 
          AND f.status != 'Completed'
    ''', (user_id, window_start, window_end)).fetchall()

    return jsonify({
        'appointments': [dict(a) for a in appointments],
        'followups': [dict(f) for f in followups]
    }), 200
