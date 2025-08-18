"""
Unit tests for AvailabilityForm.
"""

import pytest
from datetime import date, time, timedelta
from app.forms import AvailabilityForm


class TestAvailabilityForm:
    """Test cases for AvailabilityForm."""
    
    def test_valid_availability_form(self, app_context):
        """Test valid availability form data."""
        future_date = date.today() + timedelta(days=1)
        form_data = {
            'date': future_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is True
    
    def test_availability_form_future_date_validation(self, app_context):
        """Test future date validation."""
        # Past date
        past_date = date.today() - timedelta(days=1)
        form_data = {
            'date': past_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date must be in the future' in form.date.errors
        
        # Today's date
        today = date.today()
        form_data['date'] = today
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date must be in the future' in form.date.errors
    
    def test_availability_form_date_range_validation(self, app_context):
        """Test date range validation (not too far in future)."""
        # More than one year in future
        far_future_date = date.today() + timedelta(days=366)
        form_data = {
            'date': far_future_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date cannot be more than one year in the future' in form.date.errors
    
    def test_availability_form_time_validation(self, app_context):
        """Test time validation."""
        future_date = date.today() + timedelta(days=1)
        
        # End time before start time
        form_data = {
            'date': future_date,
            'start_time': time(12, 0),
            'end_time': time(10, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be after start time' in form.end_time.errors
        
        # Same start and end time
        form_data['end_time'] = time(12, 0)
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be after start time' in form.end_time.errors
    
    def test_availability_form_time_range_validation(self, app_context):
        """Test reasonable time range validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Start time too early
        form_data = {
            'date': future_date,
            'start_time': time(5, 0),
            'end_time': time(7, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Start time must be between 6:00 AM and 11:00 PM' in form.start_time.errors
        
        # End time too late
        form_data = {
            'date': future_date,
            'start_time': time(22, 0),
            'end_time': time(23, 30),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be between 6:00 AM and 11:59 PM' in form.end_time.errors
    
    def test_availability_form_duration_validation(self, app_context):
        """Test duration validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Duration too long (more than 8 hours)
        form_data = {
            'date': future_date,
            'start_time': time(8, 0),
            'end_time': time(17, 0),  # 9 hours
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Availability duration cannot exceed 8 hours' in form.end_time.errors
        
        # Duration too short (less than 30 minutes)
        form_data = {
            'date': future_date,
            'start_time': time(10, 0),
            'end_time': time(10, 15),  # 15 minutes
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Availability duration must be at least 30 minutes' in form.end_time.errors