"""
Health check endpoints for monitoring the application on alwaysdata.
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os
import sqlite3

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check including database connectivity."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Check database connectivity
    try:
        from models import User
        user_count = User.query.count()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'user_count': user_count
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check file system
    try:
        db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if db_path and os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            health_status['checks']['filesystem'] = {
                'status': 'healthy',
                'database_size_bytes': db_size
            }
        else:
            health_status['checks']['filesystem'] = {
                'status': 'healthy',
                'note': 'Using in-memory or remote database'
            }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['filesystem'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check static files
    try:
        static_folder = current_app.static_folder
        if static_folder and os.path.exists(static_folder):
            static_files = len([f for f in os.listdir(static_folder) if os.path.isfile(os.path.join(static_folder, f))])
            health_status['checks']['static_files'] = {
                'status': 'healthy',
                'file_count': static_files
            }
        else:
            health_status['checks']['static_files'] = {
                'status': 'warning',
                'note': 'Static folder not found'
            }
    except Exception as e:
        health_status['checks']['static_files'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    return jsonify(health_status)

@health_bp.route('/health/stats')
def stats():
    """Application statistics."""
    try:
        from models import User, Availability, Feedback
        
        stats_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'total_users': User.query.count(),
                'admin_users': User.query.filter_by(is_admin=True).count(),
                'total_availability_entries': Availability.query.count(),
                'total_feedback_entries': Feedback.query.count(),
            }
        }
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        stats_data['recent_activity'] = {
            'new_users_last_7_days': User.query.filter(User.created_at >= week_ago).count(),
            'availability_updates_last_7_days': Availability.query.filter(Availability.updated_at >= week_ago).count(),
            'feedback_last_7_days': Feedback.query.filter(Feedback.created_at >= week_ago).count(),
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve statistics',
            'message': str(e)
        }), 500