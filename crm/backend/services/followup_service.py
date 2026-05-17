"""
Follow-up service — business logic for follow-up operations.
"""
from database.db import get_db
from utils.validators import (
    require_fields, validate_datetime, validate_status,
    validate_positive_int, sanitize_text
)

FOLLOWUP_STATUSES = ['Pending', 'Completed', 'Delayed', 'Cancelled']
FOLLOWUP_TYPES = ['Call', 'WhatsApp', 'Email', 'Meeting', 'Demo']


def validate_followup_data(data):
    """Validate and sanitize follow-up input data."""
    require_fields(data, ['client_id', 'followup_date'])
    fu_type = data.get('followup_type', 'Call')
    if fu_type not in FOLLOWUP_TYPES:
        fu_type = 'Call'
    return {
        'client_id': validate_positive_int(data.get('client_id'), 'client_id'),
        'followup_date': validate_datetime(data.get('followup_date'), 'followup_date'),
        'followup_type': fu_type,
        'notes': sanitize_text(data.get('notes')),
        'status': validate_status(data.get('status'), FOLLOWUP_STATUSES),
    }


def get_all_followups(user_id):
    """Fetch all non-deleted follow-ups for a user with client names."""
    db = get_db()
    followups = db.execute('''
        SELECT f.*, c.name as client_name 
        FROM followups f
        LEFT JOIN clients c ON f.client_id = c.id
        WHERE f.user_id = ? AND f.is_deleted = 0
        ORDER BY f.followup_date ASC
    ''', (user_id,)).fetchall()
    return [dict(f) for f in followups]


def get_followup_by_id(user_id, fu_id):
    """Fetch a single follow-up."""
    db = get_db()
    fu = db.execute('''
        SELECT f.*, c.name as client_name 
        FROM followups f
        LEFT JOIN clients c ON f.client_id = c.id
        WHERE f.id = ? AND f.user_id = ? AND f.is_deleted = 0
    ''', (fu_id, user_id)).fetchone()
    return dict(fu) if fu else None


def create_followup(user_id, data):
    """Create a new follow-up."""
    validated = validate_followup_data(data)
    db = get_db()
    cur = db.execute('''
        INSERT INTO followups (user_id, client_id, followup_date, followup_type, notes, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id, validated['client_id'], validated['followup_date'],
        validated['followup_type'], validated['notes'], validated['status']
    ))
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'CREATE', 'followup', cur.lastrowid,
         f"Created {validated['followup_type']} follow-up for client {validated['client_id']}")
    )
    db.commit()

    return cur.lastrowid


def update_followup(user_id, fu_id, data):
    """Update an existing follow-up."""
    validated = validate_followup_data(data)
    db = get_db()

    existing = db.execute(
        'SELECT id FROM followups WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (fu_id, user_id)
    ).fetchone()
    if not existing:
        return False

    db.execute('''
        UPDATE followups 
        SET followup_date = ?, followup_type = ?, notes = ?, status = ?, updated_at = datetime('now')
        WHERE id = ? AND user_id = ?
    ''', (
        validated['followup_date'], validated['followup_type'],
        validated['notes'], validated['status'],
        fu_id, user_id
    ))
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'UPDATE', 'followup', fu_id, f"Updated follow-up")
    )
    db.commit()

    return True


def delete_followup(user_id, fu_id):
    """Soft-delete a follow-up."""
    db = get_db()

    existing = db.execute(
        'SELECT id FROM followups WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (fu_id, user_id)
    ).fetchone()
    if not existing:
        return False

    db.execute(
        "UPDATE followups SET is_deleted = 1, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (fu_id, user_id)
    )
    db.commit()

    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'DELETE', 'followup', fu_id, f"Soft-deleted follow-up")
    )
    db.commit()

    return True
