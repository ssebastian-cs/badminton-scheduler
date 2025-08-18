"""
Unit tests for Availability model.
"""

import pytest
from datetime import date, time, timedelta
from app.models import Availability
from app import db


class TestAvailabilityModel:
    """Test cases for Availability model."""
    
    def test_availability_creation_valid(self, app_context, test_user):
        """Test valid availability creation."""
        future_date = date.today() + timedelta(days=1)
        availability = Availability(
            user_id=test_user.id,
            date=future_date,
            start_time=time(9, 0),
            end_time=time(11, 0)
        )
        
        assert availability.user_id == test_user.id
        assert availability.date == future_date
        assert availability.start_time == time(9, 0)
        assert availability.end_time == time(11, 0)
    
    def test_availability_date_validation_past(self, app_context, test_user):
        """Test past date validation."""
        past_date = date.today() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Date must be in the future"):
            Availability(
                user_id=test_user.id,
                date=past_date,
                start_time=time(9, 0),
                end_time=time(11, 0)
            )
    
    def test_availability_date_validation_today(self, app_context, test_user):
        """Test today's date validation."""
        today = date.today()
        
        with pytest.raises(ValueError, match="Date must be in the future"):
            Availability(
                user_id=test_user.id,
                date=today,
                start_time=time(9, 0),
                end_time=time(11, 0)
            )
    
    def test_availability_time_validation_invalid_range(self, app_context, test_user):
        """Test invalid time range validation."""
        future_date = date.today() + timedelta(days=1)
        
        # End time before start time
        with pytest.raises(ValueError, match="End time must be after start time"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(11, 0),
                end_time=time(9, 0)
            )
        
        # Same start and end time
        with pytest.raises(ValueError, match="End time must be after start time"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(10, 0),
                end_time=time(10, 0)
            )
    
    def test_availability_time_validation_reasonable_hours(self, app_context, test_user):
        """Test reasonable hours validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Start time too early
        with pytest.raises(ValueError, match="Start time must be between 6:00 AM and 11:00 PM"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(5, 0),
                end_time=time(7, 0)
            )
        
        # End time too late
        with pytest.raises(ValueError, match="End time must be between 6:00 AM and 11:59 PM"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(22, 0),
                end_time=time(23, 30)
            )
    
    def test_availability_duration_validation(self, app_context, test_user):
        """Test duration validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Duration too long (more than 8 hours)
        with pytest.raises(ValueError, match="Availability duration cannot exceed 8 hours"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(8, 0),
                end_time=time(17, 0)  # 9 hours
            )
        
        # Duration too short (less than 30 minutes)
        with pytest.raises(ValueError, match="Availability duration must be at least 30 minutes"):
            Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(10, 0),
                end_time=time(10, 15)  # 15 minutes
            )
    
    def test_availability_update_method(self, app_context, test_user):
        """Test availability update method."""
        future_date = date.today() + timedelta(days=1)
        availability = Availability(
            user_id=test_user.id,
            date=future_date,
            start_time=time(9, 0),
            end_time=time(11, 0)
        )
        
        new_date = date.today() + timedelta(days=2)
        availability.update(
            date=new_date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        
        assert availability.date == new_date
        assert availability.start_time == time(10, 0)
        assert availability.end_time == time(12, 0)
    
    def test_availability_representation(self, app_context, test_user):
        """Test availability string representation."""
        future_date = date.today() + timedelta(days=1)
        availability = Availability(
            user_id=test_user.id,
            date=future_date,
            start_time=time(9, 0),
            end_time=time(11, 0)
        )
        
        expected_str = f"{test_user.username} - {future_date} 09:00-11:00"
        assert str(availability) == expected_str