"""
Prometheus metrics exporter for the Ingress Prime Leaderboard Bot.

Exports collected metrics in Prometheus format for monitoring.
"""

import logging
from typing import Dict, Any, TextIO
from .metrics import MetricsCollector


logger = logging.getLogger(__name__)


class PrometheusExporter:
    """Exports metrics in Prometheus format."""

    def __init__(self, metrics: MetricsCollector, namespace: str = "ingress_bot"):
        """
        Initialize Prometheus exporter.

        Args:
            metrics: Metrics collector instance
            namespace: Metric namespace prefix
        """
        self.metrics = metrics
        self.namespace = namespace

    def export_metrics(self) -> str:
        """
        Export all metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        output = []

        # Export counters
        for name, value in self.metrics.counters.items():
            prometheus_name = self._to_prometheus_name(name, "counter")
            output.append(f"# HELP {prometheus_name} Total count")
            output.append(f"# TYPE {prometheus_name} counter")
            output.append(f"{prometheus_name} {value}")
            output.append("")

        # Export gauges
        for name, value in self.metrics.gauges.items():
            prometheus_name = self._to_prometheus_name(name, "gauge")
            output.append(f"# HELP {prometheus_name} Current value")
            output.append(f"# TYPE {prometheus_name} gauge")
            output.append(f"{prometheus_name} {value}")
            output.append("")

        # Export histograms (basic implementation)
        for name, values in self.metrics.histograms.items():
            if values:
                prometheus_name = self._to_prometheus_name(name, "histogram")
                output.append(f"# HELP {prometheus_name} Histogram")
                output.append(f"# TYPE {prometheus_name} histogram")

                # Simple histogram implementation
                sorted_values = sorted(values)
                count = len(sorted_values)
                total = sum(sorted_values)

                output.append(f"{prometheus_name}_count {count}")
                output.append(f"{prometheus_name}_sum {total}")
                output.append("")

        # Export timers (as histograms)
        for name, values in self.metrics.timers.items():
            if values:
                prometheus_name = self._to_prometheus_name(name, "timer")
                output.append(f"# HELP {prometheus_name} Timer duration")
                output.append(f"# TYPE {prometheus_name} histogram")

                sorted_values = sorted(values)
                count = len(sorted_values)
                total = sum(sorted_values)

                output.append(f"{prometheus_name}_count {count}")
                output.append(f"{prometheus_name}_sum {total}")

                # Add quantiles
                if count > 0:
                    for quantile in [0.5, 0.9, 0.95, 0.99]:
                        index = int(quantile * (count - 1))
                        value = sorted_values[index]
                        output.append(f"{prometheus_name}_bucket{{le=\"+Inf\"}} {count}")
                        output.append(f"{prometheus_name}_bucket{{le=\"{value}\"}} {count}")

                output.append("")

        return "\n".join(output)

    def _to_prometheus_name(self, name: str, metric_type: str) -> str:
        """
        Convert metric name to Prometheus format.

        Args:
            name: Original metric name
            metric_type: Type of metric (counter, gauge, etc.)

        Returns:
            Prometheus-formatted metric name
        """
        # Replace dots and spaces with underscores
        clean_name = name.replace('.', '_').replace(' ', '_')

        # Add namespace prefix
        if self.namespace:
            prometheus_name = f"{self.namespace}_{clean_name}"
        else:
            prometheus_name = clean_name

        return prometheus_name

    def write_metrics(self, output: TextIO) -> None:
        """
        Write metrics to a file-like object.

        Args:
            output: File-like object to write to
        """
        metrics_text = self.export_metrics()
        output.write(metrics_text)
        output.flush()