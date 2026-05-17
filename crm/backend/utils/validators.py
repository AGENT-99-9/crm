"""
Input validation utilities.
Provides reusable validation functions for all API endpoints.
"""
import re
from datetime import datetime


class ValidationError(Exception):
    """Raised when input validation fails."""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def require_fields(data, required_fields):
    """Validate that required fields are present and non-empty."""
    if not data:
        raise ValidationError("Request body is required")
    
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            raise ValidationError(f"'{field}' is required", field=field)


def validate_string(value, field_name, min_len=1, max_len=500):
    """Validate a string field's length."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"'{field_name}' must be a string", field=field_name)
    value = value.strip()
    if len(value) < min_len:
        raise ValidationError(f"'{field_name}' must be at least {min_len} characters", field=field_name)
    if len(value) > max_len:
        raise ValidationError(f"'{field_name}' must not exceed {max_len} characters", field=field_name)
    return value


def validate_phone(value):
    """Validate phone number format (flexible)."""
    if not value or value.strip() == '':
        return None
    cleaned = re.sub(r'[\s\-\(\)]', '', value.strip())
    if not re.match(r'^\+?\d{7,15}$', cleaned):
        raise ValidationError("Invalid phone number format", field='phone')
    return value.strip()


def validate_datetime(value, field_name):
    """Validate ISO datetime string."""
    if not value or value.strip() == '':
        return None
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.strip()
    except (ValueError, AttributeError):
        raise ValidationError(f"'{field_name}' must be a valid datetime", field=field_name)


def validate_status(value, allowed_statuses):
    """Validate status against allowed values."""
    if value is None:
        return allowed_statuses[0]  # default to first
    if value not in allowed_statuses:
        raise ValidationError(
            f"Status must be one of: {', '.join(allowed_statuses)}",
            field='status'
        )
    return value


def validate_positive_int(value, field_name):
    """Validate a positive integer."""
    try:
        val = int(value)
        if val < 0:
            raise ValidationError(f"'{field_name}' must be a positive number", field=field_name)
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"'{field_name}' must be a valid number", field=field_name)


def sanitize_text(value):
    """Basic XSS sanitization for text fields stored in database."""
    if value is None:
        return None
    # Replace dangerous characters
    value = str(value)
    value = value.replace('<', '&lt;').replace('>', '&gt;')
    return value.strip()
