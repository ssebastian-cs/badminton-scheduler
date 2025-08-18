# Deployment Guide

This guide provides comprehensive instructions for deploying the Badminton Scheduler application in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Deployment Methods](#deployment-methods)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM (1GB+ recommended for production)
- **Storage**: Minimum 1GB free space
- **Network**: Port 5000 available (or configure alternative)

### Required Software

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install python3 python3-pip git

# macOS (with Homebrew)
brew install python3 git

# Windows
# Install Python from python.org
# Install Git from git-scm.com
```

## Environment Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Production Environment Variables
SECRET_KEY=your-very-secure-secret-key-here-change-this
DATABASE_URL=sqlite:///badminton_scheduler_prod.db
FLASK_ENV=production
LOG_LEVEL=INFO
LOG_FILE=logs/badminton_scheduler.log

# Optional: Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Optional: Redis for Rate Limiting
REDIS_URL=redis://localhost:6379/0
```

### 2. Generate Secret Key

```python
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Configuration Files

Ensure proper configuration files exist:

- `config/production.py` - Production settings
- `config/development.py` - Development settings
- `config/testing.py` - Testing settings

## Database Setup

### 1. Initialize Database

```bash
# Create database and tables
python scripts/init_database.py init --config production

# Verify database health
python scripts/init_database.py health
```

### 2. Database Backup Strategy

```bash
# Create backup directory
sudo mkdir -p /var/backups/badminton-scheduler
sudo chown $USER:$USER /var/backups/badminton-scheduler

# Manual backup
cp badminton_scheduler_prod.db /var/backups/badminton-scheduler/backup-$(date +%Y%m%d-%H%M%S).db

# Automated backup (add to crontab)
0 2 * * * /path/to/project/scripts/backup_database.sh
```

## Deployment Methods

### Method 1: Manual Deployment

#### 1. Prepare Environment

```bash
# Clone repository
git clone <repository-url>
cd badminton-scheduler

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Application

```bash
# Set environment variables
export SECRET_KEY="your-secret-key"
export FLASK_ENV="production"
export DATABASE_URL="sqlite:///badminton_scheduler_prod.db"

# Initialize database
python scripts/init_database.py init --config production
```

#### 3. Run Application

```bash
# Start application
python run.py production

# Or use gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Method 2: Docker Deployment

#### 1. Using Docker Compose (Recommended)

```bash
# Navigate to docker directory
cd deploy/docker

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

#### 2. Manual Docker Build

```bash
# Build image
docker build -t badminton-scheduler .

# Run container
docker run -d \
  --name badminton-scheduler \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e FLASK_ENV="production" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  badminton-scheduler
```

### Method 3: Automated Deployment Script

```bash
# Make script executable
chmod +x deploy/deploy.sh

# Deploy to production
./deploy/deploy.sh deploy production

# Check deployment health
./deploy/deploy.sh health

# Rollback if needed
./deploy/deploy.sh rollback
```

## Production Considerations

### 1. Web Server Configuration

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/badminton-scheduler
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Static files
    location /static/ {
        alias /path/to/app/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Enable Nginx Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/badminton-scheduler /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 2. SSL/TLS Configuration

#### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Process Management

#### Using Systemd

Create `/etc/systemd/system/badminton-scheduler.service`:

```ini
[Unit]
Description=Badminton Scheduler Web Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/badminton-scheduler
Environment=PATH=/path/to/badminton-scheduler/venv/bin
Environment=SECRET_KEY=your-secret-key
Environment=FLASK_ENV=production
ExecStart=/path/to/badminton-scheduler/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app('production')"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable badminton-scheduler
sudo systemctl start badminton-scheduler
sudo systemctl status badminton-scheduler
```

### 4. Security Hardening

#### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# iptables (manual)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

#### File Permissions

```bash
# Set proper ownership
sudo chown -R www-data:www-data /path/to/badminton-scheduler

# Set file permissions
find /path/to/badminton-scheduler -type f -exec chmod 644 {} \;
find /path/to/badminton-scheduler -type d -exec chmod 755 {} \;

# Make scripts executable
chmod +x /path/to/badminton-scheduler/run.py
chmod +x /path/to/badminton-scheduler/scripts/*.py
```

## Monitoring and Maintenance

### 1. Health Monitoring

#### Health Check Script

```bash
#!/bin/bash
# scripts/health_check.sh

HEALTH_URL="http://localhost:5000/health"
LOG_FILE="/var/log/badminton-scheduler-health.log"

if curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "$(date): Health check passed" >> $LOG_FILE
else
    echo "$(date): Health check failed" >> $LOG_FILE
    # Send alert (email, Slack, etc.)
    # systemctl restart badminton-scheduler
fi
```

#### Cron Job for Health Checks

```bash
# Add to crontab
*/5 * * * * /path/to/scripts/health_check.sh
```

### 2. Log Management

#### Log Rotation

Create `/etc/logrotate.d/badminton-scheduler`:

```
/path/to/badminton-scheduler/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload badminton-scheduler
    endscript
}
```

### 3. Database Maintenance

#### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/var/backups/badminton-scheduler"
DB_FILE="/path/to/badminton_scheduler_prod.db"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create backup
cp $DB_FILE $BACKUP_DIR/backup-$TIMESTAMP.db

# Compress backup
gzip $BACKUP_DIR/backup-$TIMESTAMP.db

# Remove backups older than 30 days
find $BACKUP_DIR -name "backup-*.db.gz" -mtime +30 -delete

echo "$(date): Database backup completed: backup-$TIMESTAMP.db.gz"
```

### 4. Performance Monitoring

#### Basic Monitoring Commands

```bash
# Check application status
systemctl status badminton-scheduler

# Monitor resource usage
htop
df -h
free -h

# Check application logs
tail -f /path/to/logs/badminton_scheduler.log

# Monitor database size
ls -lh badminton_scheduler_prod.db

# Check network connections
netstat -tlnp | grep :5000
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
journalctl -u badminton-scheduler -f

# Check configuration
python scripts/init_database.py health

# Verify permissions
ls -la /path/to/badminton-scheduler
```

#### 2. Database Issues

```bash
# Reset database
python scripts/init_database.py reset --config production

# Check database integrity
sqlite3 badminton_scheduler_prod.db "PRAGMA integrity_check;"
```

#### 3. Permission Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /path/to/badminton-scheduler

# Fix permissions
chmod -R 755 /path/to/badminton-scheduler
```

#### 4. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
```

### Emergency Procedures

#### 1. Quick Rollback

```bash
# Stop application
sudo systemctl stop badminton-scheduler

# Restore from backup
cp /var/backups/badminton-scheduler/backup-YYYYMMDD-HHMMSS.db badminton_scheduler_prod.db

# Start application
sudo systemctl start badminton-scheduler
```

#### 2. Emergency Maintenance Mode

```bash
# Create maintenance page
echo "System under maintenance" > /var/www/html/maintenance.html

# Redirect traffic in Nginx
# Add to server block:
# return 503;
# error_page 503 /maintenance.html;
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Run in SQLite
PRAGMA optimize;
VACUUM;
ANALYZE;
```

#### 2. Application Tuning

```bash
# Increase Gunicorn workers
gunicorn -w 8 -b 127.0.0.1:5000 "app:create_app('production')"

# Enable gzip compression in Nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## Support and Documentation

- **Application Health**: Visit `/health` endpoint
- **Logs Location**: `/path/to/logs/badminton_scheduler.log`
- **Configuration**: Check `config/production.py`
- **Database**: SQLite file location in `DATABASE_URL`

For additional support, refer to the main README.md file and application documentation.