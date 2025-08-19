from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, SubmitField,
    DateField, TimeField, TextAreaField
)
from wtforms.validators import DataRequired, Length, ValidationError, Regexp
from datetime import date, time, datetime, timedelta
from .models import User
import re
import html
import bleach

# -------------------------------
# Timezone helpers
# -------------------------------

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo  # fallback for older Python

def get_tz(tz_name="America/Edmonton"):
    """
    Resolve the app's timezone. Defaults to America/Edmonton.
    Can be overridden via Flask config: APP_TIMEZONE='America/Edmonton'
    """
    try:
        from flask import current_app
        tz_name = (current_app.config.get('APP_TIMEZONE') or tz_name).strip()
    except Exception:
        pass

    try:
        return ZoneInfo(tz_name)
    except Exception:
        import pytz
        return pytz.timezone(tz_name)

def now_tz() -> datetime:
    """Timezone-aware 'now'."""
    return datetime.now(get_tz())

def combine_local(d: date, t: time) -> datetime:
    """
    Combine a date and time into a timezone-aware datetime in the app's local TZ.
    Works across Python versions by replacing tzinfo after combine().
    """
    return datetime.combine(d, t).replace(tzinfo=get_tz())

# -------------------------------
# Shared constants & validators
# -------------------------------

USERNAME_REGEX = r'^[a-zA-Z0-9_]+$'
SQL_INJECTION_PATTERNS = ['union', 'select', 'drop', 'delete', 'insert', 'update', '--', ';']
XSS_PATTERNS = [
    '<script', '</script>', 'javascript:', 'vbscript:',
    'onload=', 'onerror=', 'onclick=', 'onmouseover=',
    'onfocus=', 'onblur=', 'onchange=', 'onsubmit='
]

def sanitize_input(value: str) -> str:
    """Utility to sanitize user input consistently."""
    if not value:
        return value
    value = value.strip()
    value = html.escape(value)
    return ''.join(ch for ch in value if ord(ch) >= 32 or ch in ['\t', '\n', '\r'])

def validate_username_common(field):
    """Shared validation for usernames."""
    field.data = sanitize_input(field.data)
    if not re.match(USERNAME_REGEX, field.data):
        raise ValidationError("Username can only contain letters, numbers, and underscores.")
    if any(p in field.data.lower() for p in SQL_INJECTION_PATTERNS):
        raise ValidationError("Username contains invalid content.")

def validate_password_common(field, min_length=6):
    """Shared password validation."""
    if '\x00' in field.data or len(field.data.encode("utf-8")) > 128:
        raise ValidationError("Invalid password format.")
    if len(field.data) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters long.")
    if not re.search(r'[a-zA-Z]', field.data) or not re.search(r'[0-9]', field.data):
        raise ValidationError("Password must contain at least one letter and one number.")

def validate_future_date(form, field):
    # Strict future date validation - not used by AvailabilityForm (it allows 'today')
    if field.data and field.data <= date.today():
        raise ValidationError("Date must be in the future.")

def validate_reasonable_time(form, field):
    if field.data and not (time(6, 0) <= field.data <= time(23, 59)):
        raise ValidationError("Time must be between 6:00 AM and 11:59 PM.")

def validate_comment_content(form, field):
    if not field.data or not field.data.strip():
        raise ValidationError("Comment content cannot be empty")

# -------------------------------
# Forms
# -------------------------------

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=3, max=20), Regexp(USERNAME_REGEX)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=1, max=128)
    ])
    submit = SubmitField("Login")

    def validate_username(self, field):
        validate_username_common(field)

    def validate_password(self, field):
        validate_password_common(field, min_length=1)

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=3, max=20), Regexp(USERNAME_REGEX)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=6, max=128)
    ])
    role = SelectField("Role", choices=[("User", "User"), ("Admin", "Admin")], default="User")
    submit = SubmitField("Create User")

    def validate_username(self, field):
        validate_username_common(field)
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already exists.")

    def validate_password(self, field):
        validate_password_common(field)

    def validate_role(self, field):
        if field.data not in ["User", "Admin"]:
            raise ValidationError("Invalid role selected.")

class AvailabilityForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    end_time = TimeField("End Time", validators=[DataRequired()])
    submit = SubmitField("Save Availability")

    def validate_date(self, field):
        today = date.today()
        if field.data < today:
            raise ValidationError("Date cannot be in the past")
        if field.data > today + timedelta(days=365):
            raise ValidationError("Date cannot be more than one year in the future")

    def validate_start_time(self, field):
        if not self.date.data or not field.data:
            return

        validate_reasonable_time(self, field)

        # If date is today, ensure time is in the future
        if self.date.data == date.today():
            current_time = datetime.now().time()
            if field.data <= current_time:
                raise ValidationError("For today's date, start time must be in the future")
        # Future dates are automatically valid

    def validate_end_time(self, field):
        if not self.date.data or not field.data or not self.start_time.data:
            return

        validate_reasonable_time(self, field)

        if field.data <= self.start_time.data:
            raise ValidationError("End time must be after start time")

        # Duration checks
        start_minutes = self.start_time.data.hour * 60 + self.start_time.data.minute
        end_minutes = field.data.hour * 60 + field.data.minute
        duration_minutes = end_minutes - start_minutes
        
        if duration_minutes < 30:
            raise ValidationError("Availability must be at least 30 minutes")
        if duration_minutes > 480:
            raise ValidationError("Availability cannot exceed 8 hours")

class AvailabilityFilterForm(FlaskForm):
    start_date = DateField("Start Date")
    end_date = DateField("End Date")
    submit = SubmitField("Filter")

    def validate_start_date(self, field):
        if field.data and field.data < date.today() - timedelta(days=365):
            raise ValidationError("Start date cannot be more than one year in the past")

    def validate_end_date(self, field):
        if field.data:
            if self.start_date.data and field.data < self.start_date.data:
                raise ValidationError("End date must be after start date")
            if field.data > date.today() + timedelta(days=365):
                raise ValidationError("End date cannot be more than one year in the future")
            if self.start_date.data and (field.data - self.start_date.data).days > 90:
                raise ValidationError("Date range cannot exceed 90 days")

class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[
        validate_comment_content, Length(min=1, max=1000)
    ])
    submit = SubmitField("Post Comment")

    def validate_content(self, field):
        raw = field.data.strip()
        if any(p in raw.lower() for p in XSS_PATTERNS):
            raise ValidationError("Comment contains invalid content")

        # Sanitize
        field.data = bleach.clean(raw, tags=[], strip=True)

        # Spam checks
        special_chars = sum(1 for c in field.data if not c.isalnum() and c not in " .,!?-_()[]{}:;\"'")
        if special_chars > len(field.data) * 0.3:
            raise ValidationError("Comment contains too many special characters")
        if re.search(r"(.)\1{10,}", field.data):
            raise ValidationError("Comment contains invalid repeated characters")
