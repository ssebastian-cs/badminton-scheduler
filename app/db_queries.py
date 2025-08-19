"""
Optimized Database Query Utilities

This module provides optimized, cached database queries for common operations
in the badminton scheduler application.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask_login import current_user
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import joinedload, selectinload

from . import db
from .models import User, Availability, Comment, AdminAction
from .db_performance import query_performance_decorator, db_optimizer


class OptimizedQueries:
    """Collection of optimized database queries with caching support."""
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda start_date, end_date: f"availability_range_{start_date}_{end_date}",
        ttl=300  # 5 minutes
    )
    def get_availability_by_date_range(start_date: date, end_date: date) -> List[Availability]:
        """Get availability entries for date range with optimized query."""
        return (
            Availability.query
            .join(User)
            .filter(
                Availability.date >= start_date,
                Availability.date <= end_date,
                User.is_active == True
            )
            .options(joinedload(Availability.user))  # Eager load user data
            .order_by(Availability.date, Availability.start_time)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda user_id, limit: f"user_availability_{user_id}_{limit}",
        ttl=180  # 3 minutes
    )
    def get_user_future_availability(user_id: int, limit: int = 50) -> List[Availability]:
        """Get user's future availability entries with limit."""
        return (
            Availability.query
            .filter(
                Availability.user_id == user_id,
                Availability.date >= date.today()
            )
            .order_by(Availability.date, Availability.start_time)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda: "active_users_count",
        ttl=600  # 10 minutes
    )
    def get_active_users_count() -> int:
        """Get count of active users."""
        return User.query.filter_by(is_active=True).count()
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda: "user_stats",
        ttl=600  # 10 minutes
    )
    def get_user_statistics() -> Dict[str, int]:
        """Get comprehensive user statistics."""
        # Use separate queries for better SQLite compatibility
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        blocked_users = User.query.filter_by(is_active=False).count()
        admin_users = User.query.filter_by(role='Admin').count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'admin_users': admin_users
        }
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda: "content_stats",
        ttl=300  # 5 minutes
    )
    def get_content_statistics() -> Dict[str, int]:
        """Get content statistics (availability, comments)."""
        # Use separate queries for better SQLite compatibility
        total_availability = Availability.query.count()
        future_availability = Availability.query.filter(Availability.date >= date.today()).count()
        total_comments = Comment.query.count()
        
        return {
            'total_availability': total_availability,
            'future_availability': future_availability,
            'total_comments': total_comments
        }
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda limit: f"recent_comments_{limit}",
        ttl=120  # 2 minutes
    )
    def get_recent_comments(limit: int = 20) -> List[Comment]:
        """Get recent comments with user data."""
        return (
            Comment.query
            .join(User)
            .filter(User.is_active == True)
            .options(joinedload(Comment.user))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda user_id, limit: f"user_comments_{user_id}_{limit}",
        ttl=300  # 5 minutes
    )
    def get_user_comments(user_id: int, limit: int = 50) -> List[Comment]:
        """Get user's comments with pagination."""
        return (
            Comment.query
            .filter_by(user_id=user_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda limit: f"recent_admin_actions_{limit}",
        ttl=180  # 3 minutes
    )
    def get_recent_admin_actions(limit: int = 10) -> List[AdminAction]:
        """Get recent admin actions with user data."""
        return (
            AdminAction.query
            .join(AdminAction.admin_user)
            .options(
                joinedload(AdminAction.admin_user),
                joinedload(AdminAction.target_user)
            )
            .order_by(AdminAction.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda page, per_page: f"users_paginated_{page}_{per_page}",
        ttl=300  # 5 minutes
    )
    def get_users_paginated(page: int = 1, per_page: int = 20):
        """Get paginated users list."""
        return (
            User.query
            .order_by(User.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
    
    @staticmethod
    def get_availability_conflicts(user_id: int, date_val: date, 
                                 start_time, end_time, exclude_id: Optional[int] = None) -> List[Availability]:
        """Check for availability conflicts for a user on a specific date."""
        query = (
            Availability.query
            .filter(
                Availability.user_id == user_id,
                Availability.date == date_val,
                or_(
                    and_(Availability.start_time <= start_time, Availability.end_time > start_time),
                    and_(Availability.start_time < end_time, Availability.end_time >= end_time),
                    and_(Availability.start_time >= start_time, Availability.end_time <= end_time)
                )
            )
        )
        
        if exclude_id:
            query = query.filter(Availability.id != exclude_id)
        
        return query.all()
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda date_val: f"daily_availability_{date_val}",
        ttl=600  # 10 minutes
    )
    def get_daily_availability_summary(date_val: date) -> Dict[str, Any]:
        """Get availability summary for a specific date."""
        entries = (
            Availability.query
            .join(User)
            .filter(
                Availability.date == date_val,
                User.is_active == True
            )
            .options(joinedload(Availability.user))
            .order_by(Availability.start_time)
            .all()
        )
        
        # Group by user
        user_availability = {}
        for entry in entries:
            user_id = entry.user_id
            if user_id not in user_availability:
                user_availability[user_id] = {
                    'user': entry.user,
                    'entries': []
                }
            user_availability[user_id]['entries'].append(entry)
        
        return {
            'date': date_val,
            'total_entries': len(entries),
            'unique_users': len(user_availability),
            'user_availability': user_availability
        }
    
    @staticmethod
    def search_users(query: str, limit: int = 20) -> List[User]:
        """Search users by username with limit."""
        search_pattern = f"%{query}%"
        return (
            User.query
            .filter(
                User.username.ilike(search_pattern),
                User.is_active == True
            )
            .order_by(User.username)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    @query_performance_decorator(
        cache_key_func=lambda hours: f"admin_actions_summary_{hours}",
        ttl=300  # 5 minutes
    )
    def get_admin_actions_summary(hours: int = 24) -> Dict[str, Any]:
        """Get admin actions summary for the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        actions = (
            AdminAction.query
            .filter(AdminAction.created_at >= since)
            .all()
        )
        
        # Group by action type
        action_counts = {}
        admin_counts = {}
        
        for action in actions:
            action_type = action.action_type
            admin_id = action.admin_user_id
            
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            admin_counts[admin_id] = admin_counts.get(admin_id, 0) + 1
        
        return {
            'total_actions': len(actions),
            'action_counts': action_counts,
            'admin_counts': admin_counts,
            'time_period_hours': hours
        }


class CacheManager:
    """Utility class for managing query cache invalidation."""
    
    @staticmethod
    def invalidate_user_cache(user_id: Optional[int] = None):
        """Invalidate user-related cache entries."""
        if db_optimizer:
            if user_id:
                db_optimizer.invalidate_cache(f"user_.*_{user_id}_.*")
            else:
                db_optimizer.invalidate_cache("user_.*")
                db_optimizer.invalidate_cache("active_users_count")
    
    @staticmethod
    def invalidate_availability_cache(user_id: Optional[int] = None, date_val: Optional[date] = None):
        """Invalidate availability-related cache entries."""
        if db_optimizer:
            patterns = ["availability_.*", "content_stats", "daily_availability_.*"]
            
            if user_id:
                patterns.append(f"user_availability_{user_id}_.*")
            
            if date_val:
                patterns.append(f"daily_availability_{date_val}")
                patterns.append(f"availability_range_.*{date_val}.*")
            
            for pattern in patterns:
                db_optimizer.invalidate_cache(pattern)
    
    @staticmethod
    def invalidate_comment_cache(user_id: Optional[int] = None):
        """Invalidate comment-related cache entries."""
        if db_optimizer:
            patterns = ["recent_comments_.*", "content_stats"]
            
            if user_id:
                patterns.append(f"user_comments_{user_id}_.*")
            
            for pattern in patterns:
                db_optimizer.invalidate_cache(pattern)
    
    @staticmethod
    def invalidate_admin_cache():
        """Invalidate admin-related cache entries."""
        if db_optimizer:
            patterns = [
                "recent_admin_actions_.*",
                "admin_actions_summary_.*",
                "users_paginated_.*"
            ]
            
            for pattern in patterns:
                db_optimizer.invalidate_cache(pattern)
    
    @staticmethod
    def invalidate_all_cache():
        """Invalidate all cache entries."""
        if db_optimizer:
            db_optimizer.invalidate_cache()


# Convenience functions for common queries
def get_dashboard_data(view_type: str = 'today', start_date: Optional[date] = None, 
                      end_date: Optional[date] = None) -> Dict[str, Any]:
    """Get optimized dashboard data with caching."""
    from .utils import get_date_range_filter
    
    # Calculate date range
    if not start_date or not end_date:
        start_date, end_date = get_date_range_filter(view_type, start_date, end_date)
    
    # Get availability data
    availability_entries = OptimizedQueries.get_availability_by_date_range(start_date, end_date)
    
    # Group entries by date, then by user
    entries_by_date = {}
    for entry in availability_entries:
        entry_date = entry.date
        if entry_date not in entries_by_date:
            entries_by_date[entry_date] = {}
        
        user_id = entry.user_id
        if user_id not in entries_by_date[entry_date]:
            entries_by_date[entry_date][user_id] = {
                'user': entry.user,
                'entries': []
            }
        entries_by_date[entry_date][user_id]['entries'].append(entry)
    
    return {
        'entries_by_date': entries_by_date,
        'start_date': start_date,
        'end_date': end_date,
        'view_type': view_type,
        'total_entries': len(availability_entries)
    }


def get_admin_dashboard_data() -> Dict[str, Any]:
    """Get optimized admin dashboard data with caching."""
    user_stats = OptimizedQueries.get_user_statistics()
    content_stats = OptimizedQueries.get_content_statistics()
    recent_actions = OptimizedQueries.get_recent_admin_actions(10)
    
    # Combine statistics
    stats = {**user_stats, **content_stats}
    
    return {
        'stats': stats,
        'recent_actions': recent_actions
    }