"""
Database Performance Monitoring and Optimization Module

This module provides comprehensive database performance monitoring, query optimization,
caching, and connection pooling for the badminton scheduler application.
"""

import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, List, Optional, Any, Tuple
from flask import g, current_app
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import json
import os

# Performance monitoring logger
perf_logger = logging.getLogger('database_performance')


class DatabasePerformanceMonitor:
    """Comprehensive database performance monitoring system."""
    
    def __init__(self):
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'recent_times': deque(maxlen=100),
            'slow_queries': deque(maxlen=50)
        })
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'peak_connections': 0,
            'connection_errors': 0,
            'pool_size': 0,
            'pool_overflow': 0
        }
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'hit_rate': 0.0,
            'cache_size': 0
        }
        self._lock = Lock()
        self.slow_query_threshold = 0.1  # 100ms
        self.monitoring_enabled = True
    
    def record_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Record query execution statistics."""
        if not self.monitoring_enabled:
            return
        
        with self._lock:
            # Normalize query for grouping (remove specific values)
            normalized_query = self._normalize_query(query)
            
            stats = self.query_stats[normalized_query]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)
            stats['recent_times'].append(duration)
            
            # Track slow queries
            if duration > self.slow_query_threshold:
                slow_query_info = {
                    'query': query[:500],  # Truncate long queries
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'params': str(params)[:200] if params else None
                }
                stats['slow_queries'].append(slow_query_info)
                
                # Log slow query
                perf_logger.warning(
                    f"Slow query detected: {duration:.3f}s - {query[:200]}..."
                )
    
    def record_connection_event(self, event_type: str, **kwargs):
        """Record connection pool events."""
        if not self.monitoring_enabled:
            return
        
        with self._lock:
            if event_type == 'connect':
                self.connection_stats['total_connections'] += 1
                self.connection_stats['active_connections'] += 1
                self.connection_stats['peak_connections'] = max(
                    self.connection_stats['peak_connections'],
                    self.connection_stats['active_connections']
                )
            elif event_type == 'disconnect':
                self.connection_stats['active_connections'] = max(
                    0, self.connection_stats['active_connections'] - 1
                )
            elif event_type == 'error':
                self.connection_stats['connection_errors'] += 1
            elif event_type == 'pool_info':
                self.connection_stats.update(kwargs)
    
    def record_cache_event(self, event_type: str):
        """Record cache hit/miss events."""
        if not self.monitoring_enabled:
            return
        
        with self._lock:
            if event_type == 'hit':
                self.cache_stats['hits'] += 1
            elif event_type == 'miss':
                self.cache_stats['misses'] += 1
            
            total = self.cache_stats['hits'] + self.cache_stats['misses']
            if total > 0:
                self.cache_stats['hit_rate'] = self.cache_stats['hits'] / total
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            # Calculate query statistics
            total_queries = sum(stats['count'] for stats in self.query_stats.values())
            total_query_time = sum(stats['total_time'] for stats in self.query_stats.values())
            avg_query_time = total_query_time / total_queries if total_queries > 0 else 0
            
            # Find slowest queries
            slowest_queries = []
            for query, stats in self.query_stats.items():
                if stats['count'] > 0:
                    slowest_queries.append({
                        'query': query[:200],
                        'avg_time': stats['avg_time'],
                        'max_time': stats['max_time'],
                        'count': stats['count'],
                        'total_time': stats['total_time']
                    })
            
            slowest_queries.sort(key=lambda x: x['avg_time'], reverse=True)
            
            return {
                'query_stats': {
                    'total_queries': total_queries,
                    'total_query_time': total_query_time,
                    'avg_query_time': avg_query_time,
                    'slowest_queries': slowest_queries[:10]
                },
                'connection_stats': dict(self.connection_stats),
                'cache_stats': dict(self.cache_stats),
                'monitoring_enabled': self.monitoring_enabled,
                'slow_query_threshold': self.slow_query_threshold
            }
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict]:
        """Get recent slow queries."""
        slow_queries = []
        with self._lock:
            for stats in self.query_stats.values():
                slow_queries.extend(stats['slow_queries'])
        
        # Sort by duration and return most recent
        slow_queries.sort(key=lambda x: x['duration'], reverse=True)
        return list(slow_queries)[:limit]
    
    def reset_stats(self):
        """Reset all performance statistics."""
        with self._lock:
            self.query_stats.clear()
            self.connection_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'peak_connections': 0,
                'connection_errors': 0,
                'pool_size': 0,
                'pool_overflow': 0
            }
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0,
                'cache_size': 0
            }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for grouping by removing specific values."""
        # Remove common parameter patterns
        import re
        
        # Replace numbers with placeholder
        query = re.sub(r'\b\d+\b', '?', query)
        
        # Replace quoted strings with placeholder
        query = re.sub(r"'[^']*'", "'?'", query)
        query = re.sub(r'"[^"]*"', '"?"', query)
        
        # Replace IN clauses with placeholder
        query = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', query, flags=re.IGNORECASE)
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query


class QueryCache:
    """Simple in-memory query result cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        with self._lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                return None
            
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache a result with optional TTL."""
        with self._lock:
            # Clean up if cache is full
            if len(self.cache) >= self.max_size:
                self._cleanup_expired()
                
                # If still full, remove oldest entries
                if len(self.cache) >= self.max_size:
                    oldest_keys = sorted(
                        self.timestamps.keys(),
                        key=lambda k: self.timestamps[k]
                    )[:self.max_size // 4]  # Remove 25% of entries
                    
                    for old_key in oldest_keys:
                        self._remove(old_key)
            
            self.cache[key] = value
            self.timestamps[key] = {
                'created': time.time(),
                'ttl': ttl or self.default_ttl
            }
    
    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries matching pattern or all if no pattern."""
        with self._lock:
            if pattern is None:
                self.cache.clear()
                self.timestamps.clear()
            else:
                import re
                regex = re.compile(pattern)
                keys_to_remove = [
                    key for key in self.cache.keys()
                    if regex.search(key)
                ]
                for key in keys_to_remove:
                    self._remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'default_ttl': self.default_ttl
            }
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.timestamps:
            return True
        
        timestamp_info = self.timestamps[key]
        age = time.time() - timestamp_info['created']
        return age > timestamp_info['ttl']
    
    def _remove(self, key: str) -> None:
        """Remove entry from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key in self.cache.keys()
            if self._is_expired(key)
        ]
        for key in expired_keys:
            self._remove(key)


class DatabaseOptimizer:
    """Database query optimization and indexing utilities."""
    
    def __init__(self, db):
        self.db = db
        self.monitor = DatabasePerformanceMonitor()
        self.cache = QueryCache()
    
    def add_performance_indexes(self):
        """Add performance indexes for frequently queried fields."""
        try:
            with self.db.engine.connect() as conn:
                # Check existing indexes first
                existing_indexes = self._get_existing_indexes(conn)
                
                # Define performance indexes to add
                performance_indexes = [
                    # User table indexes
                    {
                        'name': 'idx_users_role_active',
                        'table': 'users',
                        'columns': ['role', 'is_active'],
                        'description': 'Optimize admin user queries and active user filtering'
                    },
                    {
                        'name': 'idx_users_created_at',
                        'table': 'users',
                        'columns': ['created_at'],
                        'description': 'Optimize user listing by creation date'
                    },
                    
                    # Availability table indexes
                    {
                        'name': 'idx_availability_date_range',
                        'table': 'availability',
                        'columns': ['date', 'start_time', 'end_time'],
                        'description': 'Optimize date range queries and time-based filtering'
                    },
                    {
                        'name': 'idx_availability_user_date_time',
                        'table': 'availability',
                        'columns': ['user_id', 'date', 'start_time'],
                        'description': 'Optimize user-specific availability queries'
                    },
                    {
                        'name': 'idx_availability_future_dates',
                        'table': 'availability',
                        'columns': ['date'],
                        'where': 'date >= date("now")',
                        'description': 'Optimize future availability queries'
                    },
                    
                    # Comments table indexes
                    {
                        'name': 'idx_comments_user_created',
                        'table': 'comments',
                        'columns': ['user_id', 'created_at'],
                        'description': 'Optimize user comment history queries'
                    },
                    {
                        'name': 'idx_comments_recent',
                        'table': 'comments',
                        'columns': ['created_at'],
                        'order': 'DESC',
                        'description': 'Optimize recent comments queries'
                    },
                    
                    # Admin actions table indexes (if exists)
                    {
                        'name': 'idx_admin_actions_admin_date',
                        'table': 'admin_actions',
                        'columns': ['admin_user_id', 'created_at'],
                        'description': 'Optimize admin action history queries'
                    },
                    {
                        'name': 'idx_admin_actions_target_lookup',
                        'table': 'admin_actions',
                        'columns': ['target_type', 'target_id', 'created_at'],
                        'description': 'Optimize target-specific action queries'
                    }
                ]
                
                # Add indexes that don't already exist
                added_indexes = []
                for index_def in performance_indexes:
                    if index_def['name'] not in existing_indexes:
                        try:
                            self._create_index(conn, index_def)
                            added_indexes.append(index_def['name'])
                            perf_logger.info(f"Added performance index: {index_def['name']}")
                        except Exception as e:
                            perf_logger.error(f"Failed to create index {index_def['name']}: {e}")
                
                if added_indexes:
                    perf_logger.info(f"Successfully added {len(added_indexes)} performance indexes")
                else:
                    perf_logger.info("All performance indexes already exist")
                
                return added_indexes
                
        except Exception as e:
            perf_logger.error(f"Error adding performance indexes: {e}")
            return []
    
    def optimize_connection_pool(self, app):
        """Optimize database connection pool settings."""
        try:
            # Get current configuration
            current_config = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            # Check if using SQLite (which has different pool options)
            is_sqlite = 'sqlite' in database_url.lower()
            
            if is_sqlite:
                # SQLite-specific optimizations
                optimized_config = {
                    'pool_pre_ping': True,
                    'pool_recycle': 3600,
                    'echo': False,
                    'connect_args': {
                        'check_same_thread': False,
                        'timeout': 20,
                        'isolation_level': None,  # Autocommit mode
                    }
                }
            else:
                # PostgreSQL/MySQL optimizations
                optimized_config = {
                    'pool_size': 20,
                    'max_overflow': 30,
                    'pool_pre_ping': True,
                    'pool_recycle': 3600,
                    'pool_timeout': 30,
                    'echo': False,
                    'echo_pool': False,
                    'connect_args': {
                        'connect_timeout': 20,
                    }
                }
            
            # Merge with existing config
            optimized_config.update(current_config)
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = optimized_config
            
            perf_logger.info(f"Database connection pool optimized for {'SQLite' if is_sqlite else 'SQL database'}")
            return True
            
        except Exception as e:
            perf_logger.error(f"Error optimizing connection pool: {e}")
            return False
    
    def setup_query_monitoring(self, app):
        """Set up SQLAlchemy event listeners for query monitoring."""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time."""
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query completion and statistics."""
            if hasattr(context, '_query_start_time'):
                duration = time.time() - context._query_start_time
                self.monitor.record_query(statement, duration, parameters)
        
        @event.listens_for(Engine, "connect")
        def engine_connect(dbapi_conn, connection_record):
            """Record connection events."""
            self.monitor.record_connection_event('connect')
        
        @event.listens_for(Engine, "close")
        def engine_close(dbapi_conn, connection_record):
            """Record connection close events."""
            self.monitor.record_connection_event('disconnect')
        
        perf_logger.info("Database query monitoring enabled")
    
    def cached_query(self, cache_key: str, query_func, ttl: Optional[int] = None):
        """Execute query with caching support."""
        # Try to get from cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self.monitor.record_cache_event('hit')
            return cached_result
        
        # Execute query and cache result
        self.monitor.record_cache_event('miss')
        result = query_func()
        self.cache.set(cache_key, result, ttl)
        
        return result
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cached queries."""
        self.cache.invalidate(pattern)
        perf_logger.info(f"Cache invalidated with pattern: {pattern}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'monitor': self.monitor.get_performance_summary(),
            'cache': self.cache.get_stats(),
            'slow_queries': self.monitor.get_slow_queries(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_existing_indexes(self, conn) -> set:
        """Get list of existing database indexes."""
        try:
            # SQLite specific query
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            return {row[0] for row in result}
        except Exception as e:
            perf_logger.error(f"Error getting existing indexes: {e}")
            return set()
    
    def _create_index(self, conn, index_def: Dict):
        """Create a database index."""
        columns_str = ', '.join(index_def['columns'])
        
        # Build CREATE INDEX statement
        sql = f"CREATE INDEX IF NOT EXISTS {index_def['name']} ON {index_def['table']} ({columns_str})"
        
        # Add WHERE clause if specified (partial index)
        if 'where' in index_def:
            sql += f" WHERE {index_def['where']}"
        
        conn.execute(text(sql))
        conn.commit()


# Global instances
db_optimizer = None
performance_monitor = None


def init_db_performance(app, db):
    """Initialize database performance monitoring and optimization."""
    global db_optimizer, performance_monitor
    
    try:
        # Create optimizer instance
        db_optimizer = DatabaseOptimizer(db)
        performance_monitor = db_optimizer.monitor
        
        # Set up monitoring
        db_optimizer.setup_query_monitoring(app)
        
        # Optimize connection pool
        db_optimizer.optimize_connection_pool(app)
        
        perf_logger.info("Database performance monitoring initialized successfully")
        
        # Store reference in app for later use
        app.db_optimizer = db_optimizer
        
        return db_optimizer
        
    except Exception as e:
        perf_logger.error(f"Failed to initialize database performance monitoring: {e}")
        return None


def query_performance_decorator(cache_key_func=None, ttl=300):
    """Decorator for monitoring and caching database queries."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if db_optimizer is None:
                return func(*args, **kwargs)
            
            # Generate cache key if function provided
            if cache_key_func:
                try:
                    cache_key = cache_key_func(*args, **kwargs)
                    return db_optimizer.cached_query(cache_key, lambda: func(*args, **kwargs), ttl)
                except Exception as e:
                    perf_logger.warning(f"Cache key generation failed: {e}")
            
            # Execute without caching
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def init_performance_indexes():
    """Initialize performance indexes (call after app context is available)."""
    if db_optimizer:
        try:
            return db_optimizer.add_performance_indexes()
        except Exception as e:
            perf_logger.error(f"Failed to initialize performance indexes: {e}")
            return []
    return []


def get_performance_metrics() -> Dict[str, Any]:
    """Get current database performance metrics."""
    if db_optimizer is None:
        return {'error': 'Performance monitoring not initialized'}
    
    return db_optimizer.get_performance_report()


def invalidate_query_cache(pattern: Optional[str] = None):
    """Invalidate query cache entries."""
    if db_optimizer:
        db_optimizer.invalidate_cache(pattern)