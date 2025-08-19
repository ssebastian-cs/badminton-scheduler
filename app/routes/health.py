"""
Health Check and Database Performance Monitoring Routes

This module provides health check endpoints and database performance
monitoring interfaces for the badminton scheduler application.
"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from datetime import datetime, timedelta
import time
import os

from ..routes.auth import admin_required
from ..db_performance import get_performance_metrics, db_optimizer, performance_monitor
from ..db_logging import get_db_performance_logger
from .. import db
from ..models import User, Availability, Comment

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Basic application health check endpoint."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
        db_response_time = None
        
        # Measure database response time
        start_time = time.time()
        user_count = User.query.count()
        db_response_time = time.time() - start_time
        
    except Exception as e:
        db_status = 'unhealthy'
        db_response_time = None
        user_count = None
    
    health_data = {
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'database': {
            'status': db_status,
            'response_time_ms': round(db_response_time * 1000, 2) if db_response_time else None,
            'user_count': user_count
        },
        'uptime': _get_uptime()
    }
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code


@health_bp.route('/health/detailed')
@login_required
@admin_required
def detailed_health_check():
    """Detailed health check with performance metrics (admin only)."""
    try:
        # Basic database tests
        start_time = time.time()
        
        # Test various database operations
        user_count = User.query.count()
        availability_count = Availability.query.count()
        comment_count = Comment.query.count()
        
        # Test a more complex query
        recent_availability = Availability.query.filter(
            Availability.date >= datetime.now().date()
        ).count()
        
        db_response_time = time.time() - start_time
        
        # Get performance metrics
        performance_data = get_performance_metrics()
        
        # Get system information
        system_info = _get_system_info()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'status': 'healthy',
                'response_time_ms': round(db_response_time * 1000, 2),
                'counts': {
                    'users': user_count,
                    'availability_entries': availability_count,
                    'comments': comment_count,
                    'future_availability': recent_availability
                }
            },
            'performance': performance_data,
            'system': system_info
        }
        
    except Exception as e:
        health_data = {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'database': {'status': 'unhealthy'}
        }
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code


@health_bp.route('/health/performance')
@login_required
@admin_required
def performance_metrics():
    """Get current database performance metrics (admin only)."""
    try:
        metrics = get_performance_metrics()
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


@health_bp.route('/health/performance/dashboard')
@login_required
@admin_required
def performance_dashboard():
    """Performance monitoring dashboard (admin only)."""
    try:
        # Get performance metrics
        metrics = get_performance_metrics()
        
        # Get slow queries
        slow_queries = []
        if performance_monitor:
            slow_queries = performance_monitor.get_slow_queries(20)
        
        return render_template('admin/performance_dashboard.html',
                             metrics=metrics,
                             slow_queries=slow_queries)
    except Exception as e:
        return render_template('admin/performance_dashboard.html',
                             metrics={'error': str(e)},
                             slow_queries=[])


@health_bp.route('/health/performance/reset', methods=['POST'])
@login_required
@admin_required
def reset_performance_stats():
    """Reset performance statistics (admin only)."""
    try:
        if performance_monitor:
            performance_monitor.reset_stats()
        
        return jsonify({
            'status': 'success',
            'message': 'Performance statistics reset successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@health_bp.route('/health/cache/invalidate', methods=['POST'])
@login_required
@admin_required
def invalidate_cache():
    """Invalidate query cache (admin only)."""
    try:
        pattern = request.json.get('pattern') if request.is_json else None
        
        if db_optimizer:
            db_optimizer.invalidate_cache(pattern)
        
        return jsonify({
            'status': 'success',
            'message': f'Cache invalidated with pattern: {pattern}',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@health_bp.route('/health/database/test')
@login_required
@admin_required
def database_test():
    """Comprehensive database performance test (admin only)."""
    try:
        test_results = {}
        
        # Test 1: Simple query performance
        start_time = time.time()
        user_count = User.query.count()
        test_results['simple_query'] = {
            'duration_ms': round((time.time() - start_time) * 1000, 2),
            'result': user_count
        }
        
        # Test 2: Join query performance
        start_time = time.time()
        availability_with_users = db.session.query(Availability).join(User).count()
        test_results['join_query'] = {
            'duration_ms': round((time.time() - start_time) * 1000, 2),
            'result': availability_with_users
        }
        
        # Test 3: Complex query performance
        start_time = time.time()
        complex_query = db.session.query(User).filter(
            User.is_active == True
        ).join(Availability).filter(
            Availability.date >= datetime.now().date()
        ).distinct().count()
        test_results['complex_query'] = {
            'duration_ms': round((time.time() - start_time) * 1000, 2),
            'result': complex_query
        }
        
        # Test 4: Transaction performance
        start_time = time.time()
        try:
            db.session.begin()
            test_user = User.query.first()
            if test_user:
                test_user.username = test_user.username  # No-op update
            db.session.rollback()
            test_results['transaction_test'] = {
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'result': 'success'
            }
        except Exception as e:
            db.session.rollback()
            test_results['transaction_test'] = {
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'result': f'error: {str(e)}'
            }
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'test_results': test_results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


def _get_uptime():
    """Get application uptime information."""
    try:
        # This is a simple implementation - in production you might want
        # to track actual application start time
        import psutil
        process = psutil.Process(os.getpid())
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time
        
        return {
            'started_at': create_time.isoformat(),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_human': str(uptime)
        }
    except ImportError:
        # psutil not available, return basic info
        return {
            'uptime_seconds': None,
            'uptime_human': 'Unknown (psutil not available)'
        }


def _get_system_info():
    """Get system information for health check."""
    try:
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage for the application directory
        disk = psutil.disk_usage('.')
        
        return {
            'memory': {
                'total_mb': round(memory.total / 1024 / 1024, 2),
                'available_mb': round(memory.available / 1024 / 1024, 2),
                'percent_used': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'percent_used': round((disk.used / disk.total) * 100, 2)
            },
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
    except ImportError:
        return {
            'memory': 'Unknown (psutil not available)',
            'disk': 'Unknown (psutil not available)',
            'cpu_percent': 'Unknown (psutil not available)'
        }
    except Exception as e:
        return {
            'error': f'Error getting system info: {str(e)}'
        }