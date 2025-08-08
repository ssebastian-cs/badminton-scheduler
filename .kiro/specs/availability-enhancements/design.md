# Design Document

## Overview

This design document outlines the technical approach for enhancing the badminton scheduler's availability system with time-specific scheduling, user self-management capabilities, and administrative filtering. The enhancements will be implemented as modifications to the existing Flask backend and HTML/JavaScript frontend, maintaining backward compatibility while adding new functionality.

## Architecture

### System Components

The enhancements will modify existing components rather than introducing new architectural layers:

1. **Database Layer**: Extend the existing Availability model to support time slots
2. **API Layer**: Enhance existing endpoints and add new ones for edit/delete operations
3. **Frontend Layer**: Update the HTML/JavaScript interface with new controls and functionality
4. **Authentication Layer**: Leverage existing user authentication for permission checks

### Data Flow

```
User Interface → API Endpoints → Database Models → Response → UI Update
     ↓              ↓              ↓               ↓         ↓
Time Input → Validation → Storage → Retrieval → Display
Edit/Delete → Permission Check → Database Update → Confirmation
Admin Filter → Query Parameters → Filtered Results → Display
```

## Components and Interfaces

### Database Model Changes

#### Enhanced Availability Model

```python
class Availability(db.Model):
    # Existing fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum('available', 'tentative', 'not_available'), nullable=False)
    play_preference = db.Column(db.Enum('drop_in', 'book_court', 'either'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enhanced fields
    time_start = db.Column(db.Time, nullable=True)  # Start time for availability
    time_end = db.Column(db.Time, nullable=True)    # End time for availability
    is_all_day = db.Column(db.Boolean, default=True)  # Flag for all-day availability
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Updated unique constraint to allow multiple time slots per day
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', 'time_start', 'time_end', name='unique_availability_time'),
    )
```

### API Endpoint Enhancements

#### Modified Endpoints

**POST /api/availability** (Enhanced)
- Accept time_start, time_end, and is_all_day parameters
- Validate time formats and logical consistency
- Handle multiple entries per date

**GET /api/availability** (Enhanced)
- Add date filtering parameters for admin users
- Return time information in responses
- Support pagination for large result sets

#### New Endpoints

**PUT /api/availability/{id}** (New)
- Update existing availability entry
- Validate user ownership or admin privileges
- Prevent modification of past dates

**DELETE /api/availability/{id}** (New)
- Delete availability entry
- Validate user ownership or admin privileges
- Prevent deletion of past dates

**GET /api/admin/availability/filtered** (New)
- Admin-only endpoint for filtered availability data
- Support date range parameters
- Include user information in responses

### Frontend Interface Design

#### Time Input Component

```html
<div class="time-input-section">
    <div class="form-group">
        <label>
            <input type="checkbox" id="allDayCheck" checked> All Day
        </label>
    </div>
    <div id="timeInputs" class="hidden">
        <div class="form-group">
            <label for="timeStart">Start Time:</label>
            <input type="time" id="timeStart">
        </div>
        <div class="form-group">
            <label for="timeEnd">End Time:</label>
            <input type="time" id="timeEnd">
        </div>
    </div>
</div>
```

#### Availability Management Interface

```html
<div class="availability-item">
    <div class="availability-info">
        <strong>Date:</strong> {date}
        <strong>Time:</strong> {time_display}
        <strong>Status:</strong> {status}
    </div>
    <div class="availability-actions">
        <button onclick="editAvailability({id})" class="edit-btn">Edit</button>
        <button onclick="deleteAvailability({id})" class="delete-btn">Delete</button>
    </div>
</div>
```

#### Admin Filter Interface

```html
<div class="admin-filters">
    <div class="filter-group">
        <label for="filterStartDate">From Date:</label>
        <input type="date" id="filterStartDate">
    </div>
    <div class="filter-group">
        <label for="filterEndDate">To Date:</label>
        <input type="date" id="filterEndDate">
    </div>
    <button onclick="applyFilters()">Apply Filters</button>
    <button onclick="clearFilters()">Clear</button>
</div>
```

## Data Models

### Time Handling Strategy

1. **Storage**: Store times in UTC using Python's `time` type
2. **Display**: Show times in user's local timezone (browser-based)
3. **Input**: Accept common time formats and convert to standard format
4. **Validation**: Ensure end time is after start time when both are specified

### Availability Entry Structure

```json
{
    "id": 123,
    "user_id": 45,
    "username": "john_smith",
    "date": "2025-08-15",
    "is_all_day": false,
    "time_start": "19:00",
    "time_end": "21:00",
    "status": "available",
    "play_preference": "either",
    "notes": "Prefer competitive games",
    "created_at": "2025-08-01T10:30:00Z",
    "updated_at": "2025-08-01T10:30:00Z"
}
```

### Filter Parameters Structure

```json
{
    "start_date": "2025-08-01",
    "end_date": "2025-08-31",
    "user_id": null,
    "status": null,
    "time_filter": null
}
```

## Error Handling

### Validation Errors

1. **Time Format Errors**: Provide clear feedback for invalid time inputs
2. **Logic Errors**: Validate that end time is after start time
3. **Date Errors**: Prevent setting availability for past dates
4. **Permission Errors**: Clear messages for unauthorized edit/delete attempts

### Database Errors

1. **Constraint Violations**: Handle duplicate time slot conflicts gracefully
2. **Connection Issues**: Provide retry mechanisms and user feedback
3. **Transaction Failures**: Ensure data consistency with proper rollback

### User Experience Errors

1. **Network Timeouts**: Show loading states and retry options
2. **Concurrent Modifications**: Handle cases where data changes during editing
3. **Browser Compatibility**: Graceful degradation for older browsers

## Testing Strategy

### Unit Tests

1. **Model Tests**: Validate time handling, constraints, and data integrity
2. **API Tests**: Test all endpoints with various input combinations
3. **Validation Tests**: Ensure proper error handling for invalid inputs

### Integration Tests

1. **End-to-End Workflows**: Test complete user journeys for each feature
2. **Permission Tests**: Verify access control for edit/delete operations
3. **Admin Filter Tests**: Validate filtering logic and performance

### User Acceptance Tests

1. **Time Input Usability**: Test time picker functionality across devices
2. **Edit/Delete Workflows**: Verify intuitive user experience
3. **Admin Dashboard**: Test filtering and data export functionality

### Performance Tests

1. **Database Queries**: Ensure efficient filtering with large datasets
2. **Frontend Responsiveness**: Test UI performance with many availability entries
3. **Concurrent Users**: Validate system behavior under load

## Security Considerations

### Authorization

1. **User Ownership**: Verify users can only edit/delete their own entries
2. **Admin Privileges**: Ensure admin-only features are properly protected
3. **Past Date Protection**: Prevent modification of historical data

### Input Validation

1. **Time Format Sanitization**: Prevent injection attacks through time inputs
2. **Date Range Validation**: Ensure reasonable date ranges for filters
3. **SQL Injection Prevention**: Use parameterized queries for all database operations

### Data Privacy

1. **User Information**: Limit exposure of personal data in admin views
2. **Audit Logging**: Track modifications for accountability
3. **Session Management**: Ensure proper authentication for sensitive operations

## Implementation Phases

### Phase 1: Database and Backend API
- Extend Availability model with time fields
- Implement new API endpoints for edit/delete
- Add validation logic for time inputs
- Create database migration scripts

### Phase 2: Frontend Time Input
- Add time picker components to availability form
- Implement all-day toggle functionality
- Update display logic for time information
- Add client-side validation

### Phase 3: User Management Features
- Implement edit/delete functionality in UI
- Add confirmation dialogs and error handling
- Update availability list display with action buttons
- Test user permission enforcement

### Phase 4: Admin Filtering
- Create admin filter interface
- Implement filtered data retrieval
- Add export functionality with filters
- Optimize query performance

### Phase 5: Testing and Polish
- Comprehensive testing across all features
- Performance optimization
- UI/UX refinements
- Documentation updates