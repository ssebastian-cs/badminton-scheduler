from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

# Import db from __init__.py to avoid circular imports
from . import db


class User(UserMixin, db.Model):
    """User model with authentication fields and role-based access."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    availability_entries = db.relationship('Availability', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, password, role='User'):
        """Initialize user with hashed password."""
        self.username = username
        self.set_password(password)
        self.role = role
        self.is_active = True
    
    def set_password(self, password):
        """Hash and set the user's password."""
        if not password or len(password) < 6 or len(password) > 128:
            raise ValueError("Password must be between 6 and 128 characters")
        
        # Check password strength - must contain at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        if not (has_letter and has_number):
            raise ValueError("Password must contain at least one letter and one number")
            
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'Admin'
    
    def get_id(self):
        """Return user ID as string for Flask-Login."""
        return str(self.id)
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format and length."""
        if not username:
            raise ValueError("Username is required")
        if len(username) < 3 or len(username) > 20:
            raise ValueError("Username must be between 3 and 20 characters")
        if not username.replace('_', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return username
    
    @validates('role')
    def validate_role(self, key, role):
        """Validate user role."""
        valid_roles = ['User', 'Admin']
        if role not in valid_roles:
            raise ValueError("Role must be either 'User' or 'Admin'")
        return role
    
    def __str__(self):
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'


class Availability(db.Model):
    """Availability model with date/time validation."""
    
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_availability_date_user', 'date', 'user_id'),
    )
    
    def __init__(self, user_id, date, start_time, end_time):
        """Initialize availability entry with validation."""
        self.user_id = user_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self._validate_times()
        self._validate_future_date()
        self._validate_reasonable_hours()
        self._validate_duration()
    
    def _validate_times(self):
        """Validate that end time is after start time."""
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after start time")
    
    def _validate_future_date(self):
        """Validate that date is in the future."""
        if self.date and self.date <= date.today():
            raise ValueError("Date must be in the future")
    
    def _validate_reasonable_hours(self):
        """Validate that times are within reasonable hours."""
        if self.start_time:
            if self.start_time < time(6, 0) or self.start_time > time(23, 0):
                raise ValueError("Start time must be between 6:00 AM and 11:00 PM")
        
        if self.end_time:
            if self.end_time < time(6, 0) or self.end_time >= time(23, 30):
                raise ValueError("End time must be between 6:00 AM and 11:59 PM")
    
    def _validate_duration(self):
        """Validate availability duration."""
        if self.start_time and self.end_time:
            # Calculate duration in minutes
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
            end_minutes = self.end_time.hour * 60 + self.end_time.minute
            duration_minutes = end_minutes - start_minutes
            
            if duration_minutes < 30:
                raise ValueError("Availability duration must be at least 30 minutes")
            
            if duration_minutes > 480:  # 8 hours
                raise ValueError("Availability duration cannot exceed 8 hours")
    
    @validates('date')
    def validate_date(self, key, availability_date):
        """Validate availability date."""
        if not availability_date:
            raise ValueError("Date is required")
        if availability_date <= date.today():
            raise ValueError("Date must be in the future")
        return availability_date
    
    @validates('start_time')
    def validate_start_time(self, key, start_time):
        """Validate start time."""
        if not start_time:
            raise ValueError("Start time is required")
        return start_time
    
    @validates('end_time')
    def validate_end_time(self, key, end_time):
        """Validate end time."""
        if not end_time:
            raise ValueError("End time is required")
        if self.start_time and end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return end_time
    
    def update(self, date=None, start_time=None, end_time=None):
        """Update availability entry with validation."""
        if date is not None:
            self.date = date
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        
        self._validate_times()
        self._validate_future_date()
        self._validate_reasonable_hours()
        self._validate_duration()
        self.updated_at = datetime.utcnow()
    
    def __str__(self):
        # Try to get the user from the relationship first
        if hasattr(self, 'user') and self.user:
            username = self.user.username
        else:
            # If user relationship is not loaded, try to get it from the database
            from . import db
            user = db.session.get(User, self.user_id)
            username = user.username if user else f"User {self.user_id}"
        
        return f"{username} - {self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def __repr__(self):
        if self.user:
            return f'<Availability {self.user.username} on {self.date} from {self.start_time} to {self.end_time}>'
        return f'<Availability {self.id} on {self.date} from {self.start_time} to {self.end_time}>'


class Comment(db.Model):
    """Comment model with user relationships."""
    
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, user_id, content):
        """Initialize comment with validation."""
        self.user_id = user_id
        self.content = content
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @validates('content')
    def validate_content(self, key, content):
        """Validate comment content."""
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        if len(content) > 1000:
            raise ValueError("Comment must be between 1 and 1000 characters")
        
        # Security validation - check for malicious content
        malicious_patterns = [
            '<script', 'javascript:', '<img', 'onclick=', 'onload=', 'onerror='
        ]
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if pattern in content_lower:
                raise ValueError("Comment contains invalid content")
        
        # Spam detection - check for too many special characters
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        if special_chars > len(content) * 0.3:  # More than 30% special characters
            raise ValueError("Comment contains too many special characters")
        
        # Check for repeated characters (spam detection)
        for i in range(len(content) - 12):
            if content[i] == content[i+1] == content[i+2] == content[i+3] == content[i+4] == content[i+5] == content[i+6] == content[i+7] == content[i+8] == content[i+9] == content[i+10] == content[i+11] == content[i+12]:
                raise ValueError("Comment contains invalid repeated characters")
        
        return content.strip()
    
    def update_content(self, new_content):
        """Update comment content with validation."""
        self.content = new_content
        self.updated_at = datetime.utcnow()
    
    def __str__(self):
        # Try to get the user from the relationship first
        if hasattr(self, 'user') and self.user:
            username = self.user.username
        else:
            # If user relationship is not loaded, try to get it from the database
            from . import db
            user = db.session.get(User, self.user_id)
            username = user.username if user else f"User {self.user_id}"
        
        return f"Comment by {username}: {self.content}"
    
    def __repr__(self):
        if self.user:
            return f'<Comment by {self.user.username}: {self.content[:50]}...>'
        return f'<Comment {self.id}: {self.content[:50]}...>'


class AdminAction(db.Model):
    """Audit logging model for administrative actions."""
    
    __tablename__ = 'admin_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False)  # 'user', 'availability', 'comment'
    target_id = db.Column(db.Integer, nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User affected by action
    description = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)  # JSON or additional details
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    admin_user = db.relationship('User', foreign_keys=[admin_user_id], backref='admin_actions_performed')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='admin_actions_received')
    
    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_admin_actions_type_date', 'action_type', 'created_at'),
        db.Index('idx_admin_actions_target', 'target_type', 'target_id'),
    )
    
    def __init__(self, admin_user_id, action_type, target_type, target_id, description, target_user_id=None, details=None):
        """Initialize admin action log entry."""
        self.admin_user_id = admin_user_id
        self.action_type = action_type
        self.target_type = target_type
        self.target_id = target_id
        self.target_user_id = target_user_id
        self.description = description
        self.details = details
    
    @validates('action_type')
    def validate_action_type(self, key, action_type):
        """Validate action type."""
        valid_actions = [
            'create_user', 'block_user', 'unblock_user', 'delete_user',
            'edit_availability', 'delete_availability',
            'edit_comment', 'delete_comment'
        ]
        if action_type not in valid_actions:
            raise ValueError(f"Action type must be one of: {', '.join(valid_actions)}")
        return action_type
    
    @validates('target_type')
    def validate_target_type(self, key, target_type):
        """Validate target type."""
        valid_targets = ['user', 'availability', 'comment']
        if target_type not in valid_targets:
            raise ValueError(f"Target type must be one of: {', '.join(valid_targets)}")
        return target_type
    
    def __repr__(self):
        return f'<AdminAction {self.action_type} on {self.target_type}:{self.target_id} by {self.admin_user.username}>'