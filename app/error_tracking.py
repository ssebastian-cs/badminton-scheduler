"""
Enhanced error tracking and reporting system for the Badminton Scheduler application.
Provides comprehensive error monitoring, metrics collection, and reporting capabilities.
"""

import logging
import json
import os
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from flask import request, current_app
from werkzeug.exceptions import HTTPException


class ErrorMetrics:
    """Thread-safe error metrics collector."""
    
    def __init__(self, max_entries=1000):
        self.max_entries = max_entries
        self.lock = threading.Lock()
        self.error_counts = defaultdict(int)
        self.error_history = deque(maxlen=max_entries)
        self.hourly_stats = defaultdict(lambda: defaultdict(int))
        self.user_errors = defaultdict(int)
        self.endpoint_errors = defaultdict(int)
        
    def record_error(self, error_type: str, error_message: str, 
                    user_id: Optional[int] = None, endpoint: Optional[str] = None,
                    severity: str = 'ERROR', **kwargs):
        """Record an error occurrence with metadata."""
        with self.lock:
            timestamp = datetime.now(timezone.utc)
            hour_key = timestamp.strftime('%Y-%m-%d-%H')
            
            # Update counters
            self.error_counts[error_type] += 1
            self.hourly_stats[hour_key][error_type] += 1
            
            if user_id:
                self.user_errors[user_id] += 1
            if endpoint:
                self.endpoint_errors[endpoint] += 1
            
            # Store error details
            error_record = {
                'timestamp': timestamp.isoformat(),
                'error_type': error_type,
                'message': error_message,
                'severity': severity,
                'user_id': user_id,
                'endpoint': endpoint,
                **kwargs
            }
            self.error_history.append(error_record)
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        with self.lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            recent_errors = [
                error for error in self.error_history
                if datetime.fromisoformat(error['timestamp']) > cutoff_time
            ]
            
            summary = {
                'total_errors': len(recent_errors),
                'error_types': defaultdict(int),
                'severity_breakdown': defaultdict(int),
                'top_endpoints': defaultdict(int),
                'top_users': defaultdict(int),
                'hourly_trend': []
            }
            
            for error in recent_errors:
                summary['error_types'][error['error_type']] += 1
                summary['severity_breakdown'][error['severity']] += 1
                if error.get('endpoint'):
                    summary['top_endpoints'][error['endpoint']] += 1
                if error.get('user_id'):
                    summary['top_users'][error['user_id']] += 1
            
            # Convert defaultdicts to regular dicts for JSON serialization
            summary['error_types'] = dict(summary['error_types'])
            summary['severity_breakdown'] = dict(summary['severity_breakdown'])
            summary['top_endpoints'] = dict(summary['top_endpoints'])
            summary['top_users'] = dict(summary['top_users'])
            
            return summary
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the most recent errors."""
        with self.lock:
            return list(self.error_history)[-limit:]
    
    def clear_old_data(self, hours: int = 168):  # Default: 1 week
        """Clear error data older than specified hours."""
        with self.lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Clear old error history
            self.error_history = deque([
                error for error in self.error_history
                if datetime.fromisoformat(error['timestamp']) > cutoff_time
            ], maxlen=self.max_entries)
            
            # Clear old hourly stats
            cutoff_hour = cutoff_time.strftime('%Y-%m-%d-%H')
            old_hours = [
                hour for hour in self.hourly_stats.keys()
                if hour < cutoff_hour
            ]
            for hour in old_hours:
                del self.hourly_stats[hour]


class ErrorTracker:
    """Main error tracking system with reporting capabilities."""
    
    def __init__(self, app=None):
        self.app = app
        self.metrics = ErrorMetrics()
        self.logger = logging.getLogger('error_tracker')
        self.alert_thresholds = {
            'error_rate_per_hour': 50,
            'critical_errors_per_hour': 5,
            'database_errors_per_hour': 10
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error tracking for the Flask app."""
        self.app = app
        
        # Set up error tracking logger
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/error_tracking.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Register cleanup task (in a real app, this would be a background task)
        with app.app_context():
            self._setup_cleanup_task()
    
    def _setup_cleanup_task(self):
        """Set up periodic cleanup of old error data."""
        # In a production environment, this would be handled by a background task
        # For now, we'll just clean up on app startup
        self.metrics.clear_old_data()
    
    def track_error(self, error: Exception, error_type: Optional[str] = None,
                   severity: str = 'ERROR', **kwargs):
        """Track an error with full context."""
        try:
            # Determine error type
            if not error_type:
                error_type = type(error).__name__
            
            # Get request context
            request_info = {}
            user_id = None
            endpoint = None
            
            try:
                if request:
                    request_info = {
                        'method': request.method,
                        'url': request.url,
                        'endpoint': request.endpoint,
                        'remote_addr': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', 'Unknown')
                    }
                    endpoint = request.endpoint
                    
                    # Try to get user ID (avoid circular imports)
                    from flask_login import current_user
                    if hasattr(current_user, 'id') and current_user.is_authenticated:
                        user_id = current_user.id
            except RuntimeError:
                # Outside request context
                pass
            
            # Record the error
            self.metrics.record_error(
                error_type=error_type,
                error_message=str(error),
                user_id=user_id,
                endpoint=endpoint,
                severity=severity,
                request_info=request_info,
                **kwargs
            )
            
            # Log the error
            log_message = f"Error tracked: {error_type} - {str(error)}"
            if user_id:
                log_message += f" (User: {user_id})"
            if endpoint:
                log_message += f" (Endpoint: {endpoint})"
            
            self.logger.log(getattr(logging, severity), log_message)
            
            # Check for alert conditions
            self._check_alert_conditions()
            
        except Exception as tracking_error:
            # Don't let error tracking itself cause issues
            self.logger.error(f"Error in error tracking: {tracking_error}")
    
    def _check_alert_conditions(self):
        """Check if any alert conditions are met."""
        try:
            summary = self.metrics.get_error_summary(hours=1)
            
            # Check error rate threshold
            if summary['total_errors'] > self.alert_thresholds['error_rate_per_hour']:
                self._send_alert(
                    'HIGH_ERROR_RATE',
                    f"High error rate detected: {summary['total_errors']} errors in the last hour"
                )
            
            # Check critical errors
            critical_count = summary['severity_breakdown'].get('CRITICAL', 0)
            if critical_count > self.alert_thresholds['critical_errors_per_hour']:
                self._send_alert(
                    'CRITICAL_ERRORS',
                    f"Critical errors detected: {critical_count} critical errors in the last hour"
                )
            
            # Check database errors
            db_errors = sum(
                count for error_type, count in summary['error_types'].items()
                if 'database' in error_type.lower() or 'sql' in error_type.lower()
            )
            if db_errors > self.alert_thresholds['database_errors_per_hour']:
                self._send_alert(
                    'DATABASE_ERRORS',
                    f"Database errors detected: {db_errors} database errors in the last hour"
                )
                
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    def _send_alert(self, alert_type: str, message: str):
        """Send an alert (log for now, could be extended to email/Slack/etc.)."""
        alert_message = f"ALERT [{alert_type}]: {message}"
        self.logger.critical(alert_message)
        
        # In a production environment, this could send emails, Slack messages, etc.
        # For now, we'll just log it prominently
        if self.app:
            self.app.logger.critical(alert_message)
    
    def get_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a comprehensive error report."""
        summary = self.metrics.get_error_summary(hours)
        recent_errors = self.metrics.get_recent_errors(20)
        
        return {
            'report_generated': datetime.now(timezone.utc).isoformat(),
            'time_period_hours': hours,
            'summary': summary,
            'recent_errors': recent_errors,
            'alert_thresholds': self.alert_thresholds
        }
    
    def export_error_data(self, hours: int = 24) -> str:
        """Export error data as JSON string."""
        report = self.get_error_report(hours)
        return json.dumps(report, indent=2, default=str)


# Global error tracker instance
error_tracker = ErrorTracker()


def track_error(error: Exception, error_type: Optional[str] = None, 
               severity: str = 'ERROR', **kwargs):
    """Convenience function to track errors."""
    error_tracker.track_error(error, error_type, severity, **kwargs)


def get_error_summary(hours: int = 24) -> Dict[str, Any]:
    """Convenience function to get error summary."""
    return error_tracker.metrics.get_error_summary(hours)


def get_error_report(hours: int = 24) -> Dict[str, Any]:
    """Convenience function to get error report."""
    return error_tracker.get_error_report(hours)