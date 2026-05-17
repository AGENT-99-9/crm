"""
Client service — business logic for client operations.
All database queries are isolated here, keeping routes thin.
"""
from database.db import get_db
from utils.validators import (
    require_fields, validate_string, validate_phone,
    validate_datetime, validate_status, sanitize_text
)
from datetime import datetime

CLIENT_STATUSES = ['Active', 'Inactive', 'Completed', 'Lost']


def validate_client_data(data):
    """Validate and sanitize client input data."""
    require_fields(data, ['name'])
    return {
        'name': validate_string(data.get('name'), 'name', max_len=200),
        'phone': validate_phone(data.get('phone')),
        'company': sanitize_text(validate_string(data.get('company'), 'company', min_len=0, max_len=200)),
        'work_type': sanitize_text(validate_string(data.get('work_type'), 'work_type', min_len=0, max_len=100)),
        'interested_product': sanitize_text(validate_string(data.get('interested_product'), 'interested_product', min_len=0, max_len=200)),
        'custom_requirements': sanitize_text(data.get('custom_requirements')),
        'notes': sanitize_text(data.get('notes')),
        'status': validate_status(data.get('status'), CLIENT_STATUSES),
    }


def get_all_clients(user_id):
    """Fetch all non-deleted clients for a user."""
    db = get_db()
    clients = db.execute(
        'SELECT * FROM clients WHERE user_id = ? AND is_deleted = 0 ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    return [dict(c) for c in clients]

import csv
import io
def export_clients_csv(user_id):
    """Generate a CSV string of all clients for the user."""
    clients = get_all_clients(user_id)
    output = io.StringIO()
    if not clients:
        return output.getvalue()
        
    writer = csv.DictWriter(output, fieldnames=['id', 'name', 'phone', 'company', 'work_type', 'interested_product', 'status', 'created_at'])
    writer.writeheader()
    for c in clients:
        writer.writerow({
            'id': c['id'],
            'name': c['name'],
            'phone': c['phone'] or '',
            'company': c['company'] or '',
            'work_type': c['work_type'] or '',
            'interested_product': c['interested_product'] or '',
            'status': c['status'],
            'created_at': c['created_at']
        })
    return output.getvalue()


def get_client_by_id(user_id, client_id):
    """Fetch a single client with its followups and appointments."""
    db = get_db()
    client = db.execute(
        'SELECT * FROM clients WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (client_id, user_id)
    ).fetchone()

    if not client:
        return None

    client_data = dict(client)

    # Fetch related followups
    followups = db.execute(
        'SELECT * FROM followups WHERE client_id = ? AND user_id = ? AND is_deleted = 0 ORDER BY followup_date DESC',
        (client_id, user_id)
    ).fetchall()
    client_data['followups'] = [dict(f) for f in followups]

    # Fetch related appointments
    appointments = db.execute(
        'SELECT * FROM appointments WHERE client_id = ? AND user_id = ? AND is_deleted = 0 ORDER BY appointment_datetime DESC',
        (client_id, user_id)
    ).fetchall()
    client_data['appointments'] = [dict(a) for a in appointments]

    # Derive next_followup from actual followup records
    next_fu = db.execute(
        '''SELECT followup_date FROM followups 
           WHERE client_id = ? AND user_id = ? AND is_deleted = 0 AND status = 'Pending'
           ORDER BY followup_date ASC LIMIT 1''',
        (client_id, user_id)
    ).fetchone()
    client_data['next_followup'] = next_fu['followup_date'] if next_fu else None

    return client_data


def create_client(user_id, data):
    """Create a new client."""
    validated = validate_client_data(data)
    db = get_db()
    cur = db.execute('''
        INSERT INTO clients (user_id, name, phone, company, work_type, interested_product, custom_requirements, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, validated['name'], validated['phone'], validated['company'],
        validated['work_type'], validated['interested_product'],
        validated['custom_requirements'], validated['notes'], validated['status']
    ))
    db.commit()

    # Audit
    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'CREATE', 'client', cur.lastrowid, f"Created client: {validated['name']}")
    )
    db.commit()

    return cur.lastrowid


def update_client(user_id, client_id, data):
    """Update an existing client."""
    validated = validate_client_data(data)
    db = get_db()

    # Verify ownership
    existing = db.execute(
        'SELECT id FROM clients WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (client_id, user_id)
    ).fetchone()
    if not existing:
        return False

    db.execute('''
        UPDATE clients 
        SET name = ?, phone = ?, company = ?, work_type = ?, interested_product = ?, 
            custom_requirements = ?, notes = ?, status = ?, updated_at = datetime('now')
        WHERE id = ? AND user_id = ?
    ''', (
        validated['name'], validated['phone'], validated['company'],
        validated['work_type'], validated['interested_product'],
        validated['custom_requirements'], validated['notes'], validated['status'],
        client_id, user_id
    ))
    db.commit()

    # Audit
    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'UPDATE', 'client', client_id, f"Updated client: {validated['name']}")
    )
    db.commit()

    return True


def delete_client(user_id, client_id):
    """Soft-delete a client and cascade to related records."""
    db = get_db()

    existing = db.execute(
        'SELECT id, name FROM clients WHERE id = ? AND user_id = ? AND is_deleted = 0',
        (client_id, user_id)
    ).fetchone()
    if not existing:
        return False

    now = datetime.now().isoformat()
    db.execute('UPDATE clients SET is_deleted = 1, updated_at = ? WHERE id = ? AND user_id = ?',
               (now, client_id, user_id))
    db.execute('UPDATE followups SET is_deleted = 1, updated_at = ? WHERE client_id = ? AND user_id = ?',
               (now, client_id, user_id))
    db.execute('UPDATE appointments SET is_deleted = 1, updated_at = ? WHERE client_id = ? AND user_id = ?',
               (now, client_id, user_id))
    db.commit()

    # Audit
    db.execute(
        'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)',
        (user_id, 'DELETE', 'client', client_id, f"Soft-deleted client: {existing['name']}")
    )
    db.commit()

    return True


def search_clients(user_id, query):
    """Search clients by name, phone, company, or product."""
    db = get_db()
    if not query or len(query.strip()) < 2:
        return []
    term = f'%{query.strip()}%'
    results = db.execute('''
        SELECT * FROM clients 
        WHERE user_id = ? AND is_deleted = 0
          AND (name LIKE ? OR phone LIKE ? OR company LIKE ? OR interested_product LIKE ?)
        ORDER BY name ASC LIMIT 20
    ''', (user_id, term, term, term, term)).fetchall()
    return [dict(r) for r in results]
