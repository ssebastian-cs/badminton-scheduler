"""
Enhanced error handling utilities for the Badminton Scheduler application.
Provides comprehensive error handling, logging, and user feedback mechanisms.
"""

from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime, timezone
from .error_tracking import track_error


class ErrorHandler:
    """Centralized error handling class for consistent error management."""
    
    @staticmethod
    def handle_database_error(error, operation="database operation", user_message=None):
        """
        Handle database-related errors with appropriate logging and user feedback.
        
        Args:
            error: The database error that occurred
            operation: Description of the operation that failed
            user_message: Custom message to show to user (optional)
        
        Returns:
            tuple: (success: bool, error_message: str)
        """
        from .security import log_security_event
        
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Log the error with context
        log_entry = f"Database error during {operation}: {error_type} - {error_msg}"
        if current_user.is_authenticated:
            log_entry += f" (User: {current_user.username})"
        
        current_app.logger.error(log_entry)
        log_security_event('DATABASE_ERROR', log_entry, 'ERROR')
        
        # Track the error for monitoring
        track_error(error, 'DATABASE_ERROR', 'ERROR', operation=operation)
        
        # Determine user-friendly message based on error type
        if isinstance(error, IntegrityError):
            if user_message:
                flash_message = user_message
            elif "UNIQUE constraint failed" in error_msg:
                flash_message = "This record already exists. Please check your input."
            elif "NOT NULL constraint failed" in error_msg:
                flash_message = "Required information is missing. Please fill in all required fields."
            else:
                flash_message = "The data you entered conflicts with existing records. Please check and try again."
        elif isinstance(error, OperationalError):
            flash_message = "Database is temporarily unavailable. Please try again in a moment."
        else:
            flash_message = user_message or "An error occurred while processing your request. Please try again."
        
        flash(flash_message, 'error')
        return False, flash_message
    
    @staticmethod
    def handle_validation_error(errors, form_name="form"):
        """
        Handle form validation errors with user-friendly messages.
        
        Args:
            errors: Dictionary of field errors from WTForms
            form_name: Name of the form for logging
        
        Returns:
            bool: False (indicating validation failed)
        """
        current_app.logger.warning(f"Validation errors in {form_name}: {errors}")
        
        # Create user-friendly error messages
        error_messages = []
        for field, field_errors in errors.items():
            for error in field_errors:
                error_messages.append(f"{field.replace('_', ' ').title()}: {error}")
        
        if error_messages:
            flash("Please correct the following errors: " + "; ".join(error_messages), 'error')
        else:
            flash("Please check your input and try again.", 'error')
        
        return False
    
    @staticmethod
    def handle_permission_error(required_permission="access", redirect_to='availability.dashboard'):
        """
        Handle permission/authorization errors.
        
        Args:
            required_permission: Description of required permission
            redirect_to: Route to redirect to after error
        
        Returns:
            Flask redirect response
        """
        from .security import log_security_event
        
        user_info = f"User: {current_user.username}" if current_user.is_authenticated else "Anonymous user"
        log_security_event('PERMISSION_DENIED', 
                          f"Permission denied for {required_permission} ({user_info})", 
                          'WARNING')
        
        flash(f"You don't have permission to {required_permission}.", 'error')
        return redirect(url_for(redirect_to))
    
    @staticmethod
    def handle_not_found_error(resource_type="resource", redirect_to='availability.dashboard'):
        """
        Handle resource not found errors.
        
        Args:
            resource_type: Type of resource that wasn't found
            redirect_to: Route to redirect to after error
        
        Returns:
            Flask redirect response
        """
        current_app.logger.warning(f"{resource_type.title()} not found - URL: {request.url}")
        flash(f"The {resource_type} you're looking for doesn't exist or has been removed.", 'error')
        return redirect(url_for(redirect_to))
    
    @staticmethod
    def log_and_flash_success(message, operation="operation"):
        """
        Log successful operations and show success message to user.
        
        Args:
            message: Success message to show user
            operation: Description of successful operation for logging
        """
        user_info = f"User: {current_user.username}" if current_user.is_authenticated else "Anonymous user"
        current_app.logger.info(f"Successful {operation} ({user_info})")
        flash(message, 'success')
    
    @staticmethod
    def safe_database_operation(operation_func, success_message=None, error_message=None, operation_name="operation"):
        """
        Safely execute a database operation with comprehensive error handling.
        
        Args:
            operation_func: Function to execute (should return True on success)
            success_message: Message to show on success
            error_message: Custom error message
            operation_name: Name of operation for logging
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = operation_func()
            if result:
                if success_message:
                    ErrorHandler.log_and_flash_success(success_message, operation_name)
                return True
            else:
                flash(error_message or f"Failed to complete {operation_name}.", 'error')
                return False
        except SQLAlchemyError as e:
            from . import db
            db.session.rollback()
            ErrorHandler.handle_database_error(e, operation_name, error_message)
            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error in {operation_name}: {str(e)}")
            track_error(e, 'UNEXPECTED_ERROR', 'ERROR', operation=operation_name)
            flash(error_message or f"An unexpected error occurred during {operation_name}.", 'error')
            return False


def register_error_handlers(app):
    """Register comprehensive error handlers for the Flask application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        from .security import log_security_event
        log_security_event('BAD_REQUEST', f'400 error: {error} - URL: {request.url}', 'INFO')
        track_error(error, 'BAD_REQUEST', 'WARNING')
        
        if request.is_json:
            return jsonify({'error': 'Bad request', 'message': 'Invalid request format'}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        from .security import log_security_event
        user_info = f"User: {current_user.username}" if current_user.is_authenticated else "Anonymous user"
        log_security_event('FORBIDDEN_ACCESS', 
                          f'403 error: {error} - URL: {request.url} ({user_info})', 
                          'WARNING')
        track_error(error, 'FORBIDDEN_ACCESS', 'WARNING')
        
        if request.is_json:
            return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        current_app.logger.info(f'404 error: Page not found - URL: {request.url}')
        track_error(error, 'NOT_FOUND', 'INFO')
        
        if request.is_json:
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        from .security import log_security_event
        log_security_event('REQUEST_TOO_LARGE', 
                          f'413 error: {error} - URL: {request.url}', 
                          'WARNING')
        track_error(error, 'REQUEST_TOO_LARGE', 'WARNING')
        
        if request.is_json:
            return jsonify({'error': 'Request too large', 'message': 'File or request size exceeds limit'}), 413
        return render_template('errors/413.html'), 413
    
    @app.errorhandler(429)
    def too_many_requests(error):
        from .security import log_security_event
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        log_security_event('RATE_LIMIT_HIT', 
                          f'429 error: Rate limit exceeded - IP: {client_ip}', 
                          'WARNING')
        track_error(error, 'RATE_LIMIT_EXCEEDED', 'WARNING', client_ip=client_ip)
        
        if request.is_json:
            return jsonify({'error': 'Too many requests', 'message': 'Rate limit exceeded'}), 429
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        from .security import log_security_event
        from . import db
        
        # Log detailed error information
        error_details = f'500 error: {error} - URL: {request.url}'
        if current_user.is_authenticated:
            error_details += f' - User: {current_user.username}'
        
        # Log stack trace for debugging
        current_app.logger.error(f'{error_details}\nStack trace:\n{traceback.format_exc()}')
        log_security_event('INTERNAL_ERROR', error_details, 'ERROR')
        track_error(error, 'INTERNAL_SERVER_ERROR', 'CRITICAL', stack_trace=traceback.format_exc())
        
        # Rollback any pending database transactions
        try:
            db.session.rollback()
        except Exception:
            pass
        
        if request.is_json:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Handle SQLAlchemy database errors."""
        from . import db
        from .security import log_security_event
        
        db.session.rollback()
        
        error_msg = f'Database error: {type(error).__name__} - {str(error)}'
        if current_user.is_authenticated:
            error_msg += f' - User: {current_user.username}'
        
        current_app.logger.error(error_msg)
        log_security_event('DATABASE_ERROR', error_msg, 'ERROR')
        track_error(error, 'DATABASE_ERROR', 'ERROR')
        
        flash('A database error occurred. Please try again.', 'error')
        
        if request.is_json:
            return jsonify({'error': 'Database error', 'message': 'Database operation failed'}), 500
        
        # Redirect to dashboard or login based on authentication status
        if current_user.is_authenticated:
            return redirect(url_for('availability.dashboard'))
        else:
            return redirect(url_for('auth.login'))
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors not caught by other handlers."""
        from .security import log_security_event
        from . import db
        
        # Don't handle HTTP exceptions here (let other handlers deal with them)
        if isinstance(error, HTTPException):
            return error
        
        # Log the unexpected error
        error_msg = f'Unexpected error: {type(error).__name__} - {str(error)} - URL: {request.url}'
        if current_user.is_authenticated:
            error_msg += f' - User: {current_user.username}'
        
        current_app.logger.error(f'{error_msg}\nStack trace:\n{traceback.format_exc()}')
        log_security_event('UNEXPECTED_ERROR', error_msg, 'ERROR')
        track_error(error, 'UNEXPECTED_ERROR', 'CRITICAL', stack_trace=traceback.format_exc())
        
        # Rollback any pending database transactions
        try:
            db.session.rollback()
        except Exception:
            pass
        
        flash('An unexpected error occurred. The issue has been logged.', 'error')
        
        if request.is_json:
            return jsonify({'error': 'Unexpected error', 'message': 'An unexpected error occurred'}), 500
        
        # Redirect to appropriate page
        if current_user.is_authenticated:
            return redirect(url_for('availability.dashboard'))
        else:
            return redirect(url_for('auth.login'))


class FlashMessageHelper:
    """Helper class for consistent flash messaging across the application."""
    
    @staticmethod
    def success(message):
        """Flash a success message."""
        flash(message, 'success')
    
    @staticmethod
    def error(message):
        """Flash an error message."""
        flash(message, 'error')
    
    @staticmethod
    def info(message):
        """Flash an info message."""
        flash(message, 'info')
    
    @staticmethod
    def warning(message):
        """Flash a warning message."""
        flash(message, 'warning')
    
    @staticmethod
    def validation_errors(form):
        """Flash validation errors from a WTForms form."""
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.replace('_', ' ').title()}: {error}", 'error')
    
    @staticmethod
    def database_success(operation):
        """Flash a success message for database operations."""
        flash(f"{operation.title()} completed successfully.", 'success')
    
    @staticmethod
    def database_error(operation):
        """Flash an error message for database operations."""
        flash(f"Failed to {operation}. Please try again.", 'error')
    
    @staticmethod
    def permission_denied(action="perform this action"):
        """Flash a permission denied message."""
        flash(f"You don't have permission to {action}.", 'error')
    
    @staticmethod
    def not_found(resource="resource"):
        """Flash a not found message."""
        flash(f"The {resource} you're looking for doesn't exist.", 'error')