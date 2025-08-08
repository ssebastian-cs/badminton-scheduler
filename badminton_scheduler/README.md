# Badminton Scheduler App

A full-stack web application for managing badminton player availability, preferences, and feedback. Built with Flask (Python) backend and React frontend.

## Features

### Core Functionality
- **User Management**: Simple registration and login system with user profiles
- **Availability System**: Monthly calendar view for setting availability (Available, Tentative, Not Available)
- **Play Preferences**: Choose between Drop-in, Book a Court, or Either
- **Feedback System**: Submit and view community feedback and session comments
- **Admin Panel**: User management and data export functionality

### Technical Features
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **Interactive Calendar**: FullCalendar integration for availability management
- **Real-time Updates**: Modern React components with state management
- **Data Export**: CSV export functionality for administrators
- **Session Management**: Secure user authentication with Flask sessions

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Lightweight database
- **Flask-CORS**: Cross-origin resource sharing
- **Werkzeug**: Password hashing and security

### Frontend
- **React**: JavaScript library for building user interfaces
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI components
- **FullCalendar**: Interactive calendar component
- **Axios**: HTTP client for API requests
- **Lucide Icons**: Beautiful icon library

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- pnpm (recommended) or npm
- SQLite (included with Python)

### Backend Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd badminton-scheduler/badminton_scheduler
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the configuration in `.env` as needed

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Create an admin user (run in Python shell):
   ```python
   from app import app, db
   from models import User
   
   with app.app_context():
       admin = User(username='admin', email='admin@example.com', is_admin=True)
       admin.set_password('admin123')
       db.session.add(admin)
       db.session.commit()
   ```

7. Run the development server:
   ```bash
   flask run
   ```
   The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install  # or npm install
   ```

3. Start the development server:
   ```bash
   pnpm dev  # or npm run dev
   ```
   The frontend will be available at `http://localhost:3000`

## Project Structure

```
badminton_scheduler/
├── .env                    # Environment variables
├── app.py                 # Flask application factory
├── requirements.txt       # Python dependencies
├── models.py             # Database models
├── auth.py               # Authentication routes
├── api.py                # API endpoints
├── utils.py              # Utility functions
├── wsgi.py               # WSGI entry point
├── migrations/           # Database migrations
├── frontend/             # React frontend
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md
```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database with sample data:
   ```bash
   python src/sample_data.py
   ```

5. Start the Flask development server:
   ```bash
   python src/main.py
   ```

The backend will be available at `http://localhost:5000`

### Frontend Setup (Development)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Start the development server:
   ```bash
   pnpm run dev --host
   ```

The frontend development server will be available at `http://localhost:5173`

### Production Build

1. Build the React frontend:
   ```bash
   cd frontend
   pnpm run build
   ```

2. Copy built files to Flask static directory:
   ```bash
   cd ..
   cp -r frontend/dist/* src/static/
   ```

3. Access the full application at `http://localhost:5000`

## Usage

### Demo Credentials

The application comes with pre-populated sample data:

**Admin Account:**
- Email: `admin@badminton.com`
- Password: `admin123`

**User Accounts:**
- Email: `john.smith@email.com`
- Password: `password123`
- Email: `sarah.johnson@email.com`
- Password: `password123`

(All sample users use password: `password123`)

### Getting Started

1. **Register/Login**: Create a new account or use demo credentials
2. **Set Availability**: Use the calendar to mark your available days
3. **Choose Preferences**: Select Drop-in, Book a Court, or Either
4. **View Group Availability**: See who's available on specific dates
5. **Submit Feedback**: Share comments and rate sessions
6. **Admin Features**: Manage users and export data (admin accounts only)

## API Documentation

### Authentication Endpoints
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/me` - Get current user profile
- `PUT /api/me` - Update user profile

### Availability Endpoints
- `POST /api/availability` - Create/update availability
- `GET /api/availability/me` - Get user's availability
- `GET /api/availability/date/{date}` - Get group availability for date
- `DELETE /api/availability/{id}` - Delete availability entry
- `POST /api/availability/bulk` - Bulk create availability

### Feedback Endpoints
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/me` - Get user's feedback
- `GET /api/feedback/all` - Get all feedback
- `PUT /api/feedback/{id}` - Update feedback
- `DELETE /api/feedback/{id}` - Delete feedback

### Admin Endpoints
- `GET /api/admin/users` - List all users
- `DELETE /api/admin/users/{id}` - Delete user
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/export/users` - Export users (CSV)
- `GET /api/admin/export/availability` - Export availability (CSV)
- `GET /api/admin/export/feedback` - Export feedback (CSV)

## Database Schema

### Users Table
- `id`: Primary key
- `name`: User's full name
- `email`: Unique email address
- `password_hash`: Hashed password
- `skill_level`: Beginner, Intermediate, Advanced
- `created_date`: Registration timestamp

### Availability Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `date`: Availability date
- `time_slot`: Optional time specification
- `status`: available, tentative, not_available
- `preference_type`: drop_in, book_a_court, either

### Feedback Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `date`: Submission timestamp
- `message`: Feedback content
- `rating`: Optional 1-5 rating
- `type`: general, session_comment

## Development

### Project Structure
```
badminton_scheduler/
├── venv/                   # Python virtual environment
├── src/                    # Backend source code
│   ├── models/            # Database models
│   │   └── user.py        # User, Availability, Feedback models
│   ├── routes/            # API route handlers
│   │   ├── auth.py        # Authentication routes
│   │   ├── availability.py # Availability management
│   │   ├── feedback.py    # Feedback system
│   │   ├── admin.py       # Admin functionality
│   │   └── user.py        # User management
│   ├── static/            # Frontend build output
│   ├── database/          # SQLite database
│   ├── main.py            # Flask application entry point
│   └── sample_data.py     # Database seeding script
├── frontend/              # React frontend source
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utility functions
│   │   └── App.jsx        # Main application component
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Adding New Features

1. **Backend**: Add new routes in `src/routes/`, update models in `src/models/`
2. **Frontend**: Create components in `src/components/`, add API calls in `src/lib/api.jsx`
3. **Database**: Update models and run migrations if needed

## Deployment

### Local Deployment
1. Follow the installation steps above
2. Build the frontend for production
3. Copy built files to Flask static directory
4. Run Flask application

### Production Deployment
- Configure environment variables for production
- Use a production WSGI server (e.g., Gunicorn)
- Set up proper database (PostgreSQL recommended for production)
- Configure reverse proxy (Nginx)
- Enable HTTPS

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the documentation above
2. Review the sample data and demo credentials
3. Examine the API endpoints and database schema
4. Test with the provided sample users

## Future Enhancements

- Email notifications for session reminders
- Advanced session/event management
- Real-time updates using WebSockets
- Mobile application
- Integration with court booking systems
- Enhanced reporting and analytics

