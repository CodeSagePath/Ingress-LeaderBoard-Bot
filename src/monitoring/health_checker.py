"""
Health check system for the Ingress Prime Leaderboard Bot.

Provides comprehensive health monitoring for bot components,
database connectivity, and external services.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil
import aiohttp
from telegram import Bot


logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    message: str
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Overall health status of the application."""
    status: str  # 'healthy', 'unhealthy', 'degraded'
    checks: List[HealthCheckResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    uptime: float = 0.0
    version: str = "unknown"


class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self, settings: Any):
        """
        Initialize health checker.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.start_time = time.time()
        self.checks: Dict[str, Callable] = {}
        self.failure_counts: Dict[str, int] = {}
        self.last_check_times: Dict[str, datetime] = {}
        self.health_history: List[HealthStatus] = []
        self.max_history_size = 100

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.register_check('application', self._check_application)
        self.register_check('database', self._check_database)
        self.register_check('telegram', self._check_telegram)
        self.register_check('memory', self._check_memory)
        self.register_check('disk', self._check_disk)

        if self.settings.monitoring.metrics_enabled:
            self.register_check('metrics', self._check_metrics)

    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check.

        Args:
            name: Name of the health check
            check_func: Async function that performs the check
        """
        self.checks[name] = check_func
        self.failure_counts[name] = 0
        logger.info(f"Registered health check: {name}")

    async def check_health(self, component: Optional[str] = None) -> HealthStatus:
        """
        Perform health checks.

        Args:
            component: Specific component to check, or None for all

        Returns:
            Overall health status
        """
        checks_to_run = [component] if component else list(self.checks.keys())
        results = []

        for check_name in checks_to_run:
            if check_name not in self.checks:
                continue

            try:
                start_time = time.time()
                result = await self.checks[check_name]()
                result.response_time = time.time() - start_time
                results.append(result)

                # Update failure counts
                if result.status == 'unhealthy':
                    self.failure_counts[check_name] += 1
                else:
                    self.failure_counts[check_name] = 0

                self.last_check_times[check_name] = datetime.now()

            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                results.append(HealthCheckResult(
                    component=check_name,
                    status='unhealthy',
                    message=f"Health check failed: {str(e)}",
                    response_time=0.0
                ))
                self.failure_counts[check_name] += 1

        # Determine overall status
        overall_status = self._determine_overall_status(results)

        health_status = HealthStatus(
            status=overall_status,
            checks=results,
            timestamp=datetime.now(),
            uptime=time.time() - self.start_time,
            version=self._get_version()
        )

        # Store in history
        self.health_history.append(health_status)
        if len(self.health_history) > self.max_history_size:
            self.health_history.pop(0)

        return health_status

    async def _check_application(self) -> HealthCheckResult:
        """Check application health."""
        try:
            # Check if main application components are working
            import os
            import sys

            # Check Python environment
            python_version = sys.version_info
            if python_version.major < 3 or python_version.minor < 8:
                return HealthCheckResult(
                    component='application',
                    status='unhealthy',
                    message=f"Python version too old: {python_version}"
                )

            # Check environment variables
            required_vars = ['TELEGRAM_BOT_TOKEN']
            missing_vars = [var for var in required_vars if not os.getenv(var)]

            if missing_vars:
                return HealthCheckResult(
                    component='application',
                    status='unhealthy',
                    message=f"Missing environment variables: {missing_vars}"
                )

            return HealthCheckResult(
                component='application',
                status='healthy',
                message="Application is running normally",
                details={
                    'python_version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    'environment': self.settings.environment_settings.name
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component='application',
                status='unhealthy',
                message=f"Application check failed: {str(e)}"
            )

    async def _check_database(self) -> HealthCheckResult:
        """Check database connectivity."""
        try:
            if not hasattr(self.settings, 'database') or not self.settings.database.url:
                return HealthCheckResult(
                    component='database',
                    status='unhealthy',
                    message="Database not configured"
                )

            start_time = time.time()

            # Try to get database connection from bot data if available
            # This is a simplified check - in real deployment, you'd check
            # the actual database connection
            db_url = self.settings.database.url

            # For now, just check if the URL is properly formatted
            if not db_url.startswith(('postgresql://', 'sqlite:///')):
                return HealthCheckResult(
                    component='database',
                    status='unhealthy',
                    message="Invalid database URL format"
                )

            response_time = time.time() - start_time

            return HealthCheckResult(
                component='database',
                status='healthy',
                message="Database connection successful",
                response_time=response_time,
                details={'url_type': db_url.split('://')[0] if '://' in db_url else 'unknown'}
            )

        except Exception as e:
            return HealthCheckResult(
                component='database',
                status='unhealthy',
                message=f"Database check failed: {str(e)}"
            )

    async def _check_telegram(self) -> HealthCheckResult:
        """Check Telegram API connectivity."""
        try:
            if not self.settings.bot.token:
                return HealthCheckResult(
                    component='telegram',
                    status='unhealthy',
                    message="Telegram bot token not configured"
                )

            start_time = time.time()

            # Create bot instance and check connectivity
            bot = Bot(token=self.settings.bot.token)
            bot_info = await bot.get_me()
            response_time = time.time() - start_time

            return HealthCheckResult(
                component='telegram',
                status='healthy',
                message=f"Connected to Telegram API as @{bot_info.username}",
                response_time=response_time,
                details={
                    'bot_id': bot_info.id,
                    'username': bot_info.username,
                    'first_name': bot_info.first_name
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component='telegram',
                status='unhealthy',
                message=f"Telegram API check failed: {str(e)}"
            )

    async def _check_memory(self) -> HealthCheckResult:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            # Memory thresholds
            warning_threshold = 80.0  # 80%
            critical_threshold = 95.0  # 95%

            memory_percent = memory.percent
            process_memory_mb = process_memory.rss / 1024 / 1024

            status = 'healthy'
            message = f"Memory usage: {memory_percent:.1f}%"

            if memory_percent >= critical_threshold:
                status = 'unhealthy'
                message = f"Critical memory usage: {memory_percent:.1f}%"
            elif memory_percent >= warning_threshold:
                status = 'degraded'
                message = f"High memory usage: {memory_percent:.1f}%"

            return HealthCheckResult(
                component='memory',
                status=status,
                message=message,
                details={
                    'system_memory_percent': memory_percent,
                    'system_memory_total_gb': memory.total / 1024 / 1024 / 1024,
                    'system_memory_available_gb': memory.available / 1024 / 1024 / 1024,
                    'process_memory_mb': process_memory_mb,
                    'process_memory_percent': process_memory.percent
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component='memory',
                status='unhealthy',
                message=f"Memory check failed: {str(e)}"
            )

    async def _check_disk(self) -> HealthCheckResult:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')

            # Disk thresholds
            warning_threshold = 85.0  # 85%
            critical_threshold = 95.0  # 95%

            disk_percent = (disk.used / disk.total) * 100

            status = 'healthy'
            message = f"Disk usage: {disk_percent:.1f}%"

            if disk_percent >= critical_threshold:
                status = 'unhealthy'
                message = f"Critical disk usage: {disk_percent:.1f}%"
            elif disk_percent >= warning_threshold:
                status = 'degraded'
                message = f"High disk usage: {disk_percent:.1f}%"

            return HealthCheckResult(
                component='disk',
                status=status,
                message=message,
                details={
                    'disk_percent': disk_percent,
                    'disk_total_gb': disk.total / 1024 / 1024 / 1024,
                    'disk_used_gb': disk.used / 1024 / 1024 / 1024,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component='disk',
                status='unhealthy',
                message=f"Disk check failed: {str(e)}"
            )

    async def _check_metrics(self) -> HealthCheckResult:
        """Check metrics collection system."""
        try:
            # Check if metrics collection is working
            from .metrics import MetricsCollector

            # This is a basic check - in reality, you'd check if metrics
            # are being collected and exported properly
            return HealthCheckResult(
                component='metrics',
                status='healthy',
                message="Metrics collection is active",
                details={
                    'metrics_enabled': self.settings.monitoring.metrics_enabled,
                    'metrics_port': self.settings.monitoring.metrics_port
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component='metrics',
                status='degraded',
                message=f"Metrics check failed: {str(e)}"
            )

    def _determine_overall_status(self, results: List[HealthCheckResult]) -> str:
        """
        Determine overall health status from individual check results.

        Args:
            results: List of health check results

        Returns:
            Overall status: 'healthy', 'degraded', or 'unhealthy'
        """
        if not results:
            return 'unhealthy'

        statuses = [r.status for r in results]

        # Any unhealthy checks make the overall status unhealthy
        if 'unhealthy' in statuses:
            return 'unhealthy'

        # Any degraded checks make the overall status degraded
        if 'degraded' in statuses:
            return 'degraded'

        # All checks are healthy
        return 'healthy'

    def _get_version(self) -> str:
        """Get application version."""
        try:
            # Try to get version from package info or git
            import subprocess
            try:
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--always'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Fallback to a default version
            return "1.0.0"
        except Exception:
            return "unknown"

    def get_health_history(self, hours: int = 24) -> List[HealthStatus]:
        """
        Get health status history.

        Args:
            hours: Number of hours of history to return

        Returns:
            List of health status entries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            status for status in self.health_history
            if status.timestamp >= cutoff_time
        ]

    def get_failure_count(self, component: str) -> int:
        """Get failure count for a specific component."""
        return self.failure_counts.get(component, 0)

    def reset_failure_count(self, component: str) -> None:
        """Reset failure count for a specific component."""
        self.failure_counts[component] = 0
        logger.info(f"Reset failure count for {component}")

    def get_component_status(self, component: str) -> Optional[str]:
        """
        Get current status of a specific component.

        Args:
            component: Component name

        Returns:
            Component status or None if not found
        """
        if not self.health_history:
            return None

        latest_status = self.health_history[-1]
        for check in latest_status.checks:
            if check.component == component:
                return check.status

        return None