"""
Advanced health monitoring for the Ingress leaderboard database.

This module provides comprehensive health monitoring, performance metrics,
and alerting for the database layer.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import contextmanager

from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_database_connection, get_db_session

logger = logging.getLogger(__name__)


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    query_count: int = 0
    total_query_time: float = 0.0
    slow_queries: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    connection_pool_stats: Dict[str, Any] = field(default_factory=dict)
    uptime: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)


class DatabaseHealthMonitor:
    """Advanced database health monitoring."""

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize health monitor.

        Args:
            slow_query_threshold: Threshold in seconds for slow query detection
        """
        self.slow_query_threshold = slow_query_threshold
        self.metrics = DatabaseMetrics()
        self._setup_query_listeners()

    def _setup_query_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for query monitoring."""
        try:
            # Listen to all cursor execute events
            event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
            event.listen(Engine, "after_cursor_execute", self._after_cursor_execute)
            event.listen(Engine, "handle_error", self._handle_error)
        except Exception as e:
            logger.error(f"Failed to setup database listeners: {e}")

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Record start time for query execution."""
        context._query_start_time = time.time()

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Record query execution metrics."""
        try:
            if hasattr(context, '_query_start_time'):
                duration = time.time() - context._query_start_time

                # Update metrics
                self.metrics.query_count += 1
                self.metrics.total_query_time += duration

                # Check if it's a slow query
                if duration > self.slow_query_threshold:
                    slow_query = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'duration': duration,
                        'statement': str(statement)[:500],  # Truncate long queries
                        'parameters': str(parameters)[:200] if parameters else None
                    }
                    self.metrics.slow_queries.append(slow_query)

                    # Keep only recent slow queries (last 100)
                    if len(self.metrics.slow_queries) > 100:
                        self.metrics.slow_queries = self.metrics.slow_queries[-100:]

                    logger.warning(f"Slow query detected: {duration:.3f}s - {str(statement)[:100]}")

        except Exception as e:
            logger.error(f"Error recording query metrics: {e}")

    def _handle_error(self, context):
        """Record database errors."""
        try:
            self.metrics.error_count += 1
            self.metrics.last_error = str(context.exception)
            self.metrics.last_error_time = datetime.utcnow()

            logger.error(f"Database error: {context.exception}")
        except Exception as e:
            logger.error(f"Error recording database error: {e}")

    def get_connection_health(self) -> Dict[str, Any]:
        """
        Get comprehensive database connection health status.

        Returns:
            Dictionary with health information
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'connection': {},
            'performance': {},
            'errors': {},
            'recommendations': []
        }

        try:
            db = get_database_connection()

            # Test basic connection
            connection_healthy = db.test_connection()
            if not connection_healthy:
                health['status'] = 'unhealthy'
                health['recommendations'].append('Database connection failed')
                return health

            # Get connection pool stats
            pool_stats = db.get_connection_stats()
            health['connection'] = {
                'pool_stats': pool_stats,
                'database_url': db.database_url.split('@')[-1] if '@' in db.database_url else 'local',
                'engine_initialized': db.engine is not None
            }

            # Calculate performance metrics
            avg_query_time = (self.metrics.total_query_time / max(self.metrics.query_count, 1))

            health['performance'] = {
                'query_count': self.metrics.query_count,
                'avg_query_time_ms': round(avg_query_time * 1000, 2),
                'total_query_time_seconds': round(self.metrics.total_query_time, 2),
                'slow_query_count': len(self.metrics.slow_queries),
                'slow_query_threshold_seconds': self.slow_query_threshold,
                'uptime_hours': round((datetime.utcnow() - self.metrics.start_time).total_seconds() / 3600, 2)
            }

            # Error metrics
            if self.metrics.error_count > 0:
                time_since_last_error = None
                if self.metrics.last_error_time:
                    time_since_last_error = (datetime.utcnow() - self.metrics.last_error_time).total_seconds()

                health['errors'] = {
                    'error_count': self.metrics.error_count,
                    'last_error': self.metrics.last_error,
                    'last_error_time': self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None,
                    'time_since_last_error_seconds': time_since_last_error,
                    'error_rate': round(self.metrics.error_count / max(self.metrics.query_count, 1) * 100, 3)
                }

            # Determine health status based on metrics
            if avg_query_time > self.slow_query_threshold:
                health['status'] = 'degraded'
                health['recommendations'].append(f'High average query time: {avg_query_time:.3f}s')

            if len(self.metrics.slow_queries) > 10:
                health['status'] = 'degraded'
                health['recommendations'].append(f'Many slow queries: {len(self.metrics.slow_queries)}')

            if self.metrics.error_count > 0:
                if self.metrics.error_count / max(self.metrics.query_count, 1) > 0.05:  # 5% error rate
                    health['status'] = 'unhealthy'
                    health['recommendations'].append('High error rate detected')

            # Check connection pool health
            if 'available_connections' in pool_stats:
                available = pool_stats.get('available_connections', 0)
                if isinstance(available, int) and available == 0:
                    health['status'] = 'degraded'
                    health['recommendations'].append('No available connections in pool')

        except Exception as e:
            health['status'] = 'error'
            health['error'] = str(e)
            logger.error(f"Database health check failed: {e}")

        return health

    def get_table_health(self) -> Dict[str, Any]:
        """
        Get health status of database tables.

        Returns:
            Dictionary with table health information
        """
        table_health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'tables': {},
            'missing_tables': [],
            'table_sizes': {},
            'row_counts': {},
            'recommendations': []
        }

        try:
            # Tables we expect to exist
            expected_tables = [
                'users', 'agents', 'stats_submissions',
                'agent_stats', 'leaderboard_cache', 'faction_changes',
                'progress_snapshots', 'alembic_version'
            ]

            with get_db_session() as session:
                for table in expected_tables:
                    try:
                        # Test table access
                        result = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                        table_health['tables'][table] = 'accessible'

                        # Get row count
                        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = count_result.scalar()
                        table_health['row_counts'][table] = row_count

                        # For SQLite, get approximate page count as size indicator
                        if session.bind.dialect.name == 'sqlite':
                            try:
                                size_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                                table_health['table_sizes'][table] = row_count
                            except:
                                table_health['table_sizes'][table] = 'unknown'

                    except SQLAlchemyError as e:
                        if 'does not exist' in str(e).lower():
                            table_health['missing_tables'].append(table)
                            table_health['tables'][table] = 'missing'
                        else:
                            table_health['tables'][table] = f'error: {str(e)[:100]}'

                # Check for alembic_version table to ensure migrations are working
                if 'alembic_version' not in table_health['tables'] or \
                   table_health['tables']['alembic_version'] != 'accessible':
                    table_health['status'] = 'warning'
                    table_health['recommendations'].append('Alembic migration table not accessible')

                # Check for critical missing tables
                critical_tables = ['users', 'agents', 'stats_submissions']
                missing_critical = [t for t in critical_tables if t in table_health['missing_tables']]
                if missing_critical:
                    table_health['status'] = 'unhealthy'
                    table_health['recommendations'].append(f'Critical tables missing: {missing_critical}')

                # Check for empty critical tables (might indicate initialization issues)
                for table in critical_tables:
                    if table in table_health['row_counts'] and table_health['row_counts'][table] == 0:
                        table_health['recommendations'].append(f'Critical table {table} is empty')

        except Exception as e:
            table_health['status'] = 'error'
            table_health['error'] = str(e)
            logger.error(f"Table health check failed: {e}")

        return table_health

    def get_migration_health(self) -> Dict[str, Any]:
        """
        Get migration system health status.

        Returns:
            Dictionary with migration health information
        """
        try:
            from .migrations import get_migration_manager
            manager = get_migration_manager()
            return manager.check_migration_health()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report including all aspects.

        Returns:
            Complete health report
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'database': self.get_connection_health(),
            'tables': self.get_table_health(),
            'migrations': self.get_migration_health(),
            'recent_slow_queries': self.metrics.slow_queries[-10:],  # Last 10 slow queries
            'recommendations': []
        }

        # Determine overall status
        statuses = [
            report['database']['status'],
            report['tables']['status'],
            report['migrations']['status']
        ]

        if 'unhealthy' in statuses or 'error' in statuses:
            report['overall_status'] = 'unhealthy'
        elif 'degraded' in statuses or 'warning' in statuses:
            report['overall_status'] = 'degraded'

        # Collect all recommendations
        for section in ['database', 'tables', 'migrations']:
            if 'recommendations' in report[section]:
                report['recommendations'].extend(report[section]['recommendations'])

        return report

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = DatabaseMetrics()
        logger.info("Database metrics reset")

    @contextmanager
    def performance_check(self, operation_name: str):
        """
        Context manager for performance monitoring of specific operations.

        Args:
            operation_name: Name of the operation being monitored
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            logger.debug(f"Operation '{operation_name}' completed in {duration:.3f}s")

            if duration > self.slow_query_threshold:
                logger.warning(f"Slow operation detected: {operation_name} took {duration:.3f}s")


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> DatabaseHealthMonitor:
    """
    Get or create global health monitor instance.

    Returns:
        DatabaseHealthMonitor instance
    """
    global _health_monitor

    if _health_monitor is None:
        _health_monitor = DatabaseHealthMonitor()

    return _health_monitor


def get_database_health() -> Dict[str, Any]:
    """
    Get comprehensive database health status.

    Returns:
        Complete health report
    """
    monitor = get_health_monitor()
    return monitor.get_comprehensive_health_report()


def run_health_checks() -> Dict[str, Any]:
    """
    Run all database health checks.

    Returns:
        Dictionary with health check results
    """
    monitor = get_health_monitor()

    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'overall_status': 'healthy',
        'checks': {}
    }

    try:
        # Connection health
        results['checks']['connection'] = monitor.get_connection_health()

        # Table health
        results['checks']['tables'] = monitor.get_table_health()

        # Migration health
        results['checks']['migrations'] = monitor.get_migration_health()

        # Determine overall status
        statuses = [check['status'] for check in results['checks'].values()]

        if 'unhealthy' in statuses or 'error' in statuses:
            results['overall_status'] = 'unhealthy'
        elif 'degraded' in statuses or 'warning' in statuses:
            results['overall_status'] = 'degraded'

        # Generate summary
        results['summary'] = {
            'total_checks': len(results['checks']),
            'healthy_checks': len([s for s in statuses if s == 'healthy']),
            'degraded_checks': len([s for s in statuses if s in ['degraded', 'warning']]),
            'unhealthy_checks': len([s for s in statuses if s in ['unhealthy', 'error']])
        }

    except Exception as e:
        results['overall_status'] = 'error'
        results['error'] = str(e)
        logger.error(f"Health checks failed: {e}")

    return results


if __name__ == "__main__":
    # Simple health check when run directly
    import json

    health = run_health_checks()
    print(json.dumps(health, indent=2, default=str))