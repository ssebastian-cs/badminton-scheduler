"""
Health check routes for monitoring and deployment verification.
"""
from flask import Blueprint, jsonify, current_app
from app import db
from app.models import User
from datetime import datetime, timezone
import sys
import os

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """
    Comprehensive health check endpoint.
    Returns JSON with system status and basic metrics.
    """
    try:
        from ..error_tracking import get_error_summary
        
        # Database connectivity check
        db_status = "healthy"
        user_count = 0
        try:
            user_count = User.query.count()
        except Exception as e:
            db_status = f"error: {str(e)}"

        # Get error metrics for the last hour
        error_summary = get_error_summary(1)
        
        # Determine error health status
        error_status = "healthy"
        if error_summary['total_errors'] > 50:
            error_status = "degraded"
        elif error_summary['severity_breakdown'].get('CRITICAL', 0) > 0:
            error_status = "critical"

        # Application status
        app_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "environment": current_app.config.get('ENV', 'unknown'),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "database": {
                "status": db_status,
                "user_count": user_count
            },
            "errors": {
                "status": error_status,
                "last_hour_count": error_summary['total_errors'],
                "critical_count": error_summary['severity_breakdown'].get('CRITICAL', 0)
            },
            "system": {
                "platform": sys.platform,
                "pid": os.getpid()
            }
        }

        # Determine overall health
        overall_status = "healthy"
        status_code = 200
        
        if db_status != "healthy" or error_status == "critical":
            overall_status = "critical"
            status_code = 503
        elif error_status == "degraded":
            overall_status = "degraded"
            status_code = 503
        
        app_status["status"] = overall_status
        return jsonify(app_status), status_code

    except Exception as e:
        error_status = {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        return jsonify(error_status), 500


@health_bp.route('/health/ready')
def readiness_check():
    """
    Kubernetes-style readiness probe.
    Returns 200 if application is ready to serve traffic.
    """
    try:
        # Check database connection
        User.query.first()
        return jsonify({"status": "ready"}), 200
    except Exception:
        return jsonify({"status": "not ready"}), 503


@health_bp.route('/health/live')
def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if application is alive (basic functionality).
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200