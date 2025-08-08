# Alwaysdata Deployment Guide for Badminton Scheduler

This guide will help you deploy your Flask-based Badminton Scheduler application to alwaysdata hosting.

## Prerequisites

1. An alwaysdata account (free or paid)
2. Your project files ready for upload
3. Basic knowledge of SSH and file management

## Step 1: Prepare Your Application

### 1.1 Update Requirements
Ensure your `requirements.txt` includes all necessary dependencies for production:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Cors==4.0.0
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Werkzeug==3.0.1
python-dotenv==1.0.0
python-dateutil==2.8.2
email-validator==2.1.0.post1
gunicorn==21.2.0
```

### 1.2 Environment Configuration
Create a production-ready `.env` file:

```env
SECRET_KEY=your-super-secret-production-key-here
DATABASE_URL=sqlite:///badminton_scheduler.db
FLASK_ENV=production
FLASK_DEBUG=False
```

## Step 2: Alwaysdata Setup

### 2.1 Account Configuration
1. Log into your alwaysdata admin panel
2. Go to **Web > Sites** and create a new site
3. Choose **Python** as the application type
4. Set the Python version to 3.8+ (recommended: 3.11)

### 2.2 Domain Configuration
- Set your domain/subdomain (e.g., `yourusername.alwaysdata.net` or your custom domain)
- Configure the document root to point to your application directory

## Step 3: File Upload

### 3.1 Upload Methods
You can upload files via:
- **SSH/SFTP**: Most flexible option
- **Web interface**: For smaller files
- **Git**: If you have a repository

### 3.2 Directory Structure on Alwaysdata
```
/home/yourusername/
├── www/
│   └── badminton_scheduler/
│       ├── static/
│       ├── templates/
│       ├── app.py
│       ├── wsgi.py
│       ├── requirements.txt
│       └── ... (all your project files)
```

## Step 4: Python Environment Setup

### 4.1 SSH Access
Connect via SSH:
```bash
ssh yourusername@ssh-yourusername.alwaysdata.net
```

### 4.2 Virtual Environment
```bash
cd ~/www/badminton_scheduler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Database Setup
```bash
# Initialize the database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Or if you have migration scripts
python3 scripts/start_server.py --setup-only
```

## Step 5: WSGI Configuration

### 5.1 Update wsgi.py
Ensure your `wsgi.py` file is properly configured:

```python
import sys
import os

# Add your project directory to Python path
sys.path.insert(0, '/home/yourusername/www/badminton_scheduler')

# Activate virtual environment
activate_this = '/home/yourusername/www/badminton_scheduler/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

from app import app as application

if __name__ == "__main__":
    application.run()
```

### 5.2 Alwaysdata Web Configuration
In your alwaysdata admin panel:
1. Go to **Web > Sites**
2. Edit your site configuration
3. Set **Type** to "Python WSGI"
4. Set **Path** to `/home/yourusername/www/badminton_scheduler/wsgi.py`
5. Set **Working directory** to `/home/yourusername/www/badminton_scheduler`

## Step 6: Static Files Configuration

### 6.1 Static Files Serving
Configure static files in alwaysdata:
1. Go to **Web > Static files**
2. Add a new static files configuration:
   - **URL**: `/static/`
   - **Path**: `/home/yourusername/www/badminton_scheduler/static/`

### 6.2 Frontend Access
Your main frontend will be accessible at:
- `https://yourdomain.com/static/static_frontend.html`

## Step 7: Database Configuration

### 7.1 SQLite (Default)
SQLite works out of the box on alwaysdata. Ensure your database file has proper permissions:

```bash
chmod 664 badminton_scheduler.db
chmod 775 instance/  # if using instance folder
```

### 7.2 PostgreSQL (Optional Upgrade)
For better performance, consider upgrading to PostgreSQL:

1. Create a PostgreSQL database in alwaysdata admin
2. Update your `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@postgresql-yourusername.alwaysdata.net/dbname
   ```
3. Install psycopg2: `pip install psycopg2-binary`

## Step 8: Security Configuration

### 8.1 Environment Variables
Store sensitive data in environment variables:
```bash
# In your shell profile or .bashrc
export SECRET_KEY="your-super-secret-key"
export DATABASE_URL="your-database-url"
```

### 8.2 File Permissions
```bash
chmod 600 .env
chmod 755 static/
chmod 644 static/*
```

## Step 9: Testing and Verification

### 9.1 Test the Application
1. Visit your domain
2. Test user registration and login
3. Test availability management
4. Test admin functions
5. Check all API endpoints

### 9.2 Logs and Debugging
Check logs in alwaysdata admin panel:
- **Logs > HTTP**
- **Logs > Tasks** (for background tasks)

## Step 10: Maintenance and Updates

### 10.1 Regular Updates
```bash
# SSH into your server
cd ~/www/badminton_scheduler
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt --upgrade
```

### 10.2 Database Backups
```bash
# For SQLite
cp badminton_scheduler.db badminton_scheduler_backup_$(date +%Y%m%d).db

# For PostgreSQL
pg_dump your_database > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check Python path in wsgi.py
2. **Database Errors**: Verify database file permissions
3. **Static Files Not Loading**: Check static files configuration
4. **500 Errors**: Check error logs in alwaysdata admin

### Performance Optimization

1. **Enable Gzip**: Configure in alwaysdata admin
2. **Static File Caching**: Set appropriate cache headers
3. **Database Optimization**: Consider PostgreSQL for larger datasets

## Support

- **Alwaysdata Documentation**: https://help.alwaysdata.com/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Project Issues**: Check your application logs and error messages

## Quick Deployment Checklist

- [ ] Upload all project files
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Configure wsgi.py
- [ ] Set up database
- [ ] Configure static files
- [ ] Test application
- [ ] Set up monitoring/backups

Your Badminton Scheduler should now be live on alwaysdata!