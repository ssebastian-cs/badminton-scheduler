# Badminton Scheduler - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Badminton Scheduler application in both development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 512MB RAM (2GB recommended for production)
- **Storage**: Minimum 100MB free space
- **Network**: Internet access for package installation

### Required Software

```bash
# Python and pip (usually included with Python)
python3 --version
pip3 --version

# Optional but recommended for production
# Web server (nginx or Apache)
# Process manager (systemd, supervisor, or PM2)
# SSL certificate (Let's Encrypt recommended)
```

## Development Deployment

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd badminton-scheduler
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   # Initialize database and create tables
   python init_database.py init-db
   
   # Create admin user
   python init_database.py create-admin
   ```

3. **Run Application**
   ```bash
   # Development server
   python run.py
   
   # Or using Flask CLI
   flask run --debug
   ```

4. **Access Application**
   - Open browser to `http://localhost:5000`
   - Login with admin credentials created in step 2

### Development Configuration

Create a `.env` file in the project root:

```env
# Development Environment
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-development-secret-key
DATABASE_URL=sqlite:///badminton_scheduler_dev.db
```

## Production Deployment

### Automated Deployment

Use the comprehensive deployment script:

```bash
# Run full deployment validation
python deploy.py full-deployment-test

# Or run individual steps
python deploy.py check-config --env production
python deploy.py setup-production
python deploy.py run-health-check
```

### Manual Production Setup

1. **Environment Setup**
   ```bash
   # Create production directories
   mkdir -p logs instance backups
   
   # Set proper permissions
   chmod 755 logs instance
   chmod 700 backups
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Initialize production database
   FLASK_ENV=production python init_database.py init-db
   
   # Create admin user
   FLASK_ENV=production python init_database.py create-admin
   
   # Run migrations if needed
   FLASK_ENV=production flask db upgrade
   ```

3. **Configuration**
   
   Create production `.env` file:
   ```env
   # Production Environment
   FLASK_ENV=production
   FLASK_APP=run.py
   SECRET_KEY=your-secure-production-secret-key-here
   DATABASE_URL=sqlite:///instance/badminton_scheduler.db
   
   # Optional: External Database
   # DATABASE_URL=postgresql://user:password@localhost/badminton_scheduler
   
   # Security Settings
   SESSION_COOKIE_SECURE=True
   WTF_CSRF_SSL_STRICT=True
   ```

4. **Web Server Configuration**

   **Nginx Configuration** (`/etc/nginx/sites-available/badminton-scheduler`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location /static {
           alias /path/to/badminton-scheduler/app/static;
           expires 1y;
       }
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Process Management**

   **Systemd Service** (`/etc/systemd/system/badminton-scheduler.service`):
   ```ini
   [Unit]
   Description=Badminton Scheduler Web Application
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/badminton-scheduler
   Environment=PATH=/path/to/badminton-scheduler/venv/bin
   EnvironmentFile=/path/to/badminton-scheduler/.env
   ExecStart=/path/to/badminton-scheduler/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start the service:
   ```bash
   sudo systemctl enable badminton-scheduler
   sudo systemctl start badminton-scheduler
   sudo systemctl status badminton-scheduler
   ```

## Database Setup

### SQLite (Default)

SQLite is used by default and requires no additional setup:

```bash
# Development
DATABASE_URL=sqlite:///badminton_scheduler_dev.db

# Production
DATABASE_URL=sqlite:///instance/badminton_scheduler.db
```

### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql-server postgresql-contrib
   ```

2. **Create Database**
   ```bash
   sudo -u postgres createuser badminton_user
   sudo -u postgres createdb badminton_scheduler
   sudo -u postgres psql -c "ALTER USER badminton_user PASSWORD 'secure_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE badminton_scheduler TO badminton_user;"
   ```

3. **Update Configuration**
   ```env
   DATABASE_URL=postgresql://badminton_user:secure_password@localhost/badminton_scheduler
   ```

### MySQL/MariaDB

1. **Install MySQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mysql-server
   
   # CentOS/RHEL
   sudo yum install mysql-server
   ```

2. **Create Database**
   ```sql
   CREATE DATABASE badminton_scheduler;
   CREATE USER 'badminton_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON badminton_scheduler.* TO 'badminton_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Update Configuration**
   ```env
   DATABASE_URL=mysql://badminton_user:secure_password@localhost/badminton_scheduler
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Environment mode | `development` | Yes |
| `SECRET_KEY` | Security key for sessions | None | Yes |
| `DATABASE_URL` | Database connection string | SQLite | Yes |
| `FLASK_APP` | Application entry point | `run.py` | No |

### Security Configuration

For production, ensure these security settings:

```env
# Strong secret key (generate with: python deploy.py generate-secret-key)
SECRET_KEY=your-32-character-random-string-here

# Secure cookies (requires HTTPS)
SESSION_COOKIE_SECURE=True
WTF_CSRF_SSL_STRICT=True

# Database security
DATABASE_URL=postgresql://user:password@localhost/db_name
```

### Application Configuration

Key configuration options in `app/config.py`:

- **Session timeout**: Default 8 hours (development), 4 hours (production)
- **CSRF token lifetime**: 1 hour (development), 30 minutes (production)
- **File upload limits**: 1MB maximum
- **Rate limiting**: 100 requests per hour per IP

## Testing

### Pre-Deployment Testing

Run comprehensive tests before deployment:

```bash
# Full test suite
python run_tests.py

# Integration tests
python test_final_integration.py

# Deployment validation
python deploy.py full-deployment-test
```

### Test Categories

1. **Unit Tests**: Model, form, and utility function tests
2. **Integration Tests**: Database and route integration
3. **Functional Tests**: Complete user workflows
4. **Security Tests**: Authentication and authorization
5. **Performance Tests**: Load and stress testing

### Continuous Testing

Set up automated testing in your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Test and Deploy
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py
```

## Monitoring

### Application Monitoring

1. **Health Checks**
   ```bash
   # Manual health check
   python deploy.py run-health-check
   
   # Automated monitoring endpoint
   curl http://your-domain.com/health
   ```

2. **Log Monitoring**
   ```bash
   # Application logs
   tail -f logs/application.log
   
   # Error logs
   tail -f logs/errors.log
   
   # Security logs
   tail -f logs/security.log
   ```

3. **Database Monitoring**
   ```bash
   # Check database status
   python init_database.py check-db
   
   # Monitor database size (SQLite)
   ls -lh instance/badminton_scheduler.db
   ```

### Performance Monitoring

Monitor key metrics:

- **Response time**: Average < 200ms
- **Memory usage**: < 100MB per worker
- **Database connections**: Monitor connection pool
- **Error rate**: < 1% of requests

### Alerting

Set up alerts for:

- Application downtime
- High error rates
- Database connection failures
- Disk space usage > 80%
- Memory usage > 80%

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database file permissions
   ls -la instance/
   
   # Test database connection
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.engine.connect()"
   ```

2. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"
   
   # Test critical imports
   python -c "from app import create_app; print('OK')"
   ```

3. **Permission Errors**
   ```bash
   # Fix file permissions
   chmod 644 *.py
   chmod 755 logs/ instance/
   chmod 600 .env
   ```

4. **Port Already in Use**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   
   # Kill process if needed
   kill -9 <PID>
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with debug output
python run.py
```

### Log Analysis

Check logs for issues:

```bash
# Recent errors
grep -i error logs/application.log | tail -20

# Security events
grep -i "security" logs/security.log | tail -10

# Database issues
grep -i "database" logs/application.log | tail -10
```

### Performance Issues

1. **Slow Database Queries**
   - Enable SQL query logging in development
   - Add database indexes if needed
   - Consider connection pooling

2. **High Memory Usage**
   - Monitor with `htop` or `ps`
   - Check for memory leaks
   - Adjust worker processes

3. **Slow Response Times**
   - Enable profiling in development
   - Optimize database queries
   - Add caching if needed

## Backup and Recovery

### Database Backup

```bash
# Create backup
python deploy.py backup-database

# Automated daily backup (crontab)
0 2 * * * /path/to/badminton-scheduler/deploy.py backup-database
```

### Application Backup

```bash
# Full application backup
tar -czf badminton-scheduler-backup-$(date +%Y%m%d).tar.gz \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=logs/* \
    /path/to/badminton-scheduler/
```

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop application
   sudo systemctl stop badminton-scheduler
   
   # Restore database
   cp backups/database_backup_YYYYMMDD_HHMMSS.db instance/badminton_scheduler.db
   
   # Start application
   sudo systemctl start badminton-scheduler
   ```

2. **Full Application Recovery**
   ```bash
   # Extract backup
   tar -xzf badminton-scheduler-backup-YYYYMMDD.tar.gz
   
   # Restore configuration
   cp .env.backup .env
   
   # Restart services
   sudo systemctl restart badminton-scheduler
   sudo systemctl restart nginx
   ```

## Security Considerations

### Production Security Checklist

- [ ] Strong secret key generated and set
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database credentials secured
- [ ] File permissions properly set
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Access logs monitored
- [ ] Firewall configured

### Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip audit
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review application logs
   - Check disk space usage
   - Verify backup integrity

2. **Monthly**
   - Update dependencies
   - Review security logs
   - Performance analysis

3. **Quarterly**
   - Security audit
   - Disaster recovery test
   - Documentation updates

### Getting Help

1. **Check logs first**: Most issues are logged
2. **Run health checks**: Use built-in diagnostic tools
3. **Test in development**: Reproduce issues locally
4. **Check documentation**: Review this guide and code comments

---

## Quick Reference

### Essential Commands

```bash
# Development
python run.py                          # Start development server
python init_database.py init-db        # Initialize database
python run_tests.py                    # Run test suite

# Production
python deploy.py full-deployment-test  # Validate deployment
python deploy.py run-health-check      # Health check
python deploy.py backup-database       # Create backup

# Maintenance
python init_database.py check-db       # Check database
tail -f logs/application.log           # Monitor logs
sudo systemctl status badminton-scheduler  # Check service
```

### Configuration Files

- `.env` - Environment variables
- `app/config.py` - Application configuration
- `requirements.txt` - Python dependencies
- `nginx.conf` - Web server configuration
- `badminton-scheduler.service` - Systemd service

This deployment guide provides comprehensive instructions for successfully deploying and maintaining the Badminton Scheduler application in any environment.