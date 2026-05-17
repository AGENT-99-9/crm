"""
Database seed script — populates demo data for testing.
Updated for the normalized enterprise schema with user_id scoping.
"""
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'crm.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')


def seed():
    """Seed the database with demo data."""
    # Remove old database to prevent schema conflicts
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Deleted old database file.")
        except Exception as e:
            print(f"Warning: Could not delete old database: {e}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())

    cur = conn.cursor()

    # ── Users ──
    users = [
        ('admin', 'admin', 'Administrator', 'admin'),
        ('demo', 'demo', 'Demo User', 'user'),
    ]
    user_ids = {}
    for username, password, display_name, role in users:
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing = cur.fetchone()
        if existing:
            user_ids[username] = existing['id']
            print(f"  User '{username}' already exists (id={existing['id']})")
        else:
            cur.execute(
                'INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)',
                (username, generate_password_hash(password), display_name, role)
            )
            user_ids[username] = cur.lastrowid
            print(f"  Created user: {username} / {password} (role={role})")

    conn.commit()

    # Use demo user for seed data
    uid = user_ids['demo']

    # Check if demo data already seeded
    cur.execute('SELECT COUNT(*) as cnt FROM clients WHERE user_id = ?', (uid,))
    if cur.fetchone()['cnt'] > 0:
        print("\nDemo data already exists. Skipping seed.")
        conn.close()
        return

    # ── Dates ──
    now = datetime.now()
    today = now.strftime('%Y-%m-%dT%H:%M')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    in_3_days = (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
    in_10_mins = (now + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M')

    # ── Clients ──
    clients = [
        (uid, "Rajesh Kumar", "+91 9876543210", "TechCorp", "IT", "AI Surveillance",
         "Wants cloud backup and remote access", "High-priority enterprise client.", "Active"),
        (uid, "Sarah Jenkins", "+1 555-1234", "DesignHub", "Design", "Website",
         "Needs custom dashboard for portfolio", "Very responsive. Prefers email.", "Active"),
        (uid, "Amit Patel", "+91 8888888888", "RetailPro", "Retail", "ERP",
         "Multi-store inventory management", "Has budget approved. Ready to proceed.", "Active"),
        (uid, "Emily Chen", "+1 444-5678", "AutoMakers", "Manufacturing", "Automation",
         "GPU support for running local LLMs", "Technical buyer. Needs POC.", "Active"),
        (uid, "Priya Sharma", "+91 7777777777", "EduLearn", "Education", "LMS Platform",
         "Needs student tracking and assessment modules", "Government contract. Long sales cycle.", "Active"),
    ]

    client_ids = []
    for c in clients:
        cur.execute('''
            INSERT INTO clients (user_id, name, phone, company, work_type, interested_product,
                                 custom_requirements, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', c)
        client_ids.append(cur.lastrowid)
    print(f"  Created {len(clients)} demo clients")

    # ── Follow-ups ──
    followups = [
        (uid, client_ids[2], yesterday, 'Call', 'Ask about the quotation sent last week.', 'Pending'),
        (uid, client_ids[0], today, 'WhatsApp', 'Send the product demo link.', 'Pending'),
        (uid, client_ids[1], tomorrow, 'Email', 'Follow up on the design proposal.', 'Pending'),
        (uid, client_ids[3], in_10_mins, 'Call', 'Confirm the POC demo schedule.', 'Pending'),
        (uid, client_ids[4], in_3_days, 'Meeting', 'Present the LMS platform features.', 'Pending'),
        (uid, client_ids[0], yesterday, 'Email', 'Sent initial pricing breakdown.', 'Completed'),
    ]
    for f in followups:
        cur.execute('''
            INSERT INTO followups (user_id, client_id, followup_date, followup_type, notes, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', f)
    print(f"  Created {len(followups)} demo follow-ups")

    # ── Appointments ──
    appointments = [
        (uid, client_ids[3], "Technical Architecture Review", in_10_mins,
         "Google Meet", "Discuss GPU requirements for LLMs.", "Pending"),
        (uid, client_ids[1], "Proposal Review", tomorrow,
         "HQ Office", "Finalize the website dashboard design.", "Pending"),
        (uid, client_ids[0], "Product Demo", today,
         "Zoom", "Live walkthrough of AI surveillance features.", "Pending"),
        (uid, client_ids[4], "LMS Platform Presentation", in_3_days,
         "Client Office", "Full demo of student tracking module.", "Pending"),
    ]
    for a in appointments:
        cur.execute('''
            INSERT INTO appointments (user_id, client_id, title, appointment_datetime,
                                       location, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', a)
    print(f"  Created {len(appointments)} demo appointments")

    # ── Settings ──
    cur.execute('SELECT id FROM settings WHERE user_id = ?', (uid,))
    if not cur.fetchone():
        cur.execute(
            'INSERT INTO settings (user_id, reminder_before_minutes, dark_mode) VALUES (?, ?, ?)',
            (uid, 15, 1)
        )
        print("  Created demo user settings")

    conn.commit()
    conn.close()
    print("\n✅ Database seeded successfully!")


if __name__ == '__main__':
    print("Seeding Streamux CRM database...\n")
    seed()
