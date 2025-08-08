#!/usr/bin/env python3
"""
Simple monitoring script for Badminton Scheduler on Alwaysdata
Checks application health and sends alerts if needed.
"""

import requests
import json
import os
import sys
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AppMonitor:
    def __init__(self, base_url, notification_email=None):
        self.base_url = base_url.rstrip('/')
        self.notification_email = notification_email
        self.issues = []
    
    def check_health_endpoint(self):
        """Check the basic health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    print("✅ Health endpoint: OK")
                    return True
                else:
                    self.issues.append(f"Health endpoint returned unhealthy status: {data}")
                    print("❌ Health endpoint: UNHEALTHY")
                    return False
            else:
                self.issues.append(f"Health endpoint returned status code: {response.status_code}")
                print(f"❌ Health endpoint: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.issues.append(f"Health endpoint error: {str(e)}")
            print(f"❌ Health endpoint: ERROR - {str(e)}")
            return False
    
    def check_detailed_health(self):
        """Check the detailed health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=15)
            if response.status_code == 200:
                data = response.json()
                overall_status = data.get('status')
                checks = data.get('checks', {})
                
                print(f"🔍 Detailed health check: {overall_status.upper()}")
                
                for check_name, check_data in checks.items():
                    status = check_data.get('status')
                    if status == 'healthy':
                        print(f"  ✅ {check_name}: OK")
                    elif status == 'warning':
                        print(f"  ⚠️  {check_name}: WARNING - {check_data.get('note', 'No details')}")
                    else:
                        print(f"  ❌ {check_name}: FAILED - {check_data.get('error', 'No details')}")
                        self.issues.append(f"{check_name} check failed: {check_data.get('error')}")
                
                return overall_status == 'healthy'
            else:
                self.issues.append(f"Detailed health endpoint returned status code: {response.status_code}")
                print(f"❌ Detailed health endpoint: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.issues.append(f"Detailed health endpoint error: {str(e)}")
            print(f"❌ Detailed health endpoint: ERROR - {str(e)}")
            return False
    
    def check_frontend_access(self):
        """Check if the frontend is accessible."""
        try:
            response = requests.get(f"{self.base_url}/static/static_frontend.html", timeout=10)
            if response.status_code == 200:
                if 'Badminton Scheduler' in response.text:
                    print("✅ Frontend: OK")
                    return True
                else:
                    self.issues.append("Frontend loaded but doesn't contain expected content")
                    print("❌ Frontend: Content issue")
                    return False
            else:
                self.issues.append(f"Frontend returned status code: {response.status_code}")
                print(f"❌ Frontend: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.issues.append(f"Frontend access error: {str(e)}")
            print(f"❌ Frontend: ERROR - {str(e)}")
            return False
    
    def check_api_endpoints(self):
        """Check critical API endpoints."""
        endpoints_to_check = [
            '/api/availability',
            '/api/feedback',
        ]
        
        all_good = True
        
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                # We expect 401 (unauthorized) for protected endpoints without login
                if response.status_code in [200, 401]:
                    print(f"✅ API {endpoint}: OK")
                else:
                    self.issues.append(f"API {endpoint} returned unexpected status: {response.status_code}")
                    print(f"❌ API {endpoint}: HTTP {response.status_code}")
                    all_good = False
            except Exception as e:
                self.issues.append(f"API {endpoint} error: {str(e)}")
                print(f"❌ API {endpoint}: ERROR - {str(e)}")
                all_good = False
        
        return all_good
    
    def send_notification(self):
        """Send notification email if there are issues."""
        if not self.notification_email or not self.issues:
            return
        
        try:
            # This is a basic example - you'll need to configure SMTP settings
            subject = f"Badminton Scheduler Alert - {len(self.issues)} Issues Detected"
            body = f"""
Badminton Scheduler Monitoring Alert

Timestamp: {datetime.now().isoformat()}
Application URL: {self.base_url}

Issues Detected:
{chr(10).join(f"- {issue}" for issue in self.issues)}

Please check the application and resolve these issues.
"""
            
            print(f"📧 Would send notification email to {self.notification_email}")
            print(f"   Subject: {subject}")
            print(f"   Issues: {len(self.issues)}")
            
            # Uncomment and configure the following to actually send emails:
            # msg = MIMEText(body)
            # msg['Subject'] = subject
            # msg['From'] = 'monitor@yourdomain.com'
            # msg['To'] = self.notification_email
            # 
            # smtp_server = smtplib.SMTP('smtp.alwaysdata.com', 587)
            # smtp_server.starttls()
            # smtp_server.login('your-email@yourdomain.com', 'your-password')
            # smtp_server.send_message(msg)
            # smtp_server.quit()
            
        except Exception as e:
            print(f"❌ Failed to send notification: {str(e)}")
    
    def run_all_checks(self):
        """Run all monitoring checks."""
        print(f"🔍 Starting monitoring checks for {self.base_url}")
        print("=" * 60)
        
        checks = [
            ("Basic Health Check", self.check_health_endpoint),
            ("Detailed Health Check", self.check_detailed_health),
            ("Frontend Access", self.check_frontend_access),
            ("API Endpoints", self.check_api_endpoints),
        ]
        
        results = []
        
        for check_name, check_function in checks:
            print(f"\n📋 {check_name}:")
            result = check_function()
            results.append((check_name, result))
        
        print("\n" + "=" * 60)
        print("📊 MONITORING SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for check_name, result in results:
            status = "PASS" if result else "FAIL"
            icon = "✅" if result else "❌"
            print(f"{icon} {check_name}: {status}")
            if not result:
                all_passed = False
        
        if self.issues:
            print(f"\n⚠️  Total Issues: {len(self.issues)}")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if not all_passed:
            self.send_notification()
            print(f"\n❌ Monitoring completed with {len(self.issues)} issues")
            return False
        else:
            print(f"\n🎉 All checks passed! Application is healthy.")
            return True

def main():
    """Main monitoring function."""
    # Configuration
    base_url = os.environ.get('APP_URL', 'https://yourdomain.alwaysdata.net')
    notification_email = os.environ.get('NOTIFICATION_EMAIL')
    
    # Allow URL to be passed as command line argument
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Create monitor instance
    monitor = AppMonitor(base_url, notification_email)
    
    # Run checks
    success = monitor.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()