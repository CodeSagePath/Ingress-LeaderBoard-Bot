"""
Metrics collection system for the Ingress Prime Leaderboard Bot.

Provides comprehensive metrics collection for performance monitoring,
bot activity, and system health.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json


logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric over a time period."""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    last: Optional[float] = None


class MetricsCollector:
    """Comprehensive metrics collection system."""

    def __init__(self, settings: Any):
        """
        Initialize metrics collector.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.monitoring.metrics_enabled

        # Metric storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # Metric history
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        # Thread safety
        self.lock = threading.RLock()

        # Background collection thread
        self.collection_thread: Optional[threading.Thread] = None
        self.running = False

        # Auto-collection callbacks
        self.auto_collect_callbacks: List[Callable] = []

        if self.enabled:
            self.start_collection()

    def start_collection(self) -> None:
        """Start background metrics collection."""
        if self.running:
            return

        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collection_worker,
            daemon=True,
            name="MetricsCollector"
        )
        self.collection_thread.start()
        logger.info("Started metrics collection")

    def stop_collection(self) -> None:
        """Stop background metrics collection."""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")

    def _collection_worker(self) -> None:
        """Background worker for automatic metric collection."""
        interval = 30  # Collect every 30 seconds

        while self.running:
            try:
                # Run auto-collection callbacks
                for callback in self.auto_collect_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Auto-collection callback failed: {e}")

                # Collect system metrics
                self._collect_system_metrics()

                # Clean old metrics
                self._cleanup_old_metrics()

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

            time.sleep(interval)

    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge('system_cpu_percent', cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge('system_memory_percent', memory.percent)
            self.set_gauge('system_memory_available_bytes', memory.available)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.set_gauge('system_disk_percent', (disk.used / disk.total) * 100)
            self.set_gauge('system_disk_free_bytes', disk.free)

            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self.set_gauge('process_memory_rss_bytes', process_memory.rss)
            self.set_gauge('process_memory_vms_bytes', process_memory.vms)
            self.set_gauge('process_cpu_percent', process.cpu_percent())
            self.set_gauge('process_num_threads', process.num_threads())
            self.set_gauge('process_num_fds', process.num_fds())

        except ImportError:
            logger.warning("psutil not available, system metrics disabled")
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metric data to prevent memory leaks."""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours

        with self.lock:
            for metric_name, history in self.metric_history.items():
                # Remove old entries
                while history and history[0].timestamp < cutoff_time:
                    history.popleft()

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1.0)
            labels: Optional metric labels
        """
        if not self.enabled:
            return

        with self.lock:
            full_name = self._format_metric_name(name, labels)
            self.counters[full_name] += value

            # Add to history
            metric_value = MetricValue(value=self.counters[full_name], labels=labels or {})
            self.metric_history[full_name].append(metric_value)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional metric labels
        """
        if not self.enabled:
            return

        with self.lock:
            full_name = self._format_metric_name(name, labels)
            self.gauges[full_name] = value

            # Add to history
            metric_value = MetricValue(value=value, labels=labels or {})
            self.metric_history[full_name].append(metric_value)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """
        Record a histogram metric.

        Args:
            name: Metric name
            value: Histogram value
            labels: Optional metric labels
        """
        if not self.enabled:
            return

        with self.lock:
            full_name = self._format_metric_name(name, labels)
            self.histograms[full_name].append(value)

            # Add to history
            metric_value = MetricValue(value=value, labels=labels or {})
            self.metric_history[full_name].append(metric_value)

    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None) -> None:
        """
        Record a timer metric.

        Args:
            name: Metric name
            duration: Duration in seconds
            labels: Optional metric labels
        """
        if not self.enabled:
            return

        with self.lock:
            full_name = self._format_metric_name(name, labels)
            self.timers[full_name].append(duration)

            # Keep only recent timer values
            if len(self.timers[full_name]) > 1000:
                self.timers[full_name] = self.timers[full_name][-1000:]

            # Add to history
            metric_value = MetricValue(value=duration, labels=labels or {})
            self.metric_history[full_name].append(metric_value)

    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get counter value."""
        full_name = self._format_metric_name(name, labels)
        return self.counters.get(full_name, 0.0)

    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Get gauge value."""
        full_name = self._format_metric_name(name, labels)
        return self.gauges.get(full_name)

    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> MetricSummary:
        """Get histogram statistics."""
        full_name = self._format_metric_name(name, labels)
        values = list(self.histograms.get(full_name, []))

        if not values:
            return MetricSummary()

        summary = MetricSummary(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values),
            last=values[-1] if values else None
        )

        return summary

    def get_timer_stats(self, name: str, labels: Dict[str, str] = None) -> MetricSummary:
        """Get timer statistics."""
        full_name = self._format_metric_name(name, labels)
        values = self.timers.get(full_name, [])

        if not values:
            return MetricSummary()

        summary = MetricSummary(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values),
            last=values[-1] if values else None
        )

        return summary

    def _format_metric_name(self, name: str, labels: Dict[str, str] = None) -> str:
        """Format metric name with labels."""
        if not labels:
            return name

        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self.lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    name: self.get_histogram_stats(name)._asdict()
                    for name in self.histograms.keys()
                },
                'timers': {
                    name: self.get_timer_stats(name)._asdict()
                    for name in self.timers.keys()
                }
            }

    def get_metric_history(self, name: str, labels: Dict[str, str] = None,
                          hours: int = 1) -> List[MetricValue]:
        """
        Get metric history.

        Args:
            name: Metric name
            labels: Optional metric labels
            hours: Number of hours of history to return

        Returns:
            List of metric values
        """
        full_name = self._format_metric_name(name, labels)
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.lock:
            history = list(self.metric_history.get(full_name, []))
            return [mv for mv in history if mv.timestamp >= cutoff_time]

    def reset_metric(self, name: str, labels: Dict[str, str] = None) -> None:
        """Reset a metric."""
        full_name = self._format_metric_name(name, labels)

        with self.lock:
            self.counters.pop(full_name, None)
            self.gauges.pop(full_name, None)
            self.histograms.pop(full_name, None)
            self.timers.pop(full_name, None)
            self.metric_history.pop(full_name, None)

    def reset_all_metrics(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
            self.metric_history.clear()

    def register_auto_collector(self, callback: Callable) -> None:
        """
        Register a callback for automatic metric collection.

        Args:
            callback: Function that collects and records metrics
        """
        self.auto_collect_callbacks.append(callback)

    def export_json(self) -> str:
        """Export metrics as JSON."""
        metrics = self.get_all_metrics()

        # Convert datetime objects to strings
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, MetricValue):
                return {
                    'value': obj.value,
                    'timestamp': obj.timestamp.isoformat(),
                    'labels': obj.labels
                }
            return obj

        return json.dumps(metrics, default=serialize_datetime, indent=2)

    # Bot-specific metric helpers
    def record_bot_command(self, command: str, user_id: int, chat_id: int) -> None:
        """Record a bot command execution."""
        self.increment_counter('bot_commands_total', labels={'command': command})
        self.increment_counter('bot_users_total', labels={'user_id': str(user_id)})
        self.increment_counter('bot_chats_total', labels={'chat_id': str(chat_id)})

    def record_leaderboard_request(self, category: str, limit: int) -> None:
        """Record a leaderboard request."""
        self.increment_counter('leaderboard_requests_total', labels={'category': category})
        self.record_histogram('leaderboard_request_limit', limit, labels={'category': category})

    def record_database_query(self, table: str, operation: str, duration: float) -> None:
        """Record a database query."""
        self.increment_counter('database_queries_total', labels={'table': table, 'operation': operation})
        self.record_timer('database_query_duration', duration, labels={'table': table, 'operation': operation})

    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float) -> None:
        """Record an API request."""
        labels = {'endpoint': endpoint, 'method': method, 'status_code': str(status_code)}
        self.increment_counter('api_requests_total', labels=labels)
        self.record_timer('api_request_duration', duration, labels=labels)

    def record_error(self, error_type: str, component: str) -> None:
        """Record an error."""
        self.increment_counter('errors_total', labels={'type': error_type, 'component': component})


class Timer:
    """Context manager for timing operations."""

    def __init__(self, metrics: MetricsCollector, name: str, labels: Dict[str, str] = None):
        self.metrics = metrics
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.metrics.record_timer(self.name, duration, self.labels)