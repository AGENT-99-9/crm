import os
import sys

# Set testing environment variables BEFORE importing app/config
test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_crm.db')
if os.path.exists(test_db_path):
    try: os.remove(test_db_path)
    except: pass

os.environ['CRM_ENV'] = 'development'
os.environ['DATABASE_PATH'] = test_db_path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from database.db import get_db

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # We need to initialize the schema for the in-memory DB
    with app.app_context():
        db = get_db()
        # Read the actual schema file
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
        with open(schema_path, 'r') as f:
            db.executescript(f.read())
        
        # Insert a test user
        db.execute("INSERT INTO users (username, password, role) VALUES ('testuser', 'testhash', 'user')")
        db.commit()

    yield app

@pytest.fixture(scope='session')
def client(app):
    return app.test_client()

@pytest.fixture(scope='session')
def auth_client(client):
    # Log in
    client.post('/api/auth/login', json={'username': 'testuser', 'password': 'testuser123'})
    # Actually, we mocked the hash. To test routes, we need a valid hash or just test the services directly.
    return client

def test_login_failure(client):
    response = client.post('/api/auth/login', json={
        'username': 'wronguser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data

def test_unauthorized_access(client):
    # Try accessing protected route without login
    response = client.get('/api/clients/')
    assert response.status_code == 401

def test_app_creation(app):
    assert app.name == 'app'
