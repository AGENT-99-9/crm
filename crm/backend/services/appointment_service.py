"""
Appointment service — business logic for appointment operations.
"""
from database.db import get_db
from utils.validators import (
    require_fields, validate_string, validate_datetime,
    validate_status, validate_positive_int, sanitize_text
)

APPOINTMENT_STATUSES = ['Pending', 'Completed', 'Cancelled']


def validate_appointment_data(data):
    """Validate and sanitize appointment input data."""
    require_fields(data, ['title', 'appointment_datetime'])
    return {
        'client_id': validate_positive_int(data['client_id'], 'client_id') if data.get('client_id') else None,
        'title': validate_string(data.get('title'), 'title', max_len=300),
        'appointment_datetime': validate_datetime(data.get('appointment_datetime'), 'appointment_datetime'),
        'location': sanitize_text(validate_string(data.get('location'), 'location', min_len=0, max_len=300)),
        'description': sanitize_text(data.get('description')),
        'status': validate_status(data.get('status'), APPOINTMENT_STATUSES),
    }


def get_all_appointments(user_id):
    """Fetch all non-deleted appointments for a user with client names."""
    db = get_db()
    appointments = db.execute('''
        SELECT a.*, c.name as client_name 
        FROM appointments a 
        LEFT JOIN clients c ON a.client_id = c.id
        WHERE a.user_id = ? AND a.is_deleted = 0
        ORDER BY a.appointment_datetime ASC
    ''', (user_id,)).fetchall()
    return [dict(a) for a in appointments]


def get_appointment_by_id(user_id, appt_id):
    """Fetch a single appointment."""
    db = get_db()
    appt = db.execute('''
        SELECT a.*, c.name as client_name 
        FROM appointments a 
        LEFT JOIN clients c ON a.client_id = c.id
        WHERE a.id = ? AND a.user_id = ? AND a.is_deleted = 0
    ''', (appt_id, user_id)).fetchone()
    return dict(appt) if appt else None


def create_appointment(user_id, data):
    """Create a new appointment."""
    validated = validate_appointment_data(data)
    db = get_db()
    cur = db.execute('''
        INSERT INTO appointments (user_id, client_id, title, appointment_datetime, location, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, validated['client_id'], validated['title'],
        validated['appointment_datetime'], validated['location'],
        validated['description'], validated['status']
    ))
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'CREATE', 'appointment', cur.lastrowid, f"Created appointment: {validated['title']}")
    )
    db.commit()

    return cur.lastrowid


def update_appointment(user_id, appt_id, data):
    """Update an existing appointment."""
    validated = validate_appointment_data(data)
    db = get_db()

    existing = db.execute(
        'SELECT id FROM appointments WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (appt_id, user_id)
    ).fetchone()
    if not existing:
        return False

    db.execute('''
        UPDATE appointments 
        SET client_id = ?, title = ?, appointment_datetime = ?, location = ?, 
            description = ?, status = ?, updated_at = datetime('now')
        WHERE id = ? AND user_id = ?
    ''', (
        validated['client_id'], validated['title'],
        validated['appointment_datetime'], validated['location'],
        validated['description'], validated['status'],
        appt_id, user_id
    ))
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'UPDATE', 'appointment', appt_id, f"Updated appointment: {validated['title']}")
    )
    db.commit()

    return True


def delete_appointment(user_id, appt_id):
    """Soft-delete an appointment."""
    db = get_db()

    existing = db.execute(
        'SELECT id, title FROM appointments WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (appt_id, user_id)
    ).fetchone()
    if not existing:
        return False

    db.execute(
        "UPDATE appointments SET is_deleted = 1, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (appt_id, user_id)
    )
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'DELETE', 'appointment', appt_id, f"Soft-deleted appointment: {existing['title']}")
    )
    db.commit()

    return True
