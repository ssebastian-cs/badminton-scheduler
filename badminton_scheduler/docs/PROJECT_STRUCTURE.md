# Badminton Scheduler - Project Structure

## Overview
This document describes the organized project structure for the Badminton Scheduler application.

## Directory Structure

```
badminton_scheduler/
├── docs/                           # Documentation files
│   ├── PROJECT_STRUCTURE.md        # This file
│   ├── TASK*_IMPLEMENTATION_SUMMARY.md  # Task implementation summaries
│   └── TEST_IMPLEMENTATION_SUMMARY.md   # Test documentation
├── scripts/                        # Utility and setup scripts
│   ├── create_sample_data.py       # Sample data generation
│   ├── create_sample_data_simple.py
│   ├── create_test_data.py
│   ├── demo_admin_filtering.py     # Demo scripts
│   ├── migrate_availability.py    # Database migration scripts
│   ├── quick_test.py              # Quick testing utilities
│   ├── run_comprehensive_tests.py # Test runners
│   ├── start_app.py               # Application startup scripts
│   ├── start_server.py
│   └── verify_*.py                # Verification scripts
├── static/                         # Static web assets
│   ├── static_frontend.html       # Main frontend application
│   └── test_*.html                # Test HTML files
├── tests/                          # Test files
│   ├── test_*.py                  # All test files
│   └── ...
├── frontend/                       # Additional frontend assets (if any)
├── instance/                       # Flask instance folder
├── venv/                          # Virtual environment (if present)
├── __pycache__/                   # Python cache files
├── .pytest_cache/                 # Pytest cache files
├── __init__.py                    # Python package initialization
├── .env                           # Environment variables
├── api.py                         # API routes and endpoints
├── app.py                         # Flask application factory
├── auth.py                        # Authentication routes
├── models.py                      # Database models
├── run.py                         # Main application runner
├── utils.py                       # Utility functions
├── wsgi.py                        # WSGI entry point
├── README.md                      # Project documentation
└── requirements.txt               # Python dependencies
```

## Core Application Files

### Main Application
- **`run.py`** - Main application entry point and Flask app configuration
- **`app.py`** - Flask application factory (if using factory pattern)
- **`wsgi.py`** - WSGI entry point for production deployment

### Backend Components
- **`models.py`** - SQLAlchemy database models (User, Availability, Feedback)
- **`api.py`** - REST API endpoints and business logic
- **`auth.py`** - Authentication and authorization routes
- **`utils.py`** - Utility functions and decorators

### Frontend
- **`static/static_frontend.html`** - Single-page application with complete UI
- **`frontend/`** - Additional frontend assets (if separated)

### Configuration
- **`.env`** - Environment variables (database URL, secret keys, etc.)
- **`requirements.txt`** - Python package dependencies
- **`__init__.py`** - Package initialization

## Documentation (`docs/`)

### Implementation Summaries
- **`TASK*_IMPLEMENTATION_SUMMARY.md`** - Detailed implementation documentation for each task
- **`TEST_IMPLEMENTATION_SUMMARY.md`** - Testing strategy and results
- **`PROJECT_STRUCTURE.md`** - This file

## Scripts (`scripts/`)

### Data Management
- **`create_sample_data.py`** - Generate sample data for development/demo
- **`create_test_data.py`** - Generate test data for automated testing
- **`migrate_availability.py`** - Database migration utilities

### Development Tools
- **`start_server.py`** - Development server startup with sample data
- **`start_app.py`** - Alternative application startup
- **`quick_test.py`** - Quick functionality testing
- **`run_comprehensive_tests.py`** - Run full test suite

### Verification
- **`verify_*.py`** - Various verification and validation scripts
- **`demo_*.py`** - Demonstration scripts for specific features

## Tests (`tests/`)

### Test Categories
- **`test_api*.py`** - API endpoint testing
- **`test_admin*.py`** - Admin functionality testing
- **`test_validation*.py`** - Input validation testing
- **`test_task*.py`** - Task-specific requirement testing
- **`test_comprehensive*.py`** - Integration and comprehensive testing
- **`test_final*.py`** - Final integration testing

### Test Types
- **Unit Tests** - Individual function/method testing
- **Integration Tests** - Component interaction testing
- **API Tests** - REST endpoint testing
- **Frontend Tests** - UI functionality testing
- **Comprehensive Tests** - End-to-end workflow testing

## Static Assets (`static/`)

### Web Interface
- **`static_frontend.html`** - Complete single-page application
  - Responsive design with mobile support
  - Admin and user interfaces
  - Real-time form validation
  - Loading states and visual feedback

### Test Assets
- **`test_*.html`** - HTML files for testing specific UI components

## Development Workflow

### 1. Setup
```bash
cd badminton_scheduler
pip install -r requirements.txt
python scripts/start_server.py  # Starts with sample data
```

### 2. Development
- Edit core files: `run.py`, `api.py`, `models.py`, `auth.py`
- Update frontend: `static/static_frontend.html`
- Add utilities: `utils.py`

### 3. Testing
```bash
python scripts/run_comprehensive_tests.py  # Run all tests
python tests/test_specific_feature.py      # Run specific tests
```

### 4. Documentation
- Update implementation summaries in `docs/`
- Document new features and changes
- Update this structure document as needed

## Key Features by File

### `run.py` - Main Application
- Flask app configuration
- Database initialization
- Route registration
- Development server

### `api.py` - REST API
- Availability CRUD operations
- Admin filtering and management
- Input validation and error handling
- Optimized database queries

### `models.py` - Database Models
- User authentication model
- Availability tracking with time support
- Feedback system
- Database indexes for performance

### `static/static_frontend.html` - Frontend
- Single-page application
- Responsive design
- Admin and user interfaces
- Real-time validation
- Loading states and visual feedback

### `auth.py` - Authentication
- User login/logout
- Session management
- Admin authorization
- Password hashing

## Deployment Structure

### Production Files
- `wsgi.py` - WSGI entry point
- `requirements.txt` - Dependencies
- `.env` - Environment configuration
- Core application files

### Development Files
- `scripts/` - Development utilities
- `tests/` - Test suite
- `docs/` - Documentation
- Cache directories

This structure provides clear separation of concerns, making the project maintainable and scalable while keeping development and testing workflows organized.