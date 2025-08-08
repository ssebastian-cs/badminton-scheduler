from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# This will be imported from app.py
db = None
login_manager = None

def init_models(database, login_mgr):
    global db, login_manager
    db = database
    login_manager = login_mgr

class User(UserMixin, db.Model):
    """User model for authentication and profile information."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    availability = db.relationship('Availability', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Availability(db.Model):
    """Model for tracking user availability."""
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time_slot = db.Column(db.String(50), nullable=True)  # Legacy field for backward compatibility
    time_start = db.Column(db.Time, nullable=True, index=True)  # Start time for availability
    time_end = db.Column(db.Time, nullable=True, index=True)    # End time for availability
    is_all_day = db.Column(db.Boolean, default=True, index=True)  # Flag for all-day availability
    status = db.Column(db.Enum('available', 'tentative', 'not_available', name='availability_status'), 
                      nullable=False, default='available', index=True)
    play_preference = db.Column(db.Enum('drop_in', 'book_court', 'either', name='play_preference'), 
                               nullable=True, default='either')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', 'time_start', 'time_end', name='unique_availability_time'),
        db.Index('idx_availability_date_user', 'date', 'user_id'),  # Composite index for common queries
        db.Index('idx_availability_status_date', 'status', 'date'),  # For filtering by status and date
        db.Index('idx_availability_user_date_created', 'user_id', 'date', 'created_at'),  # For user queries with ordering
    )
    
    def to_dict(self):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'time_slot': self.time_slot,  # Keep for backward compatibility
            'time_start': self.time_start.strftime('%H:%M') if self.time_start else None,
            'time_end': self.time_end.strftime('%H:%M') if self.time_end else None,
            'is_all_day': self.is_all_day if self.is_all_day is not None else True,
            'status': self.status,
            'play_preference': self.play_preference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return result
    
    def __repr__(self):
        return f'<Availability {self.user_id} - {self.date} - {self.status}>'

class Feedback(db.Model):
    """Model for user feedback and comments."""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'content': self.content,
            'rating': self.rating,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Feedback {self.id} by User {self.user_id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
