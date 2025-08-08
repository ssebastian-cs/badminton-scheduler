# Project Architecture and Plan: Badminton Scheduler App

## 1. Introduction

This document outlines the architecture and detailed plan for developing the Badminton Scheduler web application. The goal is to create a free, open-source, and optimal full-stack solution for managing availability, preferences, and feedback for a group of badminton players. This plan incorporates the chosen technologies and addresses the core requirements identified in the initial project overview.

## 2. Technology Stack

Based on the research conducted, the following technologies have been selected for optimal performance, scalability, and ease of development:

### 2.1. Backend: FastAPI

FastAPI is chosen for the backend due to its high performance, asynchronous capabilities, built-in data validation (Pydantic), and automatic API documentation. It will handle all server-side logic, database interactions, and API endpoint management.

### 2.2. Frontend: React

React is selected for the frontend to build a dynamic, responsive, and user-friendly interface. Its component-based architecture promotes modularity and reusability, facilitating efficient UI development.

### 2.3. Database: SQLite with SQLAlchemy

SQLite will be used as the database for its simplicity, portability, and ease of setup, aligning with the project's free and open-source nature. SQLAlchemy will serve as the Object-Relational Mapper (ORM) for seamless interaction between the FastAPI application and the SQLite database.

### 2.4. Styling: Tailwind CSS

Tailwind CSS will be utilized for styling the frontend. Its utility-first approach allows for rapid and highly customizable responsive design, ensuring a clean and mobile-friendly user experience.

### 2.5. Calendar Component: FullCalendar

FullCalendar is chosen as the interactive calendar widget for managing user availability. It is feature-rich, open-source, and offers excellent compatibility with React.

## 3. Database Schema Design

The database will consist of several tables to store user information, availability, preferences, feedback, and session details. The schema is designed to be efficient and support the application's core functionalities.

### 3.1. Users Table

This table will store information about registered users.

| Field          | Data Type | Constraints         | Description                               |
|----------------|-----------|---------------------|-------------------------------------------|
| `id`           | INTEGER   | PRIMARY KEY, AUTOINC | Unique identifier for the user            |
| `name`         | TEXT      | NOT NULL            | User's full name                          |
| `email`        | TEXT      | NOT NULL, UNIQUE    | User's email address (used for login)     |
| `password_hash`| TEXT      | NOT NULL            | Hashed password for security              |
| `skill_level`  | TEXT      |                     | User's badminton skill level (e.g., Beginner, Intermediate, Advanced) |
| `created_date` | DATETIME  | NOT NULL            | Timestamp of user registration            |

### 3.2. Availability Table

This table will store each user's availability for specific dates and time slots.

| Field           | Data Type | Constraints         | Description                               |
|-----------------|-----------|---------------------|-------------------------------------------|
| `id`            | INTEGER   | PRIMARY KEY, AUTOINC | Unique identifier for the availability entry |
| `user_id`       | INTEGER   | NOT NULL, FOREIGN KEY | Reference to the `users` table            |
| `date`          | DATE      | NOT NULL            | Date of availability                      |
| `time_slot`     | TEXT      |                     | Specific time slot (e.g., 'morning', 'afternoon', 'evening', '19:00-21:00') |
| `status`        | TEXT      | NOT NULL            | Availability status (e.g., 'available', 'not_available', 'tentative') |
| `preference_type`| TEXT      | NOT NULL            | Play preference for this availability (e.g., 'drop_in', 'book_a_court', 'either') |

### 3.3. Feedback Table

This table will store user feedback and comments.

| Field          | Data Type | Constraints         | Description                               |
|----------------|-----------|---------------------|-------------------------------------------|
| `id`           | INTEGER   | PRIMARY KEY, AUTOINC | Unique identifier for the feedback entry  |
| `user_id`      | INTEGER   | NOT NULL, FOREIGN KEY | Reference to the `users` table            |
| `date`         | DATETIME  | NOT NULL            | Timestamp of feedback submission          |
| `message`      | TEXT      | NOT NULL            | The feedback message or comment           |
| `rating`       | INTEGER   |                     | Optional rating for a session (e.g., 1-5) |
| `type`         | TEXT      |                     | Type of feedback (e.g., 'general', 'session_comment') |

### 3.4. Sessions/Events Table (Optional, for organized games)

This table can be added later if the application evolves to support organized sessions with court reservations.

| Field          | Data Type | Constraints         | Description                               |
|----------------|-----------|---------------------|-------------------------------------------|
| `id`           | INTEGER   | PRIMARY KEY, AUTOINC | Unique identifier for the session         |
| `title`        | TEXT      | NOT NULL            | Title of the session (e.g., 'Tuesday Night Badminton') |
| `date`         | DATE      | NOT NULL            | Date of the session                       |
| `time`         | TIME      | NOT NULL            | Time of the session                       |
| `location`     | TEXT      |                     | Location or court details                 |
| `organizer_id` | INTEGER   | FOREIGN KEY         | Reference to the `users` table (organizer) |
| `description`  | TEXT      |                     | Detailed description of the session       |

## 4. API Endpoints (FastAPI)

The FastAPI backend will expose a set of RESTful API endpoints to handle all interactions with the frontend and the database.

### 4.1. User Management

*   `POST /api/register`: Register a new user.
*   `POST /api/login`: Authenticate user and return access token.
*   `GET /api/users/me`: Get current user's profile.
*   `PUT /api/users/me`: Update current user's profile.

### 4.2. Availability Management

*   `POST /api/availability`: Submit or update user availability for a date/time.
*   `GET /api/availability/{user_id}`: Get availability for a specific user.
*   `GET /api/availability/date/{date}`: Get all available users for a specific date (for organizers/group view).
*   `DELETE /api/availability/{id}`: Delete an availability entry.

### 4.3. Play Preferences

*   `PUT /api/preferences/me`: Update current user's default play preferences.

### 4.4. Feedback & Comments

*   `POST /api/feedback`: Submit new feedback or comment.
*   `GET /api/feedback/{user_id}`: Get feedback submitted by a specific user.
*   `GET /api/feedback/date/{date}`: Get comments for a specific date/event.

### 4.5. Admin Panel (Basic)

*   `GET /api/admin/users`: Get a list of all users (admin only).
*   `DELETE /api/admin/users/{user_id}`: Delete a user (admin only).
*   `GET /api/admin/availability/export`: Export all availability data (CSV, admin only).

## 5. Frontend Components (React)

The React frontend will be structured into several components, each responsible for a specific part of the UI and interacting with the FastAPI backend.

### 5.1. Authentication Components

*   `RegisterForm`: Component for user registration.
*   `LoginForm`: Component for user login.
*   `UserProfile`: Displays and allows editing of user profile information.

### 5.2. Dashboard Component

*   `Dashboard`: Overview of user's availability, upcoming games, and recent feedback.

### 5.3. Calendar Interface Components

*   `AvailabilityCalendar`: Main calendar component using FullCalendar for displaying and setting availability.
*   `AvailabilityForm`: Modal or sidebar for detailed availability input (status, time slot, preference).

### 5.4. Group View Component

*   `GroupAvailabilityView`: Displays who is available on specific dates, primarily for organizers.

### 5.5. Feedback Components

*   `FeedbackForm`: Component for submitting general feedback or comments for specific dates.
*   `FeedbackList`: Displays historical feedback and comments.

### 5.6. Admin Components

*   `UserManagement`: Table to list and manage users.
*   `DataExport`: Interface for exporting data.

## 6. Application Flow

1.  **User Registration/Login:** New users register, existing users log in. Authentication tokens are managed on the frontend and sent with subsequent API requests.
2.  **Dashboard View:** After login, users land on a dashboard showing their current status and upcoming events.
3.  **Setting Availability:** Users navigate to the calendar, select dates, and mark their availability (available, not available, tentative) along with preferred play style. Bulk selection tools will be provided.
4.  **Viewing Group Availability:** Organizers or authorized users can view a consolidated calendar showing who is available on which dates.
5.  **Submitting Feedback:** Users can submit general feedback or comments related to specific dates/events.
6.  **Admin Actions:** Administrators can manage users and export data through a dedicated panel.

## 7. Development Plan (Phased Approach)

### Phase 1: Backend Core (FastAPI & SQLAlchemy)

*   Set up FastAPI project structure.
*   Define SQLAlchemy models for Users, Availability, Feedback.
*   Implement user authentication (registration, login, token generation).
*   Develop API endpoints for user profile management.
*   Implement API endpoints for basic availability management (create, read, update, delete).
*   Implement API endpoints for feedback submission and retrieval.

### Phase 2: Frontend Core (React & Tailwind CSS)

*   Set up React project with Vite.
*   Integrate Tailwind CSS for styling.
*   Develop basic layout and navigation.
*   Create authentication components (Register, Login, User Profile).
*   Connect frontend authentication to FastAPI backend.

### Phase 3: Calendar and Availability Integration

*   Integrate FullCalendar into the React application.
*   Develop components for setting and displaying user availability on the calendar.
*   Implement bulk selection tools for availability.
*   Connect calendar interactions to FastAPI availability API endpoints.

### Phase 4: Feedback and Group View

*   Develop feedback submission and display components.
*   Implement the group availability view, fetching data from the backend.

### Phase 5: Admin Panel and Additional Features

*   Develop basic admin interface for user management.
*   Implement data export functionality (CSV).
*   Add input validation and error handling across the application.
*   Implement basic security measures (CSRF protection).

### Phase 6: Testing, Optimization, and Deployment

*   Conduct thorough testing (unit, integration, end-to-end).
*   Optimize performance for both backend and frontend.
*   Prepare deployment scripts and documentation.
*   Deploy the application.

## 8. Deliverables

Upon completion, the following deliverables will be provided:

*   Complete working Python (FastAPI) and JavaScript (React) application.
*   Database setup script with sample data.
*   `requirements.txt` for Python dependencies and `package.json` for Node.js dependencies.
*   Comprehensive `README.md` with setup and usage instructions.
*   Simple deployment guide for local hosting.

## 9. Future Enhancements (Out of Scope for Initial Release)

*   Email notifications for session reminders or updates.
*   More advanced session/event management with court booking.
*   Real-time updates using WebSockets for group view.
*   Enhanced admin features and reporting.
*   User avatars/profile pictures.

This plan provides a clear roadmap for developing the Badminton Scheduler application, ensuring all core requirements are met with a robust, performant, and maintainable architecture.

