@echo off
REM Make Python scripts executable on Unix systems
REM Run this after uploading to alwaysdata

echo Making Python scripts executable...
chmod +x deploy_to_alwaysdata.py
chmod +x backup_database.py  
chmod +x monitor_app.py

echo Done! Scripts are now executable.
echo.
echo Next steps:
echo 1. Upload all files to your alwaysdata account
echo 2. SSH into your alwaysdata account
echo 3. Run: python3 deploy_to_alwaysdata.py
echo 4. Configure your web site in alwaysdata admin panel