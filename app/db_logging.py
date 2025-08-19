"""
Database Performance Logging Configuration

This module sets up comprehensive logging for database performance monitoring,
including query performance, connection pool metrics, and cache statistics.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask


class DatabasePerformanceLogger:
    """Custom logger for database performance metrics."""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.logger = None
        self.metrics_logger = None
        self.slow_query_logger = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize database performance logging for Flask app."""
        self.app = app
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(app.root_path, '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up main database performance logger
        self.logger = logging.getLogger('database_performance')
        self.logger.setLevel(logging.INFO)
        
        # Set up metrics logger (for structured metrics data)
        self.metrics_logger = logging.getLogger('database_metrics')
        self.metrics_logger.setLevel(logging.INFO)
        
        # Set up slow query logger
        self.slow_query_logger = logging.getLogger('slow_queries')
        self.slow_query_logger.setLevel(logging.WARNING)
        
        # Configure handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers(log_dir)
        
        # Store reference in app
        app.db_performance_logger = self
    
    def _setup_handlers(self, log_dir: str):
        """Set up logging handlers for different types of database logs."""
        
        # Main database performance log
        db_perf_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'database_performance.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        db_perf_handler.setLevel(logging.INFO)
        db_perf_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        db_perf_handler.setFormatter(db_perf_formatter)
        self.logger.addHandler(db_perf_handler)
        
        # Metrics log (JSON format for easy parsing)
        metrics_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'database_metrics.log'),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        metrics_handler.setLevel(logging.INFO)
        metrics_formatter = JsonFormatter()
        metrics_handler.setFormatter(metrics_formatter)
        self.metrics_logger.addHandler(metrics_handler)
        
        # Slow queries log
        slow_query_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'slow_queries.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5
        )
        slow_query_handler.setLevel(logging.WARNING)
        slow_query_formatter = logging.Formatter(
            '%(asctime)s - SLOW QUERY - Duration: %(duration)s - Query: %(query)s'
        )
        slow_query_handler.setFormatter(slow_query_formatter)
        self.slow_query_logger.addHandler(slow_query_handler)
        
        # Console handler for development
        if self.app and self.app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log_query_performance(self, query: str, duration: float, 
                            params: Optional[Dict] = None, **kwargs):
        """Log query performance metrics."""
        if self.logger:
            self.logger.info(f"Query executed in {duration:.3f}s: {query[:200]}...")
        
        # Log structured metrics
        if self.metrics_logger:
            metrics_data = {
                'type': 'query_performance',
                'timestamp': datetime.utcnow().isoformat(),
                'duration': duration,
                'query': query[:500],  # Truncate long queries
                'params': str(params)[:200] if params else None,
                **kwargs
            }
            self.metrics_logger.info(json.dumps(metrics_data))
    
    def log_slow_query(self, query: str, duration: float, 
                      params: Optional[Dict] = None, **kwargs):
        """Log slow query with detailed information."""
        if self.slow_query_logger:
            self.slow_query_logger.warning(
                f"Slow query detected",
                extra={
                    'duration': f"{duration:.3f}s",
                    'query': query[:1000],
                    'params': str(params)[:200] if params else None,
                    **kwargs
                }
            )
    
    def log_connection_event(self, event_type: str, **kwargs):
        """Log database connection events."""
        if self.logger:
            self.logger.info(f"Connection event: {event_type} - {kwargs}")
        
        # Log structured metrics
        if self.metrics_logger:
            metrics_data = {
                'type': 'connection_event',
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                **kwargs
            }
            self.metrics_logger.info(json.dumps(metrics_data))
    
    def log_cache_event(self, event_type: str, cache_key: Optional[str] = None, **kwargs):
        """Log cache hit/miss events."""
        if self.logger:
            self.logger.debug(f"Cache {event_type}: {cache_key}")
        
        # Log structured metrics
        if self.metrics_logger:
            metrics_data = {
                'type': 'cache_event',
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'cache_key': cache_key,
                **kwargs
            }
            self.metrics_logger.info(json.dumps(metrics_data))
    
    def log_performance_summary(self, summary: Dict[str, Any]):
        """Log periodic performance summary."""
        if self.logger:
            self.logger.info(f"Performance Summary: {summary}")
        
        # Log structured metrics
        if self.metrics_logger:
            metrics_data = {
                'type': 'performance_summary',
                'timestamp': datetime.utcnow().isoformat(),
                **summary
            }
            self.metrics_logger.info(json.dumps(metrics_data))


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated', 
                              'thread', 'threadName', 'processName', 'process',
                              'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_data[key] = value
        
        return json.dumps(log_data)


class PerformanceMetricsCollector:
    """Collects and aggregates database performance metrics."""
    
    def __init__(self, logger: DatabasePerformanceLogger):
        self.logger = logger
        self.metrics_buffer = []
        self.buffer_size = 100
        self.last_flush = datetime.utcnow()
        self.flush_interval = 300  # 5 minutes
    
    def collect_query_metric(self, query: str, duration: float, **kwargs):
        """Collect query performance metric."""
        metric = {
            'type': 'query',
            'timestamp': datetime.utcnow().isoformat(),
            'duration': duration,
            'query_hash': hash(query) % 1000000,  # Simple query identifier
            **kwargs
        }
        
        self.metrics_buffer.append(metric)
        self._check_flush()
    
    def collect_connection_metric(self, event_type: str, **kwargs):
        """Collect connection pool metric."""
        metric = {
            'type': 'connection',
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **kwargs
        }
        
        self.metrics_buffer.append(metric)
        self._check_flush()
    
    def collect_cache_metric(self, event_type: str, **kwargs):
        """Collect cache performance metric."""
        metric = {
            'type': 'cache',
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **kwargs
        }
        
        self.metrics_buffer.append(metric)
        self._check_flush()
    
    def _check_flush(self):
        """Check if metrics buffer should be flushed."""
        now = datetime.utcnow()
        time_since_flush = (now - self.last_flush).total_seconds()
        
        if (len(self.metrics_buffer) >= self.buffer_size or 
            time_since_flush >= self.flush_interval):
            self.flush_metrics()
    
    def flush_metrics(self):
        """Flush metrics buffer to log."""
        if not self.metrics_buffer:
            return
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics()
        
        # Log aggregated metrics
        self.logger.log_performance_summary(aggregated)
        
        # Clear buffer
        self.metrics_buffer.clear()
        self.last_flush = datetime.utcnow()
    
    def _aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics from buffer."""
        query_metrics = [m for m in self.metrics_buffer if m['type'] == 'query']
        connection_metrics = [m for m in self.metrics_buffer if m['type'] == 'connection']
        cache_metrics = [m for m in self.metrics_buffer if m['type'] == 'cache']
        
        aggregated = {
            'period_start': self.last_flush.isoformat(),
            'period_end': datetime.utcnow().isoformat(),
            'total_metrics': len(self.metrics_buffer)
        }
        
        # Aggregate query metrics
        if query_metrics:
            durations = [m['duration'] for m in query_metrics]
            aggregated['queries'] = {
                'count': len(query_metrics),
                'avg_duration': sum(durations) / len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations),
                'slow_queries': len([d for d in durations if d > 0.1])
            }
        
        # Aggregate connection metrics
        if connection_metrics:
            events = {}
            for metric in connection_metrics:
                event_type = metric['event_type']
                events[event_type] = events.get(event_type, 0) + 1
            
            aggregated['connections'] = {
                'events': events,
                'total_events': len(connection_metrics)
            }
        
        # Aggregate cache metrics
        if cache_metrics:
            hits = len([m for m in cache_metrics if m['event_type'] == 'hit'])
            misses = len([m for m in cache_metrics if m['event_type'] == 'miss'])
            total = hits + misses
            
            aggregated['cache'] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hits / total if total > 0 else 0,
                'total_operations': total
            }
        
        return aggregated


# Global instance
db_performance_logger = DatabasePerformanceLogger()


def init_db_logging(app: Flask):
    """Initialize database performance logging for the application."""
    db_performance_logger.init_app(app)
    return db_performance_logger


def get_db_performance_logger() -> DatabasePerformanceLogger:
    """Get the database performance logger instance."""
    return db_performance_logger