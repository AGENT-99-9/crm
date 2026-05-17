"""
Application configuration management.
Centralizes all config values with environment variable overrides.
"""
import os
import secrets


class Config:
    """Base configuration."""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    import sys
    if getattr(sys, 'frozen', False):
        _fallback_db = os.path.join(os.path.expanduser('~'), '.streamux_crm', 'crm.db')
    else:
        _fallback_db = os.path.join(BASE_DIR, 'database', 'crm.db')
        
    DB_PATH = os.environ.get('DATABASE_PATH', _fallback_db)
    
    # SCHEMA_PATH should always load from the bundle
    try:
        _schema_base = sys._MEIPASS
    except Exception:
        _schema_base = BASE_DIR
        
    SCHEMA_PATH = os.path.join(_schema_base, 'database', 'schema.sql')

    # Security
    SECRET_KEY = os.environ.get('CRM_SECRET_KEY', secrets.token_hex(32))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CORS
    CORS_ORIGINS = os.environ.get('CRM_CORS_ORIGINS', '*')

    # App
    DEBUG = os.environ.get('CRM_DEBUG', 'false').lower() == 'true'
    PORT = int(os.environ.get('CRM_PORT', 5001))
    HOST = os.environ.get('CRM_HOST', '127.0.0.1')

    # Logging
    LOG_LEVEL = os.environ.get('CRM_LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_config():
    """Return config based on CRM_ENV environment variable."""
    env = os.environ.get('CRM_ENV', 'development').lower()
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)
