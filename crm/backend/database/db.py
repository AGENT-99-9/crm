"""
Database connection manager.
Provides context-managed connections with WAL mode and foreign key enforcement.
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash
from flask import g, current_app


def get_db_path():
    """Get database path from app config or fallback."""
    try:
        return current_app.config['DB_PATH']
    except RuntimeError:
        return os.path.join(os.path.dirname(__file__), 'crm.db')


def get_db():
    """Get a database connection for the current request context.
    Reuses connection within the same request via Flask's g object.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_standalone_connection():
    """Get a standalone connection (for use outside request context like init/seed)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(app):
    """Initialize database schema and create default admin user."""
    db_path = app.config['DB_PATH']
    schema_path = app.config['SCHEMA_PATH']

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    with open(schema_path, 'r') as f:
        conn.executescript(f.read())

    cur = conn.cursor()

    # Create default admin user if not exists
    cur.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cur.fetchone():
        cur.execute(
            'INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)',
            ('admin', generate_password_hash('admin'), 'Administrator', 'admin')
        )
        admin_id = cur.lastrowid
        # Create default settings for admin
        cur.execute(
            'INSERT INTO settings (user_id, reminder_before_minutes, dark_mode) VALUES (?, ?, ?)',
            (admin_id, 15, 1)
        )
        app.logger.info("Created default admin user")

    conn.commit()
    conn.close()
    app.logger.info("Database initialized successfully")


def register_db(app):
    """Register database teardown with Flask app."""
    app.teardown_appcontext(close_db)
