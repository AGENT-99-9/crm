"""
Streamux CRM — Application Factory.
Production-grade Flask application with centralized configuration,
logging, error handling, and blueprint registration.
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import get_config
from database.db import init_db, register_db
from utils.logger import setup_logger
from utils.validators import ValidationError
import os


import sys

def get_base_path():
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'frontend')
    except Exception:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

def create_app(config_class=None):
    """Application factory pattern."""
    if config_class is None:
        config_class = get_config()

    frontend_dir = get_base_path()
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='/')

    # Load configuration
    app.config.from_object(config_class)
    app.secret_key = config_class.SECRET_KEY

    # Setup logging
    logger = setup_logger(app)
    logger.info("Starting Streamux CRM application")

    # Initialize extensions
    CORS(app, supports_credentials=True, origins=app.config.get('CORS_ORIGINS', '*'))

    # Initialize database
    init_db(app)
    register_db(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.clients import clients_bp
    from routes.appointments import appointments_bp
    from routes.followups import followups_bp
    from routes.dashboard import dashboard_bp
    from routes.settings import settings_bp
    from routes.reminders import reminders_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(followups_bp, url_prefix='/api/followups')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(reminders_bp, url_prefix='/api/reminders')

    # --- Centralized Error Handlers ---
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({'error': e.message, 'field': e.field}), 400

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(404)
    def not_found(e):
        # Check if it's an API request
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    # --- Static file routes ---
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    logger.info("Application initialized successfully")
    return app


# Entry point
app = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.config.get('DEBUG', True),
        port=app.config.get('PORT', 5000),
        host=app.config.get('HOST', '127.0.0.1')
    )
