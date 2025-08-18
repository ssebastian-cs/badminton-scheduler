"""
Utility functions for the Badminton Scheduler application.
Provides common functionality for routes, forms, and data processing.
"""

from flask import flash, redirect, url_for, current_app
from flask_login import current_user
from functools import wraps
from datetime import datetime, date, time
import re
from .error_handlers import ErrorHandler, FlashMessageHelper
from .logging_config import log_user_action, log_database_operation


def admin_required(f):
    """
    Decorator to require admin role for route access.
    Enhanced with proper error handling and logging.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            FlashMessageHelper.info('Please log in to access this page.')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            return ErrorHandler.handle_permission_error('access admin features')
        
        return f(*args, **kwargs)
    return decorated_function


def login_required_with_message(message=None):
    """
    Enhanced login required decorator with custom messages.
    
    Args:
        message: Custom message to show when login is required
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                FlashMessageHelper.info(message or 'Please log in to access this page.')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_future_date(date_value, field_name="Date"):
    """
    Validate that a date is in the future.
    
    Args:
        date_value: Date to validate
        field_name: Name of the field for error messages
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not date_value:
        return False, f"{field_name} is required."
    
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            return False, f"{field_name} must be in YYYY-MM-DD format."
    
    if date_value <= date.today():
        return False, f"{field_name} must be in the future."
    
    return True, None


def validate_time_range(start_time, end_time):
    """
    Validate that end time is after start time.
    
    Args:
        start_time: Start time value
        end_time: End time value
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not start_time or not end_time:
        return False, "Both start and end times are required."
    
    # Convert strings to time objects if needed
    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
        except ValueError:
            return False, "Start time must be in HH:MM format."
    
    if isinstance(end_time, str):
        try:
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return False, "End time must be in HH:MM format."
    
    if end_time <= start_time:
        return False, "End time must be after start time."
    
    return True, None


def safe_get_record(model_class, record_id, error_message=None):
    """
    Safely retrieve a database record with error handling.
    
    Args:
        model_class: SQLAlchemy model class
        record_id: ID of the record to retrieve
        error_message: Custom error message if record not found
    
    Returns:
        Record object or None if not found
    """
    try:
        record = model_class.query.get(record_id)
        if not record:
            resource_name = model_class.__name__.lower()
            FlashMessageHelper.not_found(error_message or resource_name)
            return None
        return record
    except Exception as e:
        ErrorHandler.handle_database_error(e, f"retrieving {model_class.__name__.lower()}")
        return None


def safe_delete_record(record, record_type="record", success_message=None):
    """
    Safely delete a database record with error handling.
    
    Args:
        record: Record to delete
        record_type: Type of record for messages
        success_message: Custom success message
    
    Returns:
        bool: True if successful, False otherwise
    """
    from . import db
    
    def delete_operation():
        db.session.delete(record)
        db.session.commit()
        log_database_operation('DELETE', record.__class__.__name__, getattr(record, 'id', None))
        return True
    
    success_msg = success_message or f"{record_type.title()} deleted successfully."
    error_msg = f"Failed to delete {record_type}."
    
    return ErrorHandler.safe_database_operation(
        delete_operation, 
        success_msg, 
        error_msg, 
        f"delete {record_type}"
    )


def safe_create_record(record, record_type="record", success_message=None):
    """
    Safely create a database record with error handling.
    
    Args:
        record: Record to create
        record_type: Type of record for messages
        success_message: Custom success message
    
    Returns:
        bool: True if successful, False otherwise
    """
    from . import db
    
    def create_operation():
        db.session.add(record)
        db.session.commit()
        log_database_operation('CREATE', record.__class__.__name__, getattr(record, 'id', None))
        return True
    
    success_msg = success_message or f"{record_type.title()} created successfully."
    error_msg = f"Failed to create {record_type}."
    
    return ErrorHandler.safe_database_operation(
        create_operation, 
        success_msg, 
        error_msg, 
        f"create {record_type}"
    )


def safe_update_record(record, record_type="record", success_message=None):
    """
    Safely update a database record with error handling.
    
    Args:
        record: Record to update
        record_type: Type of record for messages
        success_message: Custom success message
    
    Returns:
        bool: True if successful, False otherwise
    """
    from . import db
    
    def update_operation():
        db.session.commit()
        log_database_operation('UPDATE', record.__class__.__name__, getattr(record, 'id', None))
        return True
    
    success_msg = success_message or f"{record_type.title()} updated successfully."
    error_msg = f"Failed to update {record_type}."
    
    return ErrorHandler.safe_database_operation(
        update_operation, 
        success_msg, 
        error_msg, 
        f"update {record_type}"
    )


def check_record_ownership(record, user=None, allow_admin=True):
    """
    Check if a user owns a record or has admin privileges.
    
    Args:
        record: Database record to check
        user: User to check (defaults to current_user)
        allow_admin: Whether admin users can access any record
    
    Returns:
        bool: True if user can access the record
    """
    if not user:
        user = current_user
    
    if not user.is_authenticated:
        return False
    
    # Check ownership
    if hasattr(record, 'user_id') and record.user_id == user.id:
        return True
    
    # Check admin privileges
    if allow_admin and user.is_admin():
        return True
    
    return False


def sanitize_text_input(text, max_length=None, allow_html=False):
    """
    Sanitize text input to prevent XSS and other issues.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # Remove HTML tags if not allowed
    if not allow_html:
        text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    return text


def format_datetime_for_display(dt, format_string=None):
    """
    Format datetime for user-friendly display.
    
    Args:
        dt: Datetime object to format
        format_string: Custom format string
    
    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return ""
    
    if format_string:
        return dt.strftime(format_string)
    
    # Default format
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M')
    elif isinstance(dt, date):
        return dt.strftime('%Y-%m-%d')
    elif isinstance(dt, time):
        return dt.strftime('%H:%M')
    
    return str(dt)


def get_date_range_filter(view_type, start_date=None, end_date=None):
    """
    Get date range based on view type for filtering.
    
    Args:
        view_type: Type of view ('today', 'week', 'month', 'custom')
        start_date: Custom start date
        end_date: Custom end date
    
    Returns:
        tuple: (start_date, end_date)
    """
    from datetime import timedelta
    
    today = date.today()
    
    if view_type == 'today':
        return today, today
    elif view_type == 'week':
        # Current week (Monday to Sunday)
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        end = start + timedelta(days=6)
        return start, end
    elif view_type == 'month':
        # Current month
        start = today.replace(day=1)
        # Get last day of month
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end
    elif view_type == 'custom' and start_date and end_date:
        # Parse custom dates if they're strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        return start_date, end_date
    
    # Default to today
    return today, today


def log_user_activity(action, details=None):
    """
    Log user activity for audit trail.
    
    Args:
        action: Description of the action
        details: Additional details about the action
    """
    if current_user.is_authenticated:
        log_user_action(
            action, 
            {
                'user_id': current_user.id,
                'username': current_user.username,
                'details': details or {}
            }
        )


def log_admin_action(action_type, target_type=None, target_id=None, description=None, details=None, target_user_id=None):
    """
    Log administrative actions for audit trail.
    
    Args:
        action_type: Type of admin action performed
        target_type: Type of target (user, availability, comment, etc.)
        target_id: ID of the target record
        description: Description of the action
        details: Additional details about the action (dict or string)
        target_user_id: ID of the target user if applicable
    """
    from .models import AdminAction
    from . import db
    
    if not current_user.is_authenticated or not current_user.is_admin():
        return
    
    try:
        # Use provided description or extract from details
        if not description:
            if details and isinstance(details, dict) and 'description' in details:
                description = details['description']
            else:
                description = "Admin action performed"
        
        # Handle details - convert dict to JSON string if needed
        details_str = None
        if details:
            if isinstance(details, dict):
                import json
                details_str = json.dumps(details)
            else:
                details_str = str(details)
        
        admin_action = AdminAction(
            admin_user_id=current_user.id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            description=description,
            target_user_id=target_user_id,
            details=details_str
        )
        
        db.session.add(admin_action)
        db.session.commit()
        
        # Also log to application logs
        log_user_action(f'admin_{action_type}', {
            'target_type': target_type,
            'target_id': target_id,
            'details': details
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to log admin action: {str(e)}")
        db.session.rollback()


def get_admin_actions(limit=50, target_type=None, admin_user_id=None, action_type=None):
    """
    Get recent administrative actions for audit display.
    
    Args:
        limit: Maximum number of actions to return
        target_type: Filter by target type
        admin_user_id: Filter by admin user ID
        action_type: Filter by action type
    
    Returns:
        List of AdminAction records
    """
    from .models import AdminAction
    
    try:
        query = AdminAction.query
        
        if target_type:
            query = query.filter(AdminAction.target_type == target_type)
        
        if admin_user_id:
            query = query.filter(AdminAction.admin_user_id == admin_user_id)
            
        if action_type:
            query = query.filter(AdminAction.action_type == action_type)
        
        return query.order_by(AdminAction.created_at.desc()).limit(limit).all()
    
    except Exception as e:
        current_app.logger.error(f"Failed to get admin actions: {str(e)}")
        return []


class ValidationHelper:
    """Helper class for common validation tasks."""
    
    @staticmethod
    def validate_availability_data(date_val, start_time, end_time):
        """
        Validate availability form data.
        
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []
        
        # Validate date
        date_valid, date_error = validate_future_date(date_val)
        if not date_valid:
            errors.append(date_error)
        
        # Validate time range
        time_valid, time_error = validate_time_range(start_time, end_time)
        if not time_valid:
            errors.append(time_error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_comment_data(content, max_length=1000):
        """
        Validate comment form data.
        
        Returns:
            tuple: (is_valid: bool, errors: list, sanitized_content: str)
        """
        errors = []
        
        if not content or not content.strip():
            errors.append("Comment content is required.")
            return False, errors, ""
        
        # Sanitize content
        sanitized = sanitize_text_input(content, max_length)
        
        if len(sanitized) != len(content.strip()):
            errors.append(f"Comment is too long. Maximum {max_length} characters allowed.")
        
        return len(errors) == 0, errors, sanitized