"""
Centralized logging configuration.
Provides structured logging with file rotation and console output.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    """Configure application-wide logging."""
    log_dir = app.config.get('LOG_DIR', os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)

    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)

    # File handler with rotation (5MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'crm.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))

    # Apply to Flask app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    return app.logger
