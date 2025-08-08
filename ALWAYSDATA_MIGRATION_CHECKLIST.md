# Alwaysdata Migration Checklist for Badminton Scheduler

## ✅ Pre-Migration Checklist

- [x] Alwaysdata account created and verified
- [x] SSH access credentials obtained
- [x] Domain/subdomain configured (if using custom domain) - shaun.alwaysdata.net
- [x] Project files ready for upload
- [x] Database backup created (if migrating existing data)

## 📁 Files Created for Deployment

The following files have been created to help with your alwaysdata deployment:

### Core Deployment Files
- [x] `badminton_scheduler/ALWAYSDATA_DEPLOYMENT.md` - Complete deployment guide
- [x] `badminton_scheduler/README_ALWAYSDATA.md` - Alwaysdata-specific documentation
- [x] `badminton_scheduler/wsgi.py` - Updated WSGI configuration for alwaysdata
- [x] `badminton_scheduler/requirements.txt` - Updated with production dependencies

### Configuration Files
- [x] `badminton_scheduler/.env.production` - Production environment template
- [x] `badminton_scheduler/alwaysdata_config.py` - Alwaysdata-specific configuration

### Management Scripts
- [x] `badminton_scheduler/deploy_to_alwaysdata.py` - Automated deployment script
- [x] `badminton_scheduler/backup_database.py` - Database backup utility
- [x] `badminton_scheduler/monitor_app.py` - Application monitoring script
- [x] `badminton_scheduler/health_check.py` - Health check endpoints

### Utility Files
- [x] `badminton_scheduler/make_executable.bat` - Make scripts executable on Unix

## 🚀 Migration Steps

### Step 1: Prepare Files
- [x] Review all created files
- [x] Update `.env.production` with your specific settings
- [x] Test the application locally one final time

### Step 2: Upload to Alwaysdata
- [ ] Upload all files via SSH/SFTP or web interface
- [ ] Verify all files are uploaded correctly
- [ ] Check file permissions

### Step 3: Run Deployment Script
```bash
ssh username@ssh-username.alwaysdata.net
cd ~/www/badminton_scheduler
python3 deploy_to_alwaysdata.py
```
- [ ] Virtual environment created successfully
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Sample admin user created
- [ ] File permissions set correctly

### Step 4: Configure Alwaysdata Web Interface
- [ ] Site created/configured in Web > Sites
- [ ] Python WSGI type selected
- [ ] Correct path to wsgi.py set
- [ ] Working directory configured
- [ ] Python version set (3.8+)

### Step 5: Configure Static Files
- [ ] Static files configuration added in Web > Static files
- [ ] URL set to `/static/`
- [ ] Path set to correct static directory

### Step 6: Test Deployment
- [ ] Frontend accessible at `https://yourdomain.com/static/static_frontend.html`
- [ ] Health check working at `https://yourdomain.com/health`
- [ ] User registration/login working
- [ ] Availability management working
- [ ] Admin panel accessible
- [ ] API endpoints responding correctly

### Step 7: Set Up Monitoring and Backups
- [ ] Test monitoring script: `python3 monitor_app.py https://yourdomain.com`
- [ ] Create initial backup: `python3 backup_database.py`
- [ ] Set up regular backup schedule
- [ ] Configure monitoring alerts (optional)

## 🔧 Post-Migration Tasks

### Security
- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env file
- [ ] Review file permissions
- [ ] Enable HTTPS (should be automatic on alwaysdata)

### Performance
- [ ] Test application performance
- [ ] Monitor resource usage
- [ ] Consider PostgreSQL upgrade if needed
- [ ] Enable gzip compression in alwaysdata admin

### Documentation
- [ ] Update user documentation with new domain
- [ ] Share access credentials with team members
- [ ] Document any custom configurations

### Monitoring
- [ ] Set up regular health checks
- [ ] Configure log monitoring
- [ ] Set up backup schedule
- [ ] Test disaster recovery procedures

## 🚨 Troubleshooting

If you encounter issues:

1. **Check the deployment guide**: `badminton_scheduler/ALWAYSDATA_DEPLOYMENT.md`
2. **Review logs**: Check alwaysdata admin panel logs
3. **Run health checks**: `python3 monitor_app.py https://yourdomain.com`
4. **Check file permissions**: Ensure correct permissions are set
5. **Verify configuration**: Double-check wsgi.py and .env settings

## 📞 Support Resources

- **Deployment Guide**: `badminton_scheduler/ALWAYSDATA_DEPLOYMENT.md`
- **Alwaysdata Documentation**: https://help.alwaysdata.com/
- **Application Health**: `https://yourdomain.com/health/detailed`

## 🎯 Success Criteria

Your migration is successful when:
- [ ] Application loads without errors
- [ ] All core features work (registration, login, availability, admin)
- [ ] Health checks pass
- [ ] Performance is acceptable
- [ ] Backups are working
- [ ] Monitoring is in place

## 📝 Notes

- Default admin credentials: `admin` / `admin123` (change immediately!)
- Database backups are stored in the `backups/` directory
- Application logs are in `instance/logs/`
- Static files are served directly by alwaysdata for better performance

## 🎉 Congratulations!

Once all items are checked off, your Badminton Scheduler will be successfully migrated and running on alwaysdata!

Your application will be accessible at:
- **Main Application**: `https://yourdomain.com/static/static_frontend.html`
- **API Documentation**: `https://yourdomain.com/api/`
- **Health Status**: `https://yourdomain.com/health`