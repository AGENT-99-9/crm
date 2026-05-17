"""
Dashboard service — aggregates data for the dashboard view.
Replaces the old pattern of fetching all clients and filtering on the frontend.
"""
from database.db import get_db
from datetime import datetime


def get_dashboard_data(user_id):
    """Fetch all dashboard summary data in optimized queries."""
    db = get_db()
    today_str = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().isoformat()

    # Stats
    total_clients = db.execute(
        'SELECT COUNT(*) as count FROM clients WHERE user_id = ? AND is_deleted = 0',
        (user_id,)
    ).fetchone()['count']

    active_appointments = db.execute(
        "SELECT COUNT(*) as count FROM appointments WHERE user_id = ? AND is_deleted = 0 AND status = 'Pending'",
        (user_id,)
    ).fetchone()['count']

    pending_followups = db.execute(
        "SELECT COUNT(*) as count FROM followups WHERE user_id = ? AND is_deleted = 0 AND status = 'Pending'",
        (user_id,)
    ).fetchone()['count']

    total_appts = db.execute(
        'SELECT COUNT(*) as count FROM appointments WHERE user_id = ? AND is_deleted = 0',
        (user_id,)
    ).fetchone()['count']

    completed_appts = db.execute(
        "SELECT COUNT(*) as count FROM appointments WHERE user_id = ? AND is_deleted = 0 AND status = 'Completed'",
        (user_id,)
    ).fetchone()['count']

    completion_rate = round((completed_appts / max(total_appts, 1)) * 100)

    # Today's meetings
    today_meetings = db.execute('''
        SELECT a.*, c.name as client_name 
        FROM appointments a
        LEFT JOIN clients c ON a.client_id = c.id
        WHERE a.user_id = ? AND a.is_deleted = 0 
          AND a.appointment_datetime LIKE ?
        ORDER BY a.appointment_datetime ASC
    ''', (user_id, f'{today_str}%')).fetchall()

    # Today's follow-ups
    today_followups = db.execute('''
        SELECT f.*, c.name as client_name 
        FROM followups f
        LEFT JOIN clients c ON f.client_id = c.id
        WHERE f.user_id = ? AND f.is_deleted = 0 
          AND f.followup_date LIKE ? AND f.status != 'Completed'
        ORDER BY f.followup_date ASC
    ''', (user_id, f'{today_str}%')).fetchall()

    # Overdue follow-ups
    overdue_followups = db.execute('''
        SELECT f.*, c.name as client_name 
        FROM followups f
        LEFT JOIN clients c ON f.client_id = c.id
        WHERE f.user_id = ? AND f.is_deleted = 0 
          AND f.followup_date < ? AND f.status NOT IN ('Completed', 'Cancelled')
        ORDER BY f.followup_date ASC
    ''', (user_id, today_str)).fetchall()

    # Recent clients (last 5)
    recent_clients = db.execute('''
        SELECT c.*, 
            (SELECT MIN(f.followup_date) FROM followups f 
             WHERE f.client_id = c.id AND f.user_id = ? AND f.is_deleted = 0 AND f.status = 'Pending'
            ) as next_followup
        FROM clients c
        WHERE c.user_id = ? AND c.is_deleted = 0
        ORDER BY c.created_at DESC LIMIT 5
    ''', (user_id, user_id)).fetchall()

    return {
        'stats': {
            'total_clients': total_clients,
            'active_appointments': active_appointments,
            'pending_followups': pending_followups,
            'completion_rate': completion_rate,
        },
        'today_meetings': [dict(m) for m in today_meetings],
        'today_followups': [dict(f) for f in today_followups],
        'overdue_followups': [dict(f) for f in overdue_followups],
        'recent_clients': [dict(c) for c in recent_clients],
    }
