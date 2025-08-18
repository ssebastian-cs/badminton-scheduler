from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy import and_, or_
from .. import db
from ..models import Availability, User
from ..forms import AvailabilityForm, AvailabilityFilterForm
from ..utils import (admin_required, safe_get_record, safe_create_record, 
                     safe_update_record, safe_delete_record, check_record_ownership,
                     get_date_range_filter, log_user_activity)
from ..error_handlers import ErrorHandler, FlashMessageHelper
from ..security import rate_limit_endpoint, log_security_event

availability_bp = Blueprint('availability', __name__)


@availability_bp.route('/')
@login_required
def dashboard():
    """Dashboard with today's availability by default."""
    try:
        # Get filter parameters
        view_type = request.args.get('view', 'today')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Calculate date range using utility function
        try:
            start_date, end_date = get_date_range_filter(view_type, start_date, end_date)
        except ValueError:
            FlashMessageHelper.error('Invalid date format. Using today\'s view.')
            view_type = 'today'
            start_date, end_date = get_date_range_filter('today')
        
        # Query availability entries with error handling
        try:
            query = Availability.query.join(User).filter(
                Availability.date >= start_date,
                Availability.date <= end_date,
                User.is_active == True
            ).order_by(Availability.date, Availability.start_time)
            
            availability_entries = query.all()
        except Exception as e:
            ErrorHandler.handle_database_error(e, "loading availability data")
            availability_entries = []
        
        # Group entries by date, then by user for better display
        entries_by_date = {}
        for entry in availability_entries:
            entry_date = entry.date
            if entry_date not in entries_by_date:
                entries_by_date[entry_date] = {}
            
            user_id = entry.user_id
            if user_id not in entries_by_date[entry_date]:
                entries_by_date[entry_date][user_id] = {
                    'user': entry.user,
                    'entries': []
                }
            entries_by_date[entry_date][user_id]['entries'].append(entry)
        
        # Create filter form
        filter_form = AvailabilityFilterForm()
        if view_type == 'custom':
            filter_form.start_date.data = start_date
            filter_form.end_date.data = end_date
        
        # Log user activity
        log_user_activity('viewed_dashboard', {'view_type': view_type})
        
        return render_template('dashboard.html', 
                             entries_by_date=entries_by_date,
                             view_type=view_type,
                             start_date=start_date,
                             end_date=end_date,
                             filter_form=filter_form)
    
    except Exception as e:
        ErrorHandler.handle_database_error(e, "loading dashboard")
        return redirect(url_for('auth.login'))


@availability_bp.route('/availability/add', methods=['GET', 'POST'])
@login_required
@rate_limit_endpoint(max_requests=10, window_minutes=10, per_user=True)
def add_availability():
    """Add new availability entry."""
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        try:
            availability = Availability(
                user_id=current_user.id,
                date=form.date.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            
            # Use safe database operation
            if safe_create_record(availability, "availability", "Availability added successfully!"):
                log_user_activity('added_availability', {
                    'date': str(form.date.data),
                    'start_time': str(form.start_time.data),
                    'end_time': str(form.end_time.data)
                })
                return redirect(url_for('availability.dashboard'))
                
        except ValueError as e:
            FlashMessageHelper.error(str(e))
        except Exception as e:
            ErrorHandler.handle_database_error(e, "adding availability")
    else:
        # Handle form validation errors
        if form.errors:
            ErrorHandler.handle_validation_error(form.errors, "availability form")
    
    return render_template('availability/add.html', form=form)


@availability_bp.route('/availability/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@rate_limit_endpoint(max_requests=10, window_minutes=10, per_user=True)
def edit_availability(id):
    """Edit availability entry."""
    # Safely get the availability record
    availability = safe_get_record(Availability, id, "availability entry")
    if not availability:
        return redirect(url_for('availability.dashboard'))
    
    # Check permissions using utility function
    if not check_record_ownership(availability):
        return ErrorHandler.handle_permission_error('edit this availability entry')
    
    form = AvailabilityForm(obj=availability)
    
    if form.validate_on_submit():
        try:
            availability.update(
                date=form.date.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            
            # Use safe database operation
            if safe_update_record(availability, "availability", "Availability updated successfully!"):
                log_user_activity('updated_availability', {
                    'availability_id': id,
                    'date': str(form.date.data),
                    'start_time': str(form.start_time.data),
                    'end_time': str(form.end_time.data)
                })
                return redirect(url_for('availability.dashboard'))
                
        except ValueError as e:
            FlashMessageHelper.error(str(e))
        except Exception as e:
            ErrorHandler.handle_database_error(e, "updating availability")
    else:
        # Handle form validation errors
        if form.errors:
            ErrorHandler.handle_validation_error(form.errors, "availability form")
    
    return render_template('availability/edit.html', form=form, availability=availability)


@availability_bp.route('/availability/delete/<int:id>', methods=['POST'])
@login_required
@rate_limit_endpoint(max_requests=5, window_minutes=10, per_user=True)
def delete_availability(id):
    """Delete availability entry."""
    # Safely get the availability record
    availability = safe_get_record(Availability, id, "availability entry")
    if not availability:
        return redirect(url_for('availability.dashboard'))
    
    # Check permissions using utility function
    if not check_record_ownership(availability):
        return ErrorHandler.handle_permission_error('delete this availability entry')
    
    # Use safe database operation
    if safe_delete_record(availability, "availability", "Availability deleted successfully!"):
        log_user_activity('deleted_availability', {
            'availability_id': id,
            'date': str(availability.date),
            'start_time': str(availability.start_time),
            'end_time': str(availability.end_time)
        })
    
    return redirect(url_for('availability.dashboard'))


@availability_bp.route('/availability/my')
@login_required
def my_availability():
    """View current user's availability entries."""
    try:
        entries = Availability.query.filter_by(user_id=current_user.id).filter(
            Availability.date >= date.today()
        ).order_by(Availability.date, Availability.start_time).all()
        
        # Log user activity
        log_user_activity('viewed_my_availability', {'entries_count': len(entries)})
        
        return render_template('availability/my_availability.html', entries=entries)
    
    except Exception as e:
        ErrorHandler.handle_database_error(e, "loading your availability entries")
        return redirect(url_for('availability.dashboard'))


@availability_bp.route('/availability')
@login_required
def availability_dashboard():
    """Dedicated availability dashboard route for admins and users."""
    return dashboard()