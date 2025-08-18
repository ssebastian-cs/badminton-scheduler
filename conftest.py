"""
Pytest configuration and fixtures for the badminton scheduler application.
"""

import pytest
import tempfile
import os
from datetime import date, time, datetime, timedelta
from app import create_app, db
from app.models import User, Availability, Comment, AdminAction


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app):
    """Create request context."""
    with app.test_request_context():
        yield app


@pytest.fixture
def db_session(app_context):
    """Create database session for testing."""
    with app_context.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.session.close()
        db.drop_all()


class TestDataFactory:
    """Factory for creating test data."""
    
    _user_counter = 0
    
    @staticmethod
    def create_user(username=None, password="password123", role="User", is_active=True):
        """Create a test user."""
        if username is None:
            TestDataFactory._user_counter += 1
            username = f"testuser{TestDataFactory._user_counter}"
        
        user = User(username=username, password=password, role=role)
        user.is_active = is_active
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_admin_user(username="admin", password="admin123"):
        """Create a test admin user."""
        return TestDataFactory.create_user(username=username, password=password, role="Admin")
    
    @staticmethod
    def create_availability(user, date_offset=1, start_hour=10, end_hour=12):
        """Create a test availability entry."""
        availability_date = date.today() + timedelta(days=date_offset)
        start_time = time(start_hour, 0)
        end_time = time(end_hour, 0)
        
        availability = Availability(
            user_id=user.id,
            date=availability_date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(availability)
        db.session.commit()
        return availability
    
    @staticmethod
    def create_comment(user, content="Test comment"):
        """Create a test comment."""
        comment = Comment(user_id=user.id, content=content)
        db.session.add(comment)
        db.session.commit()
        return comment
    
    @staticmethod
    def create_admin_action(admin_user, action_type="create_user", target_type="user", 
                          target_id=1, description="Test action"):
        """Create a test admin action."""
        action = AdminAction(
            admin_user_id=admin_user.id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            description=description
        )
        db.session.add(action)
        db.session.commit()
        return action


@pytest.fixture
def test_factory():
    """Provide test data factory."""
    return TestDataFactory


@pytest.fixture
def test_user(db_session, test_factory):
    """Create a test user."""
    return test_factory.create_user()


@pytest.fixture
def test_admin(db_session, test_factory):
    """Create a test admin user."""
    return test_factory.create_admin_user()


@pytest.fixture
def test_availability(db_session, test_user, test_factory):
    """Create a test availability entry."""
    return test_factory.create_availability(test_user)


@pytest.fixture
def test_comment(db_session, test_user, test_factory):
    """Create a test comment."""
    return test_factory.create_comment(test_user)


@pytest.fixture
def authenticated_user(client, test_user):
    """Login a test user and return the client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def authenticated_admin(client, test_admin):
    """Login a test admin and return the client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_admin.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def multiple_users(db_session, test_factory):
    """Create multiple test users."""
    users = []
    for i in range(3):
        user = test_factory.create_user(
            username=f"user{i+1}",
            password=f"password{i+1}"
        )
        users.append(user)
    return users


@pytest.fixture
def multiple_availability_entries(db_session, multiple_users, test_factory):
    """Create multiple availability entries."""
    entries = []
    for i, user in enumerate(multiple_users):
        for j in range(2):
            entry = test_factory.create_availability(
                user=user,
                date_offset=i+j+1,
                start_hour=10+j,
                end_hour=12+j
            )
            entries.append(entry)
    return entries


@pytest.fixture
def multiple_comments(db_session, multiple_users, test_factory):
    """Create multiple comments."""
    comments = []
    for i, user in enumerate(multiple_users):
        comment = test_factory.create_comment(
            user=user,
            content=f"Test comment from user {i+1}"
        )
        comments.append(comment)
    return comments


@pytest.fixture(autouse=True)
def clean_database(app_context):
    """Ensure clean database state for each test."""
    with app_context.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Clear all tables before test
        try:
            db.session.query(Comment).delete()
            db.session.query(Availability).delete() 
            db.session.query(User).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Reset the user counter
        TestDataFactory._user_counter = 0
        
        yield
        
        # Clean up after test
        try:
            db.session.query(Comment).delete()
            db.session.query(Availability).delete()
            db.session.query(User).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()


@pytest.fixture
def isolated_test_data(clean_database, test_factory, app_context):
    """Create isolated test data for CRUD operations."""
    with app_context.app_context():
        # Create test user
        user = test_factory.create_user(username="cruduser", password="password123")
        
        # Create test availability
        availability = test_factory.create_availability(user, date_offset=1)
        
        # Create test comment
        comment = test_factory.create_comment(user, "Test comment for CRUD")
        
        return {
            'user': user,
            'availability': availability,
            'comment': comment
        }