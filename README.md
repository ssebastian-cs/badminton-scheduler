# Badminton Scheduler

A comprehensive availability management system for badminton scheduling with role-based authentication, built with Flask and featuring a distinctive black background with fluorescent green accents.

## Features

### User Features
- **User Registration & Authentication**: Secure login system with session management
- **Personal Availability Management**: Add, edit, and delete your availability for future games
- **Availability Viewing**: View all users' availability with filtering options (today, week, month, date range)
- **Comments System**: Post and manage comments to communicate with other players
- **Mobile-Responsive Design**: Optimized for mobile devices with touch-friendly interface

### Admin Features
- **User Management**: Create, edit, block/unblock, and delete user accounts
- **Content Moderation**: Edit or delete any user's availability entries and comments
- **Admin Dashboard**: Distinct visual interface with administrative controls
- **Audit Logging**: Track all administrative actions for accountability

### Technical Features
- **Role-Based Access Control**: Separate permissions for Users and Admins
- **Data Validation**: Comprehensive form validation and security measures
- **Responsive Design**: Mobile-first design with TailwindCSS
- **Security**: CSRF protection, password hashing, SQL injection prevention

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd badminton-scheduler
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python scripts/init_database.py init
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

5. **Access the application**:
   - Open your browser and go to `http://localhost:5000`
   - Login with default admin credentials:
     - Username: `admin`
     - Password: `admin123`

## Configuration

### Environment Variables

For production deployment, set these environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///badminton_scheduler_prod.db"
export FLASK_ENV="production"
```

### Configuration Files

- `config/development.py` - Development settings
- `config/production.py` - Production settings
- `config/testing.py` - Testing settings

## Database Management

### Initialize Database
```bash
python scripts/init_database.py init
```

### Reset Database
```bash
python scripts/init_database.py reset
```

### Check Database Health
```bash
python scripts/init_database.py health
```

### Run Migrations
```bash
python scripts/init_database.py migrate --migration-file migrations/001_initial_schema.sql
```

## Testing

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/test_models.py tests/test_forms.py -v

# Integration tests only
python -m pytest tests/test_routes.py -v

# End-to-end tests only
python -m pytest tests/test_e2e_integration.py -v
```

### Test Coverage
```bash
python -m pytest --cov=app tests/
```

## Deployment

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   cd deploy/docker
   docker-compose up -d
   ```

2. **Access the application**:
   - HTTP: `http://localhost`
   - HTTPS: `https://localhost` (requires SSL certificates)

### Manual Deployment

1. **Use the deployment script**:
   ```bash
   chmod +x deploy/deploy.sh
   ./deploy/deploy.sh deploy production
   ```

2. **Health check**:
   ```bash
   ./deploy/deploy.sh health
   ```

3. **Rollback if needed**:
   ```bash
   ./deploy/deploy.sh rollback
   ```

## API Endpoints

### Authentication
- `GET /auth/login` - Login page
- `POST /auth/login` - Process login
- `GET /auth/logout` - Logout user
- `POST /auth/register` - Register new user (Admin only)

### Availability Management
- `GET /` - Dashboard with today's availability
- `GET /availability` - Filtered availability view
- `POST /availability/add` - Add new availability
- `POST /availability/<id>/edit` - Edit availability
- `POST /availability/<id>/delete` - Delete availability

### Comments
- `GET /comments` - View all comments
- `POST /comments/add` - Add new comment
- `POST /comments/<id>/edit` - Edit comment
- `POST /comments/<id>/delete` - Delete comment

### Admin Routes
- `GET /admin/` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/users/create` - Create new user
- `POST /admin/users/<id>/edit` - Edit user
- `POST /admin/users/<id>/toggle` - Block/unblock user
- `POST /admin/users/<id>/delete` - Delete user
- `GET /admin/actions` - View admin actions log

### Utility
- `GET /health` - Application health check

## Project Structure

```
badminton-scheduler/
├── app/                    # Main application package
│   ├── __init__.py        # Application factory
│   ├── models.py          # Database models
│   ├── forms.py           # WTForms form classes
│   ├── routes/            # Route blueprints
│   ├── templates/         # Jinja2 templates
│   └── static/            # Static files (CSS, JS, images)
├── config/                # Configuration files
├── deploy/                # Deployment configurations
├── migrations/            # Database migration scripts
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── run.py                # Application entry point
└── README.md             # This file
```

## Development

### Adding New Features

1. **Create database models** in `app/models.py`
2. **Create forms** in `app/forms.py`
3. **Add routes** in appropriate blueprint in `app/routes/`
4. **Create templates** in `app/templates/`
5. **Write tests** in `tests/`
6. **Update documentation**

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Write tests for all new functionality

### Database Schema

The application uses SQLite with the following main tables:
- `users` - User accounts and authentication
- `availability` - User availability entries
- `comments` - User comments and feedback
- `admin_actions` - Audit log for administrative actions

## Security Considerations

- **Password Security**: Passwords are hashed using bcrypt
- **CSRF Protection**: All forms include CSRF tokens
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Session Security**: Secure session cookies with proper configuration
- **Input Validation**: All user inputs are validated and sanitized
- **Role-Based Access**: Proper permission checks on all routes

## Troubleshooting

### Common Issues

1. **Database not found**: Run `python scripts/init_database.py init`
2. **Permission denied**: Check file permissions and user roles
3. **Port already in use**: Change port in `run.py` or kill existing process
4. **Static files not loading**: Check static file paths and permissions

### Logs

- Application logs: `logs/badminton_scheduler.log`
- Deployment logs: `/var/log/badminton-scheduler-deploy.log`

### Health Check

Visit `/health` endpoint to check application status and database connectivity.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section above
- Review the test suite for usage examples
- Check application logs for error details

## Changelog

### Version 1.0.0
- Initial release with core functionality
- User authentication and registration
- Availability management system
- Comments and feedback system
- Admin user management
- Mobile-responsive design
- Comprehensive test suite
- Docker deployment support