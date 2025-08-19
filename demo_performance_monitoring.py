#!/usr/bin/env python3
"""
Demo script to show database performance monitoring in action.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Availability, Comment
from app.db_performance import get_performance_metrics
from app.db_queries import OptimizedQueries
from datetime import date, datetime, time
import time as time_module
import json


def demo_performance_monitoring():
    """Demonstrate database performance monitoring features."""
    print("Database Performance Monitoring Demo")
    print("=" * 50)
    
    # Create app with development config
    app = create_app('development')
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("1. Creating test data...")
        
        # Create some test users if they don't exist
        if User.query.count() == 0:
            users = [
                User(username='admin', password='admin123', role='Admin'),
                User(username='user1', password='user123', role='User'),
                User(username='user2', password='user123', role='User'),
            ]
            
            for user in users:
                db.session.add(user)
            
            db.session.commit()
            print(f"   ✓ Created {len(users)} test users")
        else:
            print(f"   ✓ Using existing {User.query.count()} users")
        
        # Create some test availability entries
        if Availability.query.count() < 5:
            from datetime import timedelta
            users = User.query.all()
            tomorrow = date.today() + timedelta(days=1)
            
            for i, user in enumerate(users[:2]):
                availability = Availability(
                    user_id=user.id,
                    date=tomorrow,
                    start_time=time(9 + i, 0),
                    end_time=time(11 + i, 0)
                )
                db.session.add(availability)
            
            db.session.commit()
            print(f"   ✓ Created test availability entries")
        
        print("\n2. Testing optimized queries...")
        
        # Test cached queries
        start_time = time_module.time()
        user_stats = OptimizedQueries.get_user_statistics()
        query_time = time_module.time() - start_time
        print(f"   ✓ User statistics (first call): {query_time:.3f}s")
        print(f"     {user_stats}")
        
        # Test cache hit
        start_time = time_module.time()
        user_stats_cached = OptimizedQueries.get_user_statistics()
        cached_time = time_module.time() - start_time
        print(f"   ✓ User statistics (cached): {cached_time:.3f}s")
        print(f"     Cache speedup: {query_time/cached_time:.1f}x faster")
        
        # Test availability queries
        from datetime import timedelta
        tomorrow = date.today() + timedelta(days=1)
        availability_entries = OptimizedQueries.get_availability_by_date_range(tomorrow, tomorrow)
        print(f"   ✓ Found {len(availability_entries)} availability entries for tomorrow")
        
        # Test content statistics
        content_stats = OptimizedQueries.get_content_statistics()
        print(f"   ✓ Content statistics: {content_stats}")
        
        print("\n3. Performance metrics...")
        
        # Get performance metrics
        metrics = get_performance_metrics()
        
        if 'error' not in metrics:
            query_stats = metrics['monitor']['query_stats']
            cache_stats = metrics['monitor']['cache_stats']
            connection_stats = metrics['monitor']['connection_stats']
            
            print(f"   ✓ Total queries executed: {query_stats['total_queries']}")
            print(f"   ✓ Average query time: {query_stats['avg_query_time']*1000:.2f}ms")
            print(f"   ✓ Cache hit rate: {cache_stats['hit_rate']*100:.1f}%")
            print(f"   ✓ Cache hits: {cache_stats['hits']}, misses: {cache_stats['misses']}")
            print(f"   ✓ Active connections: {connection_stats['active_connections']}")
            
            # Show slowest queries
            if query_stats['slowest_queries']:
                print(f"\n   Slowest queries:")
                for i, query in enumerate(query_stats['slowest_queries'][:3]):
                    print(f"   {i+1}. {query['avg_time']*1000:.2f}ms - {query['query'][:60]}...")
        else:
            print(f"   ✗ Error getting metrics: {metrics['error']}")
        
        print("\n4. Testing slow query detection...")
        
        # Simulate a slow query
        print("   Executing intentionally slow query...")
        time_module.sleep(0.2)  # Simulate slow operation
        
        # Execute a query that will be monitored
        slow_query_result = User.query.filter(User.username.like('%user%')).all()
        print(f"   ✓ Slow query returned {len(slow_query_result)} results")
        
        # Check for slow queries
        updated_metrics = get_performance_metrics()
        if 'slow_queries' in updated_metrics:
            slow_queries = updated_metrics['slow_queries']
            if slow_queries:
                print(f"   ✓ Detected {len(slow_queries)} slow queries")
                latest_slow = slow_queries[0]
                print(f"     Latest: {latest_slow['duration']:.3f}s - {latest_slow['query'][:60]}...")
            else:
                print("   ✓ No slow queries detected (threshold may be too high)")
        
        print("\n5. Cache invalidation test...")
        
        # Test cache invalidation
        from app.db_queries import CacheManager
        
        # Get cached data
        stats_before = OptimizedQueries.get_user_statistics()
        print(f"   ✓ Stats before invalidation: {stats_before}")
        
        # Invalidate cache
        CacheManager.invalidate_user_cache()
        print("   ✓ User cache invalidated")
        
        # Get data again (should be fresh)
        stats_after = OptimizedQueries.get_user_statistics()
        print(f"   ✓ Stats after invalidation: {stats_after}")
        
        print("\n" + "=" * 50)
        print("✓ Database performance monitoring demo completed successfully!")
        print("\nKey features demonstrated:")
        print("  • Query performance monitoring")
        print("  • Intelligent query caching")
        print("  • Slow query detection")
        print("  • Connection pool monitoring")
        print("  • Cache invalidation")
        print("  • Performance metrics collection")
        
        # Show final metrics summary
        final_metrics = get_performance_metrics()
        if 'error' not in final_metrics:
            print(f"\nFinal Statistics:")
            print(f"  • Total queries: {final_metrics['monitor']['query_stats']['total_queries']}")
            print(f"  • Cache hit rate: {final_metrics['monitor']['cache_stats']['hit_rate']*100:.1f}%")
            print(f"  • Average query time: {final_metrics['monitor']['query_stats']['avg_query_time']*1000:.2f}ms")


if __name__ == '__main__':
    demo_performance_monitoring()