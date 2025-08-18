from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp
from datetime import date, time, datetime, timedelta
from .models import User
import re
import html
import bleach


class LoginForm(FlaskForm):
    """Form for user login with enhanced security validation."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=1, max=128, message='Password length is invalid')
    ])
    submit = SubmitField('Login')
    
    def validate_username(self, field):
        """Sanitize and validate username input."""
        if field.data:
            # Sanitize input
            field.data = html.escape(field.data.strip())
            # Additional security check for suspicious patterns
            if any(char in field.data for char in ['<', '>', '"', "'", '&']):
                raise ValidationError('Username contains invalid characters.')
    
    def validate_password(self, field):
        """Validate password without exposing it in logs."""
        if field.data:
            # Check for null bytes and other suspicious characters
            if '\x00' in field.data or len(field.data.encode('utf-8')) > 128:
                raise ValidationError('Invalid password format.')


class RegistrationForm(FlaskForm):
    """Form for user registration (Admin only) with enhanced security validation."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, max=128, message='Password must be between 6 and 128 characters')
    ])
    role = SelectField('Role', choices=[('User', 'User'), ('Admin', 'Admin')], default='User')
    submit = SubmitField('Create User')
    
    def validate_username(self, field):
        """Sanitize and validate username uniqueness and format."""
        if field.data:
            # Sanitize input
            field.data = html.escape(field.data.strip())
            
            # Check for uniqueness
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already exists. Please choose a different one.')
            
            # Additional security checks
            if any(char in field.data for char in ['<', '>', '"', "'", '&']):
                raise ValidationError('Username contains invalid characters.')
            
            # Check for common SQL injection patterns
            suspicious_patterns = ['union', 'select', 'drop', 'delete', 'insert', 'update', '--', ';']
            if any(pattern in field.data.lower() for pattern in suspicious_patterns):
                raise ValidationError('Username contains invalid content.')
    
    def validate_password(self, field):
        """Validate password strength and security."""
        if field.data:
            # Check for null bytes and control characters
            if '\x00' in field.data or any(ord(char) < 32 for char in field.data if char not in ['\t', '\n', '\r']):
                raise ValidationError('Password contains invalid characters.')
            
            # Basic password strength validation
            if len(field.data) < 6:
                raise ValidationError('Password must be at least 6 characters long.')
            
            # Check for at least one letter and one number for better security
            if not re.search(r'[a-zA-Z]', field.data) or not re.search(r'[0-9]', field.data):
                raise ValidationError('Password must contain at least one letter and one number')
    
    def validate_role(self, field):
        """Validate role selection."""
        valid_roles = ['User', 'Admin']
        if field.data not in valid_roles:
            raise ValidationError('Invalid role selected.')


class AvailabilityForm(FlaskForm):
    """Form for creating and editing availability entries with enhanced validation."""
    date = DateField('Date', validators=[DataRequired(message='Date is required')])
    start_time = TimeField('Start Time', validators=[DataRequired(message='Start time is required')])
    end_time = TimeField('End Time', validators=[DataRequired(message='End time is required')])
    submit = SubmitField('Save Availability')
    
    def validate_date(self, field):
        """Validate that the date is today or in the future and within reasonable limits."""
        if field.data:
            today = date.today()
            if field.data <= today:
                raise ValidationError('Date must be in the future')
            
            # Prevent scheduling too far in the future (1 year limit)
            max_future_date = today + timedelta(days=365)
            if field.data > max_future_date:
                raise ValidationError('Date cannot be more than one year in the future')
    
    def validate_start_time(self, field):
        """Validate start time format and reasonableness."""
        if field.data:
            # Check for reasonable time range (6 AM to 11 PM)
            if field.data < time(6, 0) or field.data > time(23, 0):
                raise ValidationError('Start time must be between 6:00 AM and 11:00 PM')
            
            # If date is today, ensure time is in the future
            if self.date.data and self.date.data == date.today():
                current_time = datetime.now().time()
                if field.data <= current_time:
                    raise ValidationError('For today\'s date, start time must be in the future')
    
    def validate_end_time(self, field):
        """Validate that end time is after start time and within reasonable limits."""
        if field.data and self.start_time.data:
            if field.data <= self.start_time.data:
                raise ValidationError('End time must be after start time')
            
            # Check for reasonable time range
            if field.data < time(6, 0) or field.data > time(23, 0):
                raise ValidationError('End time must be between 6:00 AM and 11:59 PM')
            
            # Check for reasonable duration (max 8 hours)
            start_minutes = self.start_time.data.hour * 60 + self.start_time.data.minute
            end_minutes = field.data.hour * 60 + field.data.minute
            duration_minutes = end_minutes - start_minutes
            
            if duration_minutes > 480:  # 8 hours
                raise ValidationError('Availability duration cannot exceed 8 hours')
            
            if duration_minutes < 30:  # 30 minutes minimum
                raise ValidationError('Availability duration must be at least 30 minutes')


class AvailabilityFilterForm(FlaskForm):
    """Form for filtering availability entries with enhanced validation."""
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    submit = SubmitField('Filter')
    
    def validate_start_date(self, field):
        """Validate start date is not too far in the past."""
        if field.data:
            # Limit to 1 year in the past
            min_date = date.today() - timedelta(days=365)
            if field.data < min_date:
                raise ValidationError('Start date cannot be more than one year in the past')
    
    def validate_end_date(self, field):
        """Validate that end date is after start date and within reasonable limits."""
        if field.data:
            if self.start_date.data and field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')
            
            # Limit to 1 year in the future
            max_date = date.today() + timedelta(days=365)
            if field.data > max_date:
                raise ValidationError('End date cannot be more than one year in the future')
            
            # Limit date range to prevent performance issues
            if self.start_date.data:
                date_range = field.data - self.start_date.data
                if date_range.days > 90:  # 3 months max range
                    raise ValidationError('Date range cannot exceed 90 days')


def validate_comment_content(form, field):
    """Custom validator for comment content that handles whitespace properly."""
    if not field.data:
        raise ValidationError('Comment content is required')
    
    # Check if content is only whitespace
    if field.data.strip() == '':
        raise ValidationError('Comment content cannot be empty')


class CommentForm(FlaskForm):
    """Form for creating and editing comments with enhanced security validation."""
    content = TextAreaField('Comment', validators=[
        validate_comment_content,
        Length(min=1, max=1000, message='Comment must be between 1 and 1000 characters')
    ])
    submit = SubmitField('Post Comment')
    
    def validate_content(self, field):
        """Validate and sanitize comment content."""
        if field.data and field.data.strip():
            # Store original data for security checks
            original_data = field.data
            
            # Check for suspicious patterns BEFORE sanitizing to catch attempts
            original_lower = original_data.lower()
            suspicious_patterns = [
                '<script', '</script>', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
                'onclick=', 'onmouseover=', 'onfocus=', 'onblur=', 'onchange=', 'onsubmit='
            ]
            
            for pattern in suspicious_patterns:
                if pattern in original_lower:
                    raise ValidationError('Comment contains invalid content')
            
            # Strip and sanitize HTML content using bleach
            field.data = field.data.strip()
            allowed_tags = []  # No HTML tags allowed
            field.data = bleach.clean(field.data, tags=allowed_tags, strip=True)
            
            # Check for excessive special characters (potential spam/injection)
            special_char_count = sum(1 for char in field.data if not char.isalnum() and char not in ' .,!?-_()[]{}:;"\'')
            if special_char_count > len(field.data) * 0.3:  # More than 30% special characters
                raise ValidationError('Comment contains too many special characters')
            
            # Check for repeated characters (potential spam)
            if re.search(r'(.)\1{10,}', field.data):  # Same character repeated 11+ times
                raise ValidationError('Comment contains invalid repeated characters')


# Custom validator functions for reuse
def validate_future_date(form, field):
    """Custom validator to ensure date is in the future."""
    if field.data and field.data <= date.today():
        raise ValidationError('Date must be in the future.')


def validate_reasonable_time_range(form, field):
    """Custom validator for reasonable time ranges."""
    if field.data:
        if field.data < time(6, 0) or field.data > time(23, 59):
            raise ValidationError('Time must be between 6:00 AM and 11:59 PM.')


def validate_no_html_injection(form, field):
    """Custom validator to prevent HTML/script injection."""
    if field.data:
        # Check for HTML tags and script injection
        html_patterns = ['<', '>', 'script', 'javascript:', 'vbscript:', 'onload', 'onerror']
        content_lower = field.data.lower()
        for pattern in html_patterns:
            if pattern in content_lower:
                raise ValidationError('Input contains invalid characters or content.')


def sanitize_input(input_string):
    """Utility function to sanitize user input."""
    if not input_string:
        return input_string
    
    # Strip whitespace
    sanitized = input_string.strip()
    
    # HTML escape
    sanitized = html.escape(sanitized)
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in ['\t', '\n', '\r'])
    
    return sanitized


def validate_csrf_token(form):
    """Additional CSRF validation if needed."""
    # This is handled automatically by Flask-WTF, but can be extended here
    pass