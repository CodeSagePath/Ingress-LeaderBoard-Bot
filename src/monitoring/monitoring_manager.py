"""
Monitoring manager that coordinates health checks and metrics collection.

Provides a unified interface for all monitoring functionality.
"""

import asyncio
import logging
from typing import Any, Optional, Dict
from aiohttp import web
import json

from .health_checker import HealthChecker
from .metrics import MetricsCollector, Timer
from .prometheus_exporter import PrometheusExporter


logger = logging.getLogger(__name__)


class MonitoringManager:
    """Unified monitoring management system."""

    def __init__(self, settings: Any):
        """
        Initialize monitoring manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.monitoring.enabled

        if not self.enabled:
            logger.info("Monitoring is disabled")
            return

        # Initialize components
        self.health_checker = HealthChecker(settings)
        self.metrics_collector = MetricsCollector(settings)
        self.prometheus_exporter = PrometheusExporter(self.metrics_collector)

        # HTTP server for metrics and health endpoints
        self.app = web.Application()
        self.site: Optional[web.TCPSite] = None
        self.runner: Optional[web.AppRunner] = None

        # Set up routes
        self._setup_routes()

        # Register auto-metrics collection
        self._register_auto_metrics()

        logger.info(f"Monitoring manager initialized (metrics_port: {settings.monitoring.metrics_port})")

    def _setup_routes(self) -> None:
        """Set up HTTP routes for monitoring endpoints."""
        self.app.router.add_get('/health', self._health_endpoint)
        self.app.router.add_get('/health/{component}', self._health_component_endpoint)
        self.app.router.add_get('/metrics', self._metrics_endpoint)
        self.app.router.add_get('/metrics/prometheus', self._prometheus_endpoint)
        self.app.router.add_get('/status', self._status_endpoint)

    def _register_auto_metrics(self) -> None:
        """Register automatic metrics collection callbacks."""
        # Collect health status as a metric
        def collect_health_metrics():
            try:
                health_status = asyncio.create_task(
                    self.health_checker.check_health()
                )
                # Set gauges for overall status
                self.metrics_collector.set_gauge('health_overall', 1.0 if health_status.status == 'healthy' else 0.0)
            except Exception as e:
                logger.error(f"Health metrics collection failed: {e}")

        self.metrics_collector.register_auto_collector(collect_health_metrics)

    async def start(self) -> None:
        """Start the monitoring HTTP server."""
        if not self.enabled:
            return

        try:
            # Create and configure runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            # Create and start site
            port = self.settings.monitoring.metrics_port
            self.site = web.TCPSite(self.runner, '0.0.0.0', port)
            await self.site.start()

            logger.info(f"Monitoring server started on port {port}")
            logger.info(f"Health endpoint: http://localhost:{port}/health")
            logger.info(f"Metrics endpoint: http://localhost:{port}/metrics")
            logger.info(f"Prometheus endpoint: http://localhost:{port}/metrics/prometheus")

        except Exception as e:
            logger.error(f"Failed to start monitoring server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the monitoring HTTP server."""
        if not self.enabled:
            return

        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()

            # Stop metrics collection
            self.metrics_collector.stop_collection()

            logger.info("Monitoring server stopped")

        except Exception as e:
            logger.error(f"Error stopping monitoring server: {e}")

    # HTTP endpoint handlers
    async def _health_endpoint(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        try:
            health_status = await self.health_checker.check_health()
            return web.json_response({
                'status': health_status.status,
                'timestamp': health_status.timestamp.isoformat(),
                'uptime': health_status.uptime,
                'checks': [
                    {
                        'component': check.component,
                        'status': check.status,
                        'message': check.message,
                        'response_time': check.response_time,
                        'details': check.details
                    }
                    for check in health_status.checks
                ]
            })
        except Exception as e:
            logger.error(f"Health check endpoint error: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    async def _health_component_endpoint(self, request: web.Request) -> web.Response:
        """Health check endpoint for specific component."""
        try:
            component = request.match_info['component']
            health_status = await self.health_checker.check_health(component)

            if health_status.checks:
                check = health_status.checks[0]
                return web.json_response({
                    'component': check.component,
                    'status': check.status,
                    'message': check.message,
                    'response_time': check.response_time,
                    'timestamp': check.timestamp.isoformat(),
                    'details': check.details
                })
            else:
                return web.json_response(
                    {'error': f'Component {component} not found'},
                    status=404
                )

        except Exception as e:
            logger.error(f"Component health check endpoint error: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    async def _metrics_endpoint(self, request: web.Request) -> web.Response:
        """Metrics endpoint in JSON format."""
        try:
            metrics = self.metrics_collector.get_all_metrics()
            return web.json_response(metrics)
        except Exception as e:
            logger.error(f"Metrics endpoint error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _prometheus_endpoint(self, request: web.Request) -> web.Response:
        """Metrics endpoint in Prometheus format."""
        try:
            metrics_text = self.prometheus_exporter.export_metrics()
            return web.Response(
                text=metrics_text,
                content_type='text/plain; version=0.0.4'
            )
        except Exception as e:
            logger.error(f"Prometheus metrics endpoint error: {e}")
            return web.Response(
                text=f"# Error generating metrics: {str(e)}",
                content_type='text/plain',
                status=500
            )

    async def _status_endpoint(self, request: web.Request) -> web.Response:
        """Overall status endpoint."""
        try:
            health_status = await self.health_checker.check_health()
            metrics = self.metrics_collector.get_all_metrics()

            return web.json_response({
                'status': health_status.status,
                'uptime': health_status.uptime,
                'timestamp': health_status.timestamp.isoformat(),
                'version': health_status.version,
                'monitoring': {
                    'enabled': self.enabled,
                    'metrics_enabled': self.settings.monitoring.metrics_enabled,
                    'health_checks_enabled': self.settings.monitoring.health_check_enabled
                },
                'metrics_summary': {
                    'counters_count': len(metrics.get('counters', {})),
                    'gauges_count': len(metrics.get('gauges', {})),
                    'histograms_count': len(metrics.get('histograms', {})),
                    'timers_count': len(metrics.get('timers', {}))
                },
                'health_summary': {
                    'total_checks': len(health_status.checks),
                    'healthy_checks': len([c for c in health_status.checks if c.status == 'healthy']),
                    'unhealthy_checks': len([c for c in health_status.checks if c.status == 'unhealthy']),
                    'degraded_checks': len([c for c in health_status.checks if c.status == 'degraded'])
                }
            })
        except Exception as e:
            logger.error(f"Status endpoint error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    # Convenience methods for common operations
    def record_bot_command(self, command: str, user_id: int, chat_id: int) -> None:
        """Record a bot command execution."""
        if self.enabled:
            self.metrics_collector.record_bot_command(command, user_id, chat_id)

    def record_leaderboard_request(self, category: str, limit: int) -> None:
        """Record a leaderboard request."""
        if self.enabled:
            self.metrics_collector.record_leaderboard_request(category, limit)

    def record_database_query(self, table: str, operation: str, duration: float) -> None:
        """Record a database query."""
        if self.enabled:
            self.metrics_collector.record_database_query(table, operation, duration)

    def record_error(self, error_type: str, component: str) -> None:
        """Record an error."""
        if self.enabled:
            self.metrics_collector.record_error(error_type, component)

    def timer(self, name: str, labels: Dict[str, str] = None) -> Timer:
        """Create a timer context manager."""
        if self.enabled:
            return Timer(self.metrics_collector, name, labels)
        else:
            # Return a no-op timer if monitoring is disabled
            return NoOpTimer()

    async def check_health(self, component: Optional[str] = None):
        """Check health status."""
        if self.enabled:
            return await self.health_checker.check_health(component)
        else:
            # Return a basic health status if monitoring is disabled
            from .health_checker import HealthStatus
            return HealthStatus(status='healthy', timestamp=datetime.now(), uptime=0.0)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if self.enabled:
            return self.metrics_collector.get_all_metrics()
        else:
            return {}

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        if self.enabled:
            self.metrics_collector.reset_all_metrics()


class NoOpTimer:
    """No-operation timer for when monitoring is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass