# Badminton Scheduler - Alwaysdata Deployment

This is a comprehensive guide for deploying and managing the Badminton Scheduler application on alwaysdata hosting platform.

## 🚀 Quick Deployment

### Prerequisites
- Alwaysdata account (free or paid)
- SSH access to your alwaysdata account
- Basic knowledge of command line operations

### 1. Upload Files
Upload all project files to your alwaysdata account:
```bash
# Via SSH/SFTP
scp -r badminton_scheduler/ username@ssh-username.alwaysdata.net:~/www/
```

### 2. Run Deployment Script
```bash
ssh username@ssh-username.alwaysdata.net
cd ~/www/badminton_scheduler
python3 deploy_to_alwaysdata.py
```

### 3. Configure Alwaysdata Web Interface
1. Go to **Web > Sites** in your alwaysdata admin panel
2. Create/edit your site:
   - **Type**: Python WSGI
   - **Path**: `/home/username/www/badminton_scheduler/wsgi.py`
   - **Working directory**: `/home/username/www/badminton_scheduler`
   - **Python version**: 3.8+ (recommended: 3.11)

### 4. Configure Static Files
1. Go to **Web > Static files**
2. Add configuration:
   - **URL**: `/static/`
   - **Path**: `/home/username/www/badminton_scheduler/static/`

### 5. Access Your Application
- **Frontend**: `https://yourdomain.com/static/static_frontend.html`
- **API**: `https://yourdomain.com/api/`
- **Health Check**: `https://yourdomain.com/health`

## 📁 File Structure on Alwaysdata

```
/home/username/www/badminton_scheduler/
├── venv/                          # Python virtual environment
├── static/                        # Static files (CSS, JS, HTML)
├── instance/                      # Instance-specific files
├── backups/                       # Database backups
├── logs/                          # Application logs
├── wsgi.py                        # WSGI entry point
├── run.py                         # Main application
├── requirements.txt               # Python dependencies
├── .env                           # Environment configuration
├── deploy_to_alwaysdata.py        # Deployment script
├── backup_database.py             # Backup script
├── monitor_app.py                 # Monitoring script
└── badminton_scheduler.db         # SQLite database
```

## 🔧 Configuration

### Environment Variables (.env)
```env
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=sqlite:///badminton_scheduler.db
FLASK_ENV=production
FLASK_DEBUG=False
```

### Database Options

#### SQLite (Default)
- **Pros**: Simple, no additional setup required
- **Cons**: Limited concurrent access
- **Best for**: Small to medium user bases

#### PostgreSQL (Recommended for Production)
1. Create PostgreSQL database in alwaysdata admin
2. Update `.env`:
   ```env
   DATABASE_URL=postgresql://username:password@postgresql-username.alwaysdata.net/dbname
   ```

## 🛠️ Management Scripts

### Deployment Script
```bash
python3 deploy_to_alwaysdata.py
```
- Sets up virtual environment
- Installs dependencies
- Initializes database
- Sets file permissions
- Creates sample admin user

### Database Backup
```bash
python3 backup_database.py
```
- Creates timestamped database backups
- Exports data to JSON format
- Cleans up old backup files

### Application Monitoring
```bash
python3 monitor_app.py https://yourdomain.com
```
- Checks application health
- Tests API endpoints
- Verifies frontend access
- Can send email notifications

## 📊 Monitoring and Maintenance

### Health Check Endpoints
- **Basic**: `/health` - Simple status check
- **Detailed**: `/health/detailed` - Database and system checks
- **Statistics**: `/health/stats` - Application usage statistics

### Log Files
Application logs are stored in:
- `instance/logs/badminton_scheduler.log`

### Regular Maintenance Tasks

#### Daily
```bash
# Check application health
python3 monitor_app.py https://yourdomain.com

# Create database backup
python3 backup_database.py
```

#### Weekly
```bash
# Update dependencies (if needed)
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Clean up old logs
find instance/logs/ -name "*.log.*" -mtime +30 -delete
```

#### Monthly
```bash
# Review and clean up old backups
ls -la backups/
# Remove backups older than 3 months manually if needed
```

## 🔒 Security Best Practices

### File Permissions
```bash
chmod 600 .env                    # Environment file
chmod 664 badminton_scheduler.db  # Database file
chmod 755 static/                 # Static directory
chmod 644 static/*                # Static files
```

### Environment Security
- Use strong, unique `SECRET_KEY`
- Keep `.env` file secure and never commit to version control
- Regularly update dependencies
- Monitor access logs

### Database Security
- Regular backups
- Consider PostgreSQL for better security features
- Monitor for unusual activity

## 🚨 Troubleshooting

### Common Issues

#### 500 Internal Server Error
1. Check error logs in alwaysdata admin panel
2. Verify WSGI configuration
3. Check file permissions
4. Ensure virtual environment is properly set up

#### Database Connection Errors
1. Verify database file exists and has correct permissions
2. Check `DATABASE_URL` in `.env` file
3. Ensure database directory is writable

#### Static Files Not Loading
1. Verify static files configuration in alwaysdata admin
2. Check file permissions in static directory
3. Ensure static files exist

#### Import Errors
1. Verify virtual environment is activated
2. Check Python path in `wsgi.py`
3. Ensure all dependencies are installed

### Debug Mode
For debugging (temporarily):
1. Set `FLASK_DEBUG=True` in `.env`
2. Restart the application
3. **Remember to set back to `False` for production**

### Getting Help
1. Check application logs: `instance/logs/badminton_scheduler.log`
2. Run health checks: `python3 monitor_app.py`
3. Check alwaysdata documentation: https://help.alwaysdata.com/
4. Contact alwaysdata support if needed

## 📈 Performance Optimization

### Database Optimization
- Consider PostgreSQL for better performance
- Regular database maintenance
- Monitor query performance

### Static Files
- Enable gzip compression in alwaysdata admin
- Set appropriate cache headers
- Optimize images and CSS/JS files

### Application Performance
- Monitor response times
- Use database indexing effectively
- Consider caching for frequently accessed data

## 🔄 Updates and Deployment

### Updating the Application
1. Upload new files via SSH/SFTP
2. Run deployment script:
   ```bash
   python3 deploy_to_alwaysdata.py
   ```
3. Test the application
4. Monitor for any issues

### Rolling Back
1. Restore from database backup if needed:
   ```bash
   cp backups/badminton_scheduler_backup_YYYYMMDD_HHMMSS.db badminton_scheduler.db
   ```
2. Restore previous application files
3. Restart the application

## 📞 Support and Resources

- **Alwaysdata Documentation**: https://help.alwaysdata.com/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Application Health Check**: `https://yourdomain.com/health`
- **Admin Panel**: Login with admin credentials created during setup

## 🎯 Next Steps After Deployment

1. **Test thoroughly**: Verify all functionality works
2. **Set up monitoring**: Configure regular health checks
3. **Create backups**: Set up automated backup schedule
4. **Security review**: Ensure all security measures are in place
5. **Performance monitoring**: Monitor response times and resource usage
6. **User training**: Provide access credentials to users
7. **Documentation**: Update any user-facing documentation with your domain

Your Badminton Scheduler is now ready for production use on alwaysdata! 🏸