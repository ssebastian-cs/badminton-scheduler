from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, time
import re
from models import db, Availability, Feedback, User
from utils import admin_required

# Create API blueprint
api_bp = Blueprint('api', __name__)

def parse_time_string(time_str):
    """Parse various time formats and return a time object with comprehensive validation."""
    if not time_str:
        return None
    
    # Input sanitization
    if not isinstance(time_str, str):
        raise ValueError("Time input must be a string")
    
    time_str = time_str.strip().upper()
    
    # Check for empty or whitespace-only strings
    if not time_str:
        return None
    
    # Check for obviously malformed inputs
    if len(time_str) > 20:  # Reasonable maximum length
        raise ValueError("Time format too long - expected formats like '7:00 PM', '19:00', or '7PM'")
    
    # Handle common time formats with comprehensive validation
    time_patterns = [
        # 24-hour format: "19:00", "7:30", "07:30"
        (r'^(\d{1,2}):(\d{2})$', lambda m: _validate_and_create_time(
            int(m.group(1)), int(m.group(2)), 0, "24-hour format (HH:MM)"
        )),
        # 12-hour format with minutes: "7:00 PM", "7:30 AM", "12:15 PM"
        (r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', lambda m: _validate_and_create_12h_time(
            int(m.group(1)), int(m.group(2)), m.group(3), "12-hour format with minutes (H:MM AM/PM)"
        )),
        # 12-hour format without minutes: "7PM", "7 AM", "12 PM"
        (r'^(\d{1,2})\s*(AM|PM)$', lambda m: _validate_and_create_12h_time(
            int(m.group(1)), 0, m.group(2), "12-hour format without minutes (H AM/PM)"
        )),
        # 24-hour format with seconds (less common but supported): "19:00:00"
        (r'^(\d{1,2}):(\d{2}):(\d{2})$', lambda m: _validate_and_create_time(
            int(m.group(1)), int(m.group(2)), int(m.group(3)), "24-hour format with seconds (HH:MM:SS)"
        )),
    ]
    
    for pattern, converter in time_patterns:
        match = re.match(pattern, time_str)
        if match:
            try:
                return converter(match)
            except ValueError as e:
                # Re-raise with more context
                raise ValueError(f"Invalid time '{time_str}': {str(e)}")
    
    # If no pattern matches, provide helpful error message
    raise ValueError(
        f"Invalid time format '{time_str}'. "
        f"Supported formats: '7:00 PM', '19:00', '7PM', '7:30 AM', '19:30', etc."
    )

def _validate_and_create_time(hour, minute, second, format_desc):
    """Helper function to validate time components and create time object."""
    # Validate hour
    if hour < 0 or hour > 23:
        raise ValueError(f"Hour must be between 0-23 for {format_desc}, got {hour}")
    
    # Validate minute
    if minute < 0 or minute > 59:
        raise ValueError(f"Minutes must be between 0-59, got {minute}")
    
    # Validate second
    if second < 0 or second > 59:
        raise ValueError(f"Seconds must be between 0-59, got {second}")
    
    return time(hour, minute, second)

def _validate_and_create_12h_time(hour_12, minute, period, format_desc):
    """Helper function to validate 12-hour time and convert to 24-hour."""
    # Validate 12-hour format hour
    if hour_12 < 1 or hour_12 > 12:
        raise ValueError(f"Hour must be between 1-12 for {format_desc}, got {hour_12}")
    
    # Validate minute
    if minute < 0 or minute > 59:
        raise ValueError(f"Minutes must be between 0-59, got {minute}")
    
    # Convert to 24-hour format
    if period == 'AM':
        hour_24 = 0 if hour_12 == 12 else hour_12
    else:  # PM
        hour_24 = 12 if hour_12 == 12 else hour_12 + 12
    
    return time(hour_24, minute, 0)

def parse_time_range(time_range_str):
    """Parse time range strings with comprehensive validation and error handling."""
    if not time_range_str:
        return None, None
    
    # Input sanitization
    if not isinstance(time_range_str, str):
        raise ValueError("Time range input must be a string")
    
    time_range_str = time_range_str.strip().upper()
    
    # Check for empty or whitespace-only strings
    if not time_range_str:
        return None, None
    
    # Check for obviously malformed inputs
    if len(time_range_str) > 50:  # Reasonable maximum length
        raise ValueError("Time range format too long - expected formats like '7-9 PM', '19:00-21:00', or '7:00 PM - 9:00 PM'")
    
    # Check if there's actually a range separator
    if '-' not in time_range_str:
        raise ValueError("Time range must contain a dash (-) separator")
    
    # Count dashes to detect malformed ranges
    dash_count = time_range_str.count('-')
    if dash_count > 1:
        raise ValueError("Time range should contain only one dash (-) separator")
    
    try:
        # Try specific range patterns with comprehensive validation
        
        # Pattern 1: "7-9 PM", "7-9AM" (same period for both times)
        match = re.match(r'^(\d{1,2})-(\d{1,2})\s*(AM|PM)$', time_range_str)
        if match:
            start_hour = int(match.group(1))
            end_hour = int(match.group(2))
            period = match.group(3)
            
            # Validate hours for 12-hour format
            if start_hour < 1 or start_hour > 12:
                raise ValueError(f"Start hour must be between 1-12 for 12-hour format, got {start_hour}")
            if end_hour < 1 or end_hour > 12:
                raise ValueError(f"End hour must be between 1-12 for 12-hour format, got {end_hour}")
            
            # Convert to 24-hour format
            if period == 'AM':
                start_hour_24 = 0 if start_hour == 12 else start_hour
                end_hour_24 = 0 if end_hour == 12 else end_hour
            else:  # PM
                start_hour_24 = 12 if start_hour == 12 else start_hour + 12
                end_hour_24 = 12 if end_hour == 12 else end_hour + 12
            
            start_time = time(start_hour_24, 0)
            end_time = time(end_hour_24, 0)
            
            # Validate logical order
            if end_time <= start_time:
                raise ValueError(f"End time ({end_hour} {period}) must be after start time ({start_hour} {period})")
            
            return start_time, end_time
        
        # Pattern 2: "19:00-21:00", "7:30-9:45" (24-hour format)
        match = re.match(r'^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$', time_range_str)
        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2))
            end_hour = int(match.group(3))
            end_minute = int(match.group(4))
            
            # Validate components
            start_time = _validate_and_create_time(start_hour, start_minute, 0, "24-hour range start")
            end_time = _validate_and_create_time(end_hour, end_minute, 0, "24-hour range end")
            
            # Validate logical order
            if end_time <= start_time:
                raise ValueError(f"End time ({end_hour:02d}:{end_minute:02d}) must be after start time ({start_hour:02d}:{start_minute:02d})")
            
            return start_time, end_time
        
        # Pattern 3: General range split "7:00 PM - 9:00 PM", "7 PM - 9 PM"
        match = re.match(r'^(.+?)\s*-\s*(.+)$', time_range_str)
        if match:
            start_str = match.group(1).strip()
            end_str = match.group(2).strip()
            
            # Validate that both parts are non-empty
            if not start_str:
                raise ValueError("Start time cannot be empty in time range")
            if not end_str:
                raise ValueError("End time cannot be empty in time range")
            
            try:
                start_time = parse_time_string(start_str)
                end_time = parse_time_string(end_str)
                
                if start_time is None or end_time is None:
                    raise ValueError("Both start and end times must be specified in a time range")
                
                # Validate logical order
                if end_time <= start_time:
                    raise ValueError(f"End time ({end_str}) must be after start time ({start_str})")
                
                return start_time, end_time
                
            except ValueError as e:
                # Re-raise with more context about which part failed
                if "start time" in str(e).lower() or start_str in str(e):
                    raise ValueError(f"Invalid start time in range '{start_str}': {str(e)}")
                elif "end time" in str(e).lower() or end_str in str(e):
                    raise ValueError(f"Invalid end time in range '{end_str}': {str(e)}")
                else:
                    raise ValueError(f"Invalid time range '{time_range_str}': {str(e)}")
    
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        # Catch any unexpected errors and provide helpful message
        raise ValueError(f"Unexpected error parsing time range '{time_range_str}': {str(e)}")
    
    # If no pattern matches, provide helpful error message
    raise ValueError(
        f"Invalid time range format '{time_range_str}'. "
        f"Supported formats: '7-9 PM', '19:00-21:00', '7:00 PM - 9:00 PM', etc."
    )

def validate_time_logic(start_time, end_time):
    """Comprehensive validation of time logic and constraints."""
    if not start_time and not end_time:
        return True  # All-day availability is valid
    
    # If only one time is provided, that's valid (e.g., "from 7 PM" or "until 9 PM")
    if start_time and not end_time:
        # Validate start time is reasonable (not in the past for today's date, etc.)
        return True
    
    if end_time and not start_time:
        # Validate end time is reasonable
        return True
    
    # Both times provided - validate logical relationship
    if start_time and end_time:
        if end_time <= start_time:
            # Format times for user-friendly error message
            start_str = start_time.strftime('%I:%M %p').lstrip('0')
            end_str = end_time.strftime('%I:%M %p').lstrip('0')
            raise ValueError(f"End time ({end_str}) must be after start time ({start_str})")
        
        # Check for reasonable time spans (not more than 24 hours)
        time_diff = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
        if time_diff.total_seconds() > 24 * 3600:  # More than 24 hours
            raise ValueError("Time span cannot exceed 24 hours")
        
        # Check for very short time spans (less than 15 minutes) - warning but not error
        if time_diff.total_seconds() < 15 * 60:  # Less than 15 minutes
            # This could be a warning in the future, but for now we'll allow it
            pass
    
    return True

def validate_date_input(date_str, field_name="date"):
    """Validate date input with comprehensive error checking."""
    if not date_str:
        raise ValueError(f"{field_name.capitalize()} is required")
    
    if not isinstance(date_str, str):
        raise ValueError(f"{field_name.capitalize()} must be a string in YYYY-MM-DD format")
    
    # Check basic format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise ValueError(f"Invalid {field_name} format. Use YYYY-MM-DD (e.g., 2025-08-15)")
    
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid {field_name} '{date_str}'. Use YYYY-MM-DD format with valid date values")
    
    # Check for reasonable date ranges
    min_date = date(2020, 1, 1)  # Reasonable minimum date
    max_date = date(2030, 12, 31)  # Reasonable maximum date
    
    if parsed_date < min_date:
        raise ValueError(f"{field_name.capitalize()} cannot be before {min_date.isoformat()}")
    
    if parsed_date > max_date:
        raise ValueError(f"{field_name.capitalize()} cannot be after {max_date.isoformat()}")
    
    return parsed_date

def validate_availability_status(status):
    """Validate availability status with comprehensive checking."""
    if not status:
        raise ValueError("Status is required")
    
    if not isinstance(status, str):
        raise ValueError("Status must be a string")
    
    valid_statuses = ['available', 'tentative', 'not_available']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
    
    return status

def validate_play_preference(preference):
    """Validate play preference with comprehensive checking."""
    if preference is None or preference == '':
        return None  # Optional field
    
    if not isinstance(preference, str):
        raise ValueError("Play preference must be a string")
    
    valid_preferences = ['drop_in', 'book_court', 'either']
    if preference not in valid_preferences:
        raise ValueError(f"Invalid play preference '{preference}'. Must be one of: {', '.join(valid_preferences)}")
    
    return preference

def validate_notes(notes):
    """Validate notes field with length and content checking."""
    if notes is None or notes == '':
        return None  # Optional field
    
    if not isinstance(notes, str):
        raise ValueError("Notes must be a string")
    
    # Check length limits
    if len(notes) > 1000:  # Reasonable limit
        raise ValueError("Notes cannot exceed 1000 characters")
    
    # Basic content validation (no malicious content)
    if '<script' in notes.lower() or 'javascript:' in notes.lower():
        raise ValueError("Notes contain invalid content")
    
    return notes.strip()

def create_validation_error_response(error_msg, field=None):
    """Create a standardized error response for validation failures."""
    response_data = {
        'error': error_msg,
        'error_type': 'validation_error'
    }
    
    if field:
        response_data['field'] = field
    
    return jsonify(response_data), 400

def format_time_slot(start_time, end_time, is_all_day=False):
    """Format time information into a time_slot string for storage."""
    if is_all_day or (not start_time and not end_time):
        return None  # All day availability
    
    if start_time and end_time:
        return f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
    elif start_time:
        return f"{start_time.strftime('%H:%M')}"
    elif end_time:
        return f"until {end_time.strftime('%H:%M')}"
    
    return None

# Availability Routes
@api_bp.route('/availability', methods=['GET'])
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
    
    # Enhance response with parsed time information
    enhanced_availability = []
    for avail in availability:
        avail_dict = avail.to_dict()
        
        # Parse time_slot to extract time information
        if avail.time_slot:
            try:
                if '-' in avail.time_slot and not avail.time_slot.startswith('until'):
                    # Parse time range
                    start_time, end_time = parse_time_range(avail.time_slot)
                    avail_dict.update({
                        'time_start': start_time.strftime('%H:%M') if start_time else None,
                        'time_end': end_time.strftime('%H:%M') if end_time else None,
                        'is_all_day': False
                    })
                elif avail.time_slot.startswith('until'):
                    # Parse "until" format
                    time_str = avail.time_slot.replace('until ', '')
                    end_time = parse_time_string(time_str)
                    avail_dict.update({
                        'time_start': None,
                        'time_end': end_time.strftime('%H:%M') if end_time else None,
                        'is_all_day': False
                    })
                else:
                    # Single time
                    start_time = parse_time_string(avail.time_slot)
                    avail_dict.update({
                        'time_start': start_time.strftime('%H:%M') if start_time else None,
                        'time_end': None,
                        'is_all_day': False
                    })
            except ValueError:
                # If parsing fails, treat as legacy format
                avail_dict.update({
                    'time_start': None,
                    'time_end': None,
                    'is_all_day': False,
                    'legacy_time_slot': avail.time_slot
                })
        else:
            # All-day availability
            avail_dict.update({
                'time_start': None,
                'time_end': None,
                'is_all_day': True
            })
        
        enhanced_availability.append(avail_dict)
    
    return jsonify(enhanced_availability)

@api_bp.route('/availability', methods=['POST'])
@login_required
def set_availability():
    """Set or update availability with comprehensive validation."""
    # Validate request data exists
    if not request.is_json:
        return create_validation_error_response("Request must contain JSON data")
    
    data = request.get_json()
    if not data:
        return create_validation_error_response("Request body cannot be empty")
    
    # Validate required fields
    if 'date' not in data:
        return create_validation_error_response("Date is required", 'date')
    
    if 'status' not in data:
        return create_validation_error_response("Status is required", 'status')
    
    try:
        # Validate date
        avail_date = validate_date_input(data['date'], 'date')
        
        # Check if the date is in the past
        if avail_date < date.today():
            return create_validation_error_response("Cannot set availability for past dates", 'date')
        
        # Validate status
        status = validate_availability_status(data['status'])
        
        # Validate play preference
        play_preference = validate_play_preference(data.get('play_preference'))
        
        # Validate notes
        notes = validate_notes(data.get('notes'))
        
    except ValueError as e:
        return create_validation_error_response(str(e))
    
    # Parse and validate time information with comprehensive error handling
    start_time = None
    end_time = None
    is_all_day = data.get('is_all_day', True)
    time_slot = None
    
    try:
        # Validate is_all_day field
        if 'is_all_day' in data:
            if not isinstance(data['is_all_day'], bool):
                return create_validation_error_response("is_all_day must be true or false", 'is_all_day')
            is_all_day = data['is_all_day']
        
        # Handle different time input formats with validation
        if not is_all_day:
            # Check for time range in a single field
            if 'time_range' in data and data['time_range']:
                if not isinstance(data['time_range'], str):
                    return create_validation_error_response("time_range must be a string", 'time_range')
                
                try:
                    start_time, end_time = parse_time_range(data['time_range'])
                except ValueError as e:
                    return create_validation_error_response(f"Invalid time range: {str(e)}", 'time_range')
            else:
                # Check for separate start and end time fields
                if 'time_start' in data and data['time_start']:
                    if not isinstance(data['time_start'], str):
                        return create_validation_error_response("time_start must be a string", 'time_start')
                    
                    try:
                        start_time = parse_time_string(data['time_start'])
                    except ValueError as e:
                        return create_validation_error_response(f"Invalid start time: {str(e)}", 'time_start')
                
                if 'time_end' in data and data['time_end']:
                    if not isinstance(data['time_end'], str):
                        return create_validation_error_response("time_end must be a string", 'time_end')
                    
                    try:
                        end_time = parse_time_string(data['time_end'])
                    except ValueError as e:
                        return create_validation_error_response(f"Invalid end time: {str(e)}", 'time_end')
            
            # Validate time logic
            try:
                validate_time_logic(start_time, end_time)
            except ValueError as e:
                return create_validation_error_response(str(e), 'time_logic')
            
            # Format time slot for storage
            if start_time or end_time:
                is_all_day = False
                time_slot = format_time_slot(start_time, end_time, is_all_day)
        
        # Handle legacy time_slot field for backward compatibility
        if 'time_slot' in data and data['time_slot'] and not time_slot:
            if not isinstance(data['time_slot'], str):
                return create_validation_error_response("time_slot must be a string", 'time_slot')
            
            try:
                # Try to parse legacy time_slot as a range
                start_time, end_time = parse_time_range(data['time_slot'])
                time_slot = format_time_slot(start_time, end_time, False)
                is_all_day = False
            except ValueError:
                # If parsing fails, validate it's not obviously malformed
                if len(data['time_slot'].strip()) > 50:
                    return create_validation_error_response("time_slot is too long", 'time_slot')
                
                # Use as-is for backward compatibility but sanitize
                time_slot = data['time_slot'].strip()
                is_all_day = False
    
    except Exception as e:
        # Catch any unexpected errors in time processing
        return create_validation_error_response(f"Error processing time information: {str(e)}")
    
    # Find existing availability or create a new one
    availability = Availability.query.filter_by(
        user_id=current_user.id,
        date=avail_date,
        time_slot=time_slot
    ).first()
    
    if not availability:
        availability = Availability(
            user_id=current_user.id,
            date=avail_date,
            time_slot=time_slot
        )
        db.session.add(availability)
    
    # Update fields with validated data
    availability.status = status
    if play_preference is not None:
        availability.play_preference = play_preference
    if notes is not None:
        availability.notes = notes
    
    try:
        db.session.commit()
        
        # Return enhanced response with parsed time information
        response_data = availability.to_dict()
        if not is_all_day and (start_time or end_time):
            response_data.update({
                'time_start': start_time.strftime('%H:%M') if start_time else None,
                'time_end': end_time.strftime('%H:%M') if end_time else None,
                'is_all_day': False
            })
        else:
            response_data.update({
                'time_start': None,
                'time_end': None,
                'is_all_day': True
            })
        
        return jsonify({
            'message': 'Availability set successfully',
            'availability': response_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        # Log the actual error for debugging but don't expose internal details
        app.logger.error(f"Database error in set_availability: {str(e)}")
        return jsonify({
            'error': 'Failed to save availability. Please try again.',
            'error_type': 'database_error'
        }), 500

@api_bp.route('/availability/<int:availability_id>', methods=['PUT'])
@login_required
def update_availability(availability_id):
    """Update an existing availability entry with comprehensive validation."""
    # Validate request data
    if not request.is_json:
        return create_validation_error_response("Request must contain JSON data")
    
    data = request.get_json()
    if not data:
        return create_validation_error_response("Request body cannot be empty")
    
    # Validate availability_id
    if availability_id <= 0:
        return create_validation_error_response("Invalid availability ID")
    
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
    
    # Parse and validate time information if provided
    start_time = None
    end_time = None
    is_all_day = data.get('is_all_day', True)
    time_slot = availability.time_slot  # Keep existing time_slot if not updating
    
    try:
        # Handle different time input formats
        if not is_all_day:
            # Check for time range in a single field
            if 'time_range' in data and data['time_range']:
                start_time, end_time = parse_time_range(data['time_range'])
                time_slot = format_time_slot(start_time, end_time, is_all_day)
            else:
                # Check for separate start and end time fields
                if 'time_start' in data:
                    if data['time_start']:
                        start_time = parse_time_string(data['time_start'])
                    else:
                        start_time = None
                if 'time_end' in data:
                    if data['time_end']:
                        end_time = parse_time_string(data['time_end'])
                    else:
                        end_time = None
                
                # Only update time_slot if time fields were provided
                if 'time_start' in data or 'time_end' in data:
                    time_slot = format_time_slot(start_time, end_time, is_all_day)
            
            # Validate time logic
            if start_time or end_time:
                validate_time_logic(start_time, end_time)
                is_all_day = False
        else:
            # All-day availability
            time_slot = None
        
        # Handle legacy time_slot field for backward compatibility
        if 'time_slot' in data:
            if data['time_slot']:
                try:
                    # Try to parse legacy time_slot as a range
                    start_time, end_time = parse_time_range(data['time_slot'])
                    time_slot = format_time_slot(start_time, end_time, False)
                    is_all_day = False
                except ValueError:
                    # If parsing fails, use as-is for backward compatibility
                    time_slot = data['time_slot']
                    is_all_day = False
            else:
                time_slot = None
                is_all_day = True
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Validate and handle date updates
    if 'date' in data:
        try:
            new_date = validate_date_input(data['date'], 'date')
            
            # Check if the new date is in the past
            if new_date < date.today():
                return create_validation_error_response("Cannot set availability for past dates", 'date')
            
            # Check for conflicts with other entries
            conflict_query = Availability.query.filter_by(
                user_id=availability.user_id,
                date=new_date,
                time_slot=time_slot
            ).filter(Availability.id != availability_id)
            
            if conflict_query.first():
                return create_validation_error_response(
                    "An availability entry already exists for this date and time", 
                    'date'
                )
            
            availability.date = new_date
            
        except ValueError as e:
            return create_validation_error_response(str(e), 'date')
    else:
        # If date is not being changed, still check for time slot conflicts
        if time_slot != availability.time_slot:
            conflict_query = Availability.query.filter_by(
                user_id=availability.user_id,
                date=availability.date,
                time_slot=time_slot
            ).filter(Availability.id != availability_id)
            
            if conflict_query.first():
                return create_validation_error_response(
                    "An availability entry already exists for this date and time",
                    'time_slot'
                )
    
    # Validate and update fields
    try:
        if 'status' in data:
            status = validate_availability_status(data['status'])
            availability.status = status
        
        if 'play_preference' in data:
            play_preference = validate_play_preference(data['play_preference'])
            availability.play_preference = play_preference
        
        if 'notes' in data:
            notes = validate_notes(data['notes'])
            availability.notes = notes
            
    except ValueError as e:
        return create_validation_error_response(str(e))
    
    # Update time_slot
    availability.time_slot = time_slot
    
    try:
        db.session.commit()
        
        # Return enhanced response with parsed time information
        response_data = availability.to_dict()
        if not is_all_day and (start_time or end_time):
            response_data.update({
                'time_start': start_time.strftime('%H:%M') if start_time else None,
                'time_end': end_time.strftime('%H:%M') if end_time else None,
                'is_all_day': False
            })
        else:
            response_data.update({
                'time_start': None,
                'time_end': None,
                'is_all_day': True
            })
        
        return jsonify({
            'message': 'Availability updated successfully',
            'availability': response_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        # Log the actual error for debugging but don't expose internal details
        app.logger.error(f"Database error in update_availability: {str(e)}")
        return jsonify({
            'error': 'Failed to update availability. Please try again.',
            'error_type': 'database_error'
        }), 500

@api_bp.route('/availability/<int:availability_id>', methods=['DELETE'])
@login_required
def delete_availability(availability_id):
    """Delete an existing availability entry."""
    # Find the availability entry
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({'error': 'Availability entry not found'}), 404
    
    # Check user ownership (users can only delete their own entries, admins can delete any)
    if not current_user.is_admin and availability.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized: You can only delete your own availability entries'}), 403
    
    # Check if the date is in the past (prevent deleting historical entries)
    if availability.date < date.today():
        return jsonify({'error': 'Cannot delete availability for past dates'}), 400
    
    # Store information for confirmation response
    deleted_info = {
        'id': availability.id,
        'date': availability.date.isoformat(),
        'time_slot': availability.time_slot,
        'status': availability.status,
        'user_id': availability.user_id
    }
    
    try:
        db.session.delete(availability)
        db.session.commit()
        
        return jsonify({
            'message': 'Availability entry deleted successfully',
            'deleted_entry': deleted_info
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete availability entry'}), 500

# Feedback Routes
@api_bp.route('/feedback', methods=['GET'])
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

@api_bp.route('/feedback', methods=['POST'])
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
@api_bp.route('/admin/users', methods=['GET'])
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

@api_bp.route('/admin/availability/filtered', methods=['GET'])
@login_required
@admin_required
def get_filtered_availability():
    """Get filtered availability data for admin users with comprehensive validation."""
    # Get and validate query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Default 50 items per page
    
    # Validate pagination parameters
    if page < 1:
        return create_validation_error_response("Page number must be positive (starting from 1)")
    if per_page < 1 or per_page > 1000:  # Limit max per_page to prevent abuse
        return create_validation_error_response("Items per page must be between 1 and 1000")
    
    # Validate date parameters
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = validate_date_input(start_date, 'start_date')
        except ValueError as e:
            return create_validation_error_response(str(e), 'start_date')
    
    if end_date:
        try:
            end_date_obj = validate_date_input(end_date, 'end_date')
        except ValueError as e:
            return create_validation_error_response(str(e), 'end_date')
    
    # Validate date range logic
    if start_date_obj and end_date_obj:
        if start_date_obj > end_date_obj:
            return create_validation_error_response(
                "Start date must be before or equal to end date",
                'date_range'
            )
        
        # Check for reasonable date ranges (not more than 5 years)
        date_diff = end_date_obj - start_date_obj
        if date_diff.days > 5 * 365:  # More than 5 years
            return create_validation_error_response(
                "Date range cannot exceed 5 years",
                'date_range'
            )
    
    # Build base query with user information
    query = Availability.query.join(User)
    
    # Apply date filters
    if start_date_obj:
        query = query.filter(Availability.date >= start_date_obj)
    
    if end_date_obj:
        query = query.filter(Availability.date <= end_date_obj)
    
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
        return create_validation_error_response(
            f"Page {page} does not exist. Total pages: {paginated_query.pages}",
            'page'
        )
    
    availability_list = paginated_query.items
    
    # Enhance response with parsed time information and user details
    enhanced_availability = []
    for avail in availability_list:
        avail_dict = avail.to_dict()
        
        # Add user information
        avail_dict['username'] = avail.user.username
        avail_dict['user_email'] = avail.user.email
        
        # Parse time_slot to extract time information
        if avail.time_slot:
            try:
                if '-' in avail.time_slot and not avail.time_slot.startswith('until'):
                    # Parse time range
                    start_time, end_time = parse_time_range(avail.time_slot)
                    avail_dict.update({
                        'time_start': start_time.strftime('%H:%M') if start_time else None,
                        'time_end': end_time.strftime('%H:%M') if end_time else None,
                        'is_all_day': False
                    })
                elif avail.time_slot.startswith('until'):
                    # Parse "until" format
                    time_str = avail.time_slot.replace('until ', '')
                    end_time = parse_time_string(time_str)
                    avail_dict.update({
                        'time_start': None,
                        'time_end': end_time.strftime('%H:%M') if end_time else None,
                        'is_all_day': False
                    })
                else:
                    # Single time
                    start_time = parse_time_string(avail.time_slot)
                    avail_dict.update({
                        'time_start': start_time.strftime('%H:%M') if start_time else None,
                        'time_end': None,
                        'is_all_day': False
                    })
            except ValueError:
                # If parsing fails, treat as legacy format
                avail_dict.update({
                    'time_start': None,
                    'time_end': None,
                    'is_all_day': False,
                    'legacy_time_slot': avail.time_slot
                })
        else:
            # All-day availability
            avail_dict.update({
                'time_start': None,
                'time_end': None,
                'is_all_day': True
            })
        
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

@api_bp.route('/admin/export/availability', methods=['GET'])
@login_required
@admin_required
def export_availability():
    """Export availability data as CSV (admin only)."""
    import csv
    from io import StringIO
    
    # Get parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Availability.query.join(User)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Availability.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Availability.date <= end_date)
    
    availability = query.order_by(Availability.date, User.username).all()
    
    # Create CSV
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Username', 'Status', 'Play Preference', 'Notes', 'Time Slot'])
    
    for avail in availability:
        cw.writerow([
            avail.date.isoformat(),
            avail.user.username,
            avail.status,
            avail.play_preference or '',
            avail.notes or '',
            avail.time_slot or ''
        ])
    
    output = si.getvalue()
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=availability_export_{date.today()}.csv'
    }
