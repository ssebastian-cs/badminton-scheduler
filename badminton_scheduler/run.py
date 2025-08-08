#!/usr/bin/env python3
"""
Simple Flask application runner for the badminton scheduler.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-development-only')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///badminton_scheduler.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
CORS(app, supports_credentials=True)

# Models
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time_slot = db.Column(db.String(50), nullable=True)  # Legacy field for backward compatibility
    time_start = db.Column(db.Time, nullable=True)  # Start time for availability
    time_end = db.Column(db.Time, nullable=True)    # End time for availability
    is_all_day = db.Column(db.Boolean, default=True)  # Flag for all-day availability
    status = db.Column(db.Enum('available', 'tentative', 'not_available', name='availability_status'), 
                      nullable=False, default='available')
    play_preference = db.Column(db.Enum('drop_in', 'book_court', 'either', name='play_preference'), 
                               nullable=True, default='either')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Updated unique constraint to allow multiple time slots per date
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', 'time_start', 'time_end', name='unique_availability_time'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'date': self.date.isoformat() if self.date else None,
            'time_slot': self.time_slot,  # Legacy field
            'time_start': self.time_start.strftime('%H:%M') if self.time_start else None,
            'time_end': self.time_end.strftime('%H:%M') if self.time_end else None,
            'is_all_day': self.is_all_day,
            'status': self.status,
            'play_preference': self.play_preference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
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

# Utility decorators
def admin_required(f):
    """Decorator to ensure the user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    # Validate input
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Log in a user."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/auth/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/auth/me')
@login_required
def get_current_user():
    """Get the current user's profile."""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'is_admin': current_user.is_admin,
        'created_at': current_user.created_at.isoformat()
    })

# API Routes
@app.route('/api/availability', methods=['GET'])
@login_required
def get_availability():
    """Get availability for a specific date range."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    
    query = Availability.query
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Availability.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Availability.date <= end_date)
    
    if user_id:
        if not current_user.is_admin and user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        query = query.filter_by(user_id=user_id)
    elif not current_user.is_admin:
        # Non-admin users can only see their own availability by default
        query = query.filter_by(user_id=current_user.id)
    
    availability = query.order_by(Availability.date).all()
    return jsonify([avail.to_dict() for avail in availability])

@app.route('/api/availability', methods=['POST'])
@login_required
def set_availability():
    """Set or update availability."""
    data = request.get_json()
    
    if not data or 'date' not in data or 'status' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        avail_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Check if the date is in the past
    if avail_date < date.today():
        return jsonify({'error': 'Cannot set availability for past dates'}), 400
    
    # Find existing availability or create a new one
    availability = Availability.query.filter_by(
        user_id=current_user.id,
        date=avail_date,
        time_slot=data.get('time_slot')
    ).first()
    
    if not availability:
        availability = Availability(
            user_id=current_user.id,
            date=avail_date,
            time_slot=data.get('time_slot')
        )
        db.session.add(availability)
    
    # Update fields
    availability.status = data['status']
    if 'play_preference' in data:
        availability.play_preference = data['play_preference']
    if 'notes' in data:
        availability.notes = data['notes']
    
    db.session.commit()
    
    return jsonify(availability.to_dict()), 200

@app.route('/api/availability/<int:availability_id>', methods=['PUT'])
@login_required
def update_availability(availability_id):
    """Update an existing availability entry."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Find the availability entry
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({'error': 'Availability entry not found'}), 404
    
    # Check user ownership (users can only edit their own entries, admins can edit any)
    if not current_user.is_admin and availability.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized: You can only edit your own availability entries'}), 403
    
    # Check if the date is in the past (prevent editing historical entries)
    if availability.date < date.today():
        return jsonify({'error': 'Cannot edit availability for past dates'}), 400
    
    # Handle date updates
    if 'date' in data:
        try:
            new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            # Check if the new date is in the past
            if new_date < date.today():
                return jsonify({'error': 'Cannot set availability for past dates'}), 400
            availability.date = new_date
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Handle time updates
    if 'time_start' in data:
        if data['time_start']:
            try:
                time_parts = data['time_start'].split(':')
                availability.time_start = time(int(time_parts[0]), int(time_parts[1]))
                availability.is_all_day = False
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid time_start format. Use HH:MM'}), 400
        else:
            availability.time_start = None
    
    if 'time_end' in data:
        if data['time_end']:
            try:
                time_parts = data['time_end'].split(':')
                availability.time_end = time(int(time_parts[0]), int(time_parts[1]))
                availability.is_all_day = False
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid time_end format. Use HH:MM'}), 400
        else:
            availability.time_end = None
    
    # Handle is_all_day flag
    if 'is_all_day' in data:
        availability.is_all_day = bool(data['is_all_day'])
        if availability.is_all_day:
            availability.time_start = None
            availability.time_end = None
    
    # Validate time logic
    if availability.time_start and availability.time_end:
        if availability.time_end <= availability.time_start:
            return jsonify({'error': 'End time must be after start time'}), 400
    
    # Handle legacy time_slot field for backward compatibility
    if 'time_slot' in data:
        availability.time_slot = data['time_slot']
        if data['time_slot']:
            availability.is_all_day = False
        else:
            availability.is_all_day = True
    
    # Update other fields
    if 'status' in data:
        if data['status'] not in ['available', 'tentative', 'not_available']:
            return jsonify({'error': 'Invalid status. Must be one of: available, tentative, not_available'}), 400
        availability.status = data['status']
    
    if 'play_preference' in data:
        if data['play_preference'] and data['play_preference'] not in ['drop_in', 'book_court', 'either']:
            return jsonify({'error': 'Invalid play preference. Must be one of: drop_in, book_court, either'}), 400
        availability.play_preference = data['play_preference']
    
    if 'notes' in data:
        availability.notes = data['notes']
    
    # Update the updated_at timestamp
    availability.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Availability updated successfully',
            'availability': availability.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update availability'}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Get feedback entries."""
    is_public = request.args.get('public', 'true').lower() == 'true'
    user_id = request.args.get('user_id', type=int)
    
    query = Feedback.query
    
    if is_public:
        query = query.filter_by(is_public=True)
    
    if user_id:
        if not current_user.is_authenticated or (not current_user.is_admin and current_user.id != user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        query = query.filter_by(user_id=user_id)
    
    feedback = query.order_by(Feedback.created_at.desc()).all()
    return jsonify([fb.to_dict() for fb in feedback])

@app.route('/api/feedback', methods=['POST'])
@login_required
def create_feedback():
    """Create a new feedback entry."""
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    
    feedback = Feedback(
        user_id=current_user.id,
        content=data['content'],
        rating=data.get('rating'),
        is_public=data.get('is_public', True)
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify(feedback.to_dict()), 201

# Admin Routes
@app.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users (admin only)."""
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat()
    } for user in users])

@app.route('/api/admin/availability/filtered', methods=['GET'])
@login_required
@admin_required
def get_filtered_availability():
    """Get filtered availability data for admin users with date range filtering and pagination."""
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Default 50 items per page
    
    # Validate pagination parameters
    if page < 1:
        return jsonify({'error': 'Page number must be positive'}), 400
    if per_page < 1 or per_page > 1000:  # Limit max per_page to prevent abuse
        return jsonify({'error': 'Per page must be between 1 and 1000'}), 400
    
    # Build base query with user information
    query = Availability.query.join(User)
    
    # Apply date filters
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Availability.date >= start_date_obj)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Availability.date <= end_date_obj)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Validate date range logic
    if start_date and end_date:
        if start_date_obj > end_date_obj:
            return jsonify({'error': 'Start date must be before or equal to end date'}), 400
    
    # Order by date and username for consistent results
    query = query.order_by(Availability.date.desc(), User.username)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    paginated_query = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Check if page exists
    if page > paginated_query.pages and paginated_query.pages > 0:
        return jsonify({'error': f'Page {page} does not exist. Total pages: {paginated_query.pages}'}), 404
    
    availability_list = paginated_query.items
    
    # Build enhanced response with user details
    enhanced_availability = []
    for avail in availability_list:
        avail_dict = avail.to_dict()
        
        # Add user information (already included in to_dict but ensure it's there)
        avail_dict['user_email'] = avail.user.email
        
        enhanced_availability.append(avail_dict)
    
    # Prepare response with pagination metadata
    response_data = {
        'availability': enhanced_availability,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': paginated_query.pages,
            'has_next': paginated_query.has_next,
            'has_prev': paginated_query.has_prev,
            'next_page': paginated_query.next_num if paginated_query.has_next else None,
            'prev_page': paginated_query.prev_num if paginated_query.has_prev else None
        },
        'filters': {
            'start_date': start_date,
            'end_date': end_date
        },
        'result_count': len(enhanced_availability)
    }
    
    return jsonify(response_data)

# Basic routes
@app.route('/')
def index():
    return jsonify({
        'message': 'Badminton Scheduler API',
        'version': '1.0.0',
        'frontend': '/static_frontend.html',
        'endpoints': {
            'auth': '/auth/login, /auth/register, /auth/logout, /auth/me',
            'api': '/api/availability, /api/feedback',
            'admin': '/api/admin/users'
        }
    })

@app.route('/static_frontend.html')
def frontend():
    """Serve the static frontend."""
    try:
        with open('static_frontend.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Frontend not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Database migration functions
def migrate_existing_availability_data():
    """Migrate existing availability data to support time-specific fields."""
    try:
        # Check if the new columns exist by trying to query them
        try:
            # Test if new columns exist
            db.session.execute(db.text("SELECT time_start, time_end, is_all_day, updated_at FROM availability LIMIT 1"))
            print("Time-specific columns already exist.")
        except Exception:
            # Columns don't exist, need to add them
            print("Adding new time-specific columns to availability table...")
            
            # Add new columns with default values
            db.session.execute(db.text("ALTER TABLE availability ADD COLUMN time_start TIME"))
            db.session.execute(db.text("ALTER TABLE availability ADD COLUMN time_end TIME"))
            db.session.execute(db.text("ALTER TABLE availability ADD COLUMN is_all_day BOOLEAN DEFAULT 1"))
            db.session.execute(db.text("ALTER TABLE availability ADD COLUMN updated_at DATETIME"))
            
            # Update existing entries to have is_all_day = True and set updated_at
            db.session.execute(db.text("""
                UPDATE availability 
                SET is_all_day = 1, updated_at = created_at 
                WHERE is_all_day IS NULL OR updated_at IS NULL
            """))
            
            db.session.commit()
            print("Migration completed successfully!")
            
        # Check if the new unique index exists
        try:
            result = db.session.execute(db.text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_availability_time_unique'
            """)).fetchone()
            
            if not result:
                print("Creating unique index for time-specific availability...")
                # Create a unique index that allows multiple time slots per date
                db.session.execute(db.text("""
                    CREATE UNIQUE INDEX idx_availability_time_unique 
                    ON availability(user_id, date, time_start, time_end)
                    WHERE time_start IS NOT NULL AND time_end IS NOT NULL
                """))
                
                # Create another unique index for all-day entries
                db.session.execute(db.text("""
                    CREATE UNIQUE INDEX idx_availability_allday_unique 
                    ON availability(user_id, date)
                    WHERE is_all_day = 1
                """))
                
                db.session.commit()
                print("Unique indexes created successfully!")
            else:
                print("Unique indexes already exist.")
                
        except Exception as e:
            print(f"Index creation error (may be expected): {e}")
            
        # Now check if there are any entries that need data migration
        result = db.session.execute(db.text("SELECT COUNT(*) FROM availability WHERE is_all_day IS NULL")).fetchone()
        if result and result[0] > 0:
            print(f"Updating {result[0]} entries with default values...")
            db.session.execute(db.text("""
                UPDATE availability 
                SET is_all_day = 1, updated_at = COALESCE(updated_at, created_at)
                WHERE is_all_day IS NULL
            """))
            db.session.commit()
            print("Data migration completed!")
            
    except Exception as e:
        print(f"Migration error: {e}")
        db.session.rollback()
        raise

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        
        # Run migration for existing data
        migrate_existing_availability_data()
    
    print("Starting Badminton Scheduler API server...")
    print("Available at: http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    app.run(debug=True, port=5000, host='0.0.0.0')