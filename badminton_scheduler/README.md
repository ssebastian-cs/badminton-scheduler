# Badminton Scheduler

A Flask-based web application for managing badminton player availability and scheduling with a modern, responsive interface.

## 🏸 Features

### Core Functionality
- **User Authentication** - Secure login/logout with session management
- **Availability Management** - Flexible time slot tracking with all-day or specific time ranges
- **Admin Interface** - Comprehensive admin panel for user and data management
- **Responsive Design** - Mobile-first design with touch-friendly controls
- **Real-time Validation** - Instant feedback on form inputs with helpful error messages

### Advanced Features
- **Time Format Support** - Multiple time formats (12/24 hour, with/without minutes)
- **Database Optimization** - Indexed queries and pagination for large datasets
- **Visual Feedback** - Loading states, toast notifications, and progress indicators
- **Accessibility** - Keyboard navigation, screen reader support, high contrast mode
- **Performance** - Optimized queries, debounced inputs, and efficient rendering

## 🚀 Quick Start

### Option 1: Development Server with Sample Data
```bash
cd badminton_scheduler
pip install -r requirements.txt
python scripts/start_server.py
```
This will:
- Install dependencies
- Create sample data (users, availability, feedback)
- Start the development server
- Open your browser automatically

**Demo Credentials:**
- **Admin:** admin / admin123
- **User:** john_smith / password123

### Option 2: Basic Setup
```bash
cd badminton_scheduler
pip install -r requirements.txt
python run.py
```

Access the application at `http://localhost:5000/static/static_frontend.html`

## 📁 Project Structure

```
badminton_scheduler/
├── docs/                    # Documentation and implementation summaries
├── scripts/                 # Utility scripts and data generation
├── static/                  # Frontend assets (HTML, CSS, JS)
├── tests/                   # Comprehensive test suite
├── api.py                   # REST API endpoints
├── models.py                # Database models
├── auth.py                  # Authentication routes
├── run.py                   # Main application entry point
└── utils.py                 # Utility functions
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure documentation.

## 🔧 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Availability Management
- `GET /api/availability` - Get availability data (with filtering)
- `POST /api/availability` - Create availability entry
- `PUT /api/availability/<id>` - Update availability entry
- `DELETE /api/availability/<id>` - Delete availability entry

### Admin Features
- `GET /api/admin/availability/filtered` - Advanced filtering with pagination
- `GET /api/admin/users` - User management
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/<id>` - Update user
- `DELETE /api/admin/users/<id>` - Delete user

### Feedback System
- `GET /api/feedback` - Get feedback entries
- `POST /api/feedback` - Submit feedback

## 👨‍💼 Admin Features

- **User Management** - Create, edit, delete users with admin privileges
- **Advanced Filtering** - Filter availability by date range, user, status
- **Pagination** - Handle large datasets efficiently
- **Data Export** - Export availability data to CSV
- **Real-time Updates** - Live data refresh and filtering

## 🧪 Testing

### Run All Tests
```bash
python scripts/run_comprehensive_tests.py
```

### Run Specific Test Categories
```bash
# API tests
python -m pytest tests/test_api*.py -v

# Admin functionality tests
python -m pytest tests/test_admin*.py -v

# Validation tests
python -m pytest tests/test_validation*.py -v

# Integration tests
python -m pytest tests/test_final*.py -v
```

### Test Coverage
- **18+ comprehensive tests** covering all functionality
- **API endpoint testing** with authentication and validation
- **Admin interface testing** with filtering and permissions
- **Input validation testing** with edge cases
- **Integration testing** for complete workflows

## 🎨 User Interface

### Modern Design
- **Grok-inspired theme** with dark mode and neon accents
- **Responsive layout** that works on all screen sizes
- **Touch-friendly controls** optimized for mobile devices
- **Smooth animations** and visual feedback

### User Experience
- **Loading states** for all operations
- **Toast notifications** for success/error feedback
- **Real-time validation** with helpful error messages
- **Keyboard shortcuts** for power users
- **Auto-save functionality** to prevent data loss

## 🔒 Security Features

- **Password hashing** with Werkzeug security
- **Session management** with Flask-Login
- **CSRF protection** for form submissions
- **Input validation** and sanitization
- **Admin authorization** for sensitive operations

## 📊 Performance Optimizations

- **Database indexing** on frequently queried columns
- **Query optimization** with eager loading and pagination
- **Frontend optimization** with debounced inputs and efficient rendering
- **Memory management** with proper cleanup and resource handling

## 🌐 Browser Support

- **Modern browsers** (Chrome, Firefox, Safari, Edge)
- **Mobile browsers** with touch optimization
- **Accessibility features** for screen readers
- **Progressive enhancement** for older browsers

## 📚 Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed project organization
- [Implementation Summaries](docs/) - Task-by-task implementation details
- [API Documentation](docs/) - Complete API reference
- [Testing Guide](docs/) - Testing strategy and results

## 🤝 Contributing

1. Follow the existing code structure and style
2. Add tests for new features
3. Update documentation as needed
4. Use the scripts in `scripts/` for development tasks

## 📄 License

This project is for educational and demonstration purposes.