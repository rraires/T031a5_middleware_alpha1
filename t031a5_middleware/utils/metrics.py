"""Performance metrics system for t031a5_middleware.

Provides metrics collection, aggregation, and reporting capabilities.
"""

import time
import threading
import psutil
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager
from enum import Enum

from .logger import get_logger


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Individual metric value."""
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


class Metric:
    """Base metric class."""
    
    def __init__(self, name: str, metric_type: MetricType, 
                 description: str = "", labels: Dict[str, str] = None):
        self.name = name
        self.type = metric_type
        self.description = description
        self.labels = labels or {}
        self.values = deque(maxlen=1000)  # Keep last 1000 values
        self._lock = threading.Lock()
    
    def add_value(self, value: float, labels: Dict[str, str] = None):
        """Add a value to the metric."""
        with self._lock:
            metric_labels = {**self.labels, **(labels or {})}
            self.values.append(MetricValue(
                value=value,
                timestamp=datetime.now(),
                labels=metric_labels
            ))
    
    def get_summary(self, since: datetime = None) -> MetricSummary:
        """Get summary statistics."""
        with self._lock:
            values = list(self.values)
        
        if since:
            values = [v for v in values if v.timestamp >= since]
        
        if not values:
            return MetricSummary()
        
        numeric_values = [v.value for v in values]
        numeric_values.sort()
        
        count = len(numeric_values)
        total = sum(numeric_values)
        
        summary = MetricSummary(
            count=count,
            sum=total,
            min=min(numeric_values),
            max=max(numeric_values),
            avg=total / count if count > 0 else 0.0
        )
        
        # Calculate percentiles
        if count > 0:
            summary.p50 = numeric_values[int(count * 0.5)]
            summary.p95 = numeric_values[int(count * 0.95)]
            summary.p99 = numeric_values[int(count * 0.99)]
        
        return summary


class Counter(Metric):
    """Counter metric - monotonically increasing value."""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, MetricType.COUNTER, description, labels)
        self._value = 0.0
    
    def increment(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """Increment counter."""
        with self._lock:
            self._value += amount
            self.add_value(self._value, labels)
    
    def get_value(self) -> float:
        """Get current counter value."""
        return self._value


class Gauge(Metric):
    """Gauge metric - can go up and down."""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, MetricType.GAUGE, description, labels)
        self._value = 0.0
    
    def set(self, value: float, labels: Dict[str, str] = None):
        """Set gauge value."""
        with self._lock:
            self._value = value
            self.add_value(value, labels)
    
    def increment(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """Increment gauge."""
        with self._lock:
            self._value += amount
            self.add_value(self._value, labels)
    
    def decrement(self, amount: float = 1.0, labels: Dict[str, str] = None):
        """Decrement gauge."""
        self.increment(-amount, labels)
    
    def get_value(self) -> float:
        """Get current gauge value."""
        return self._value


class Histogram(Metric):
    """Histogram metric - tracks distribution of values."""
    
    def __init__(self, name: str, description: str = "", 
                 buckets: List[float] = None, labels: Dict[str, str] = None):
        super().__init__(name, MetricType.HISTOGRAM, description, labels)
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.bucket_counts = defaultdict(int)
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """Observe a value."""
        with self._lock:
            self.add_value(value, labels)
            
            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self.bucket_counts[bucket] += 1


class Timer(Metric):
    """Timer metric - measures duration."""
    
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, MetricType.TIMER, description, labels)
    
    def time(self, labels: Dict[str, str] = None):
        """Context manager for timing operations."""
        return TimerContext(self, labels)
    
    def record(self, duration: float, labels: Dict[str, str] = None):
        """Record a duration."""
        self.add_value(duration, labels)


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, timer: Timer, labels: Dict[str, str] = None):
        self.timer = timer
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.timer.record(duration, self.labels)


class MetricsCollector:
    """Central metrics collector."""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        self.logger = get_logger("metrics")
        
        # System metrics
        self._setup_system_metrics()
        
        # Start background collection
        self._collection_thread = None
        self._stop_collection = threading.Event()
    
    def _setup_system_metrics(self):
        """Setup system-level metrics."""
        self.cpu_usage = self.gauge("system_cpu_usage_percent", "CPU usage percentage")
        self.memory_usage = self.gauge("system_memory_usage_bytes", "Memory usage in bytes")
        self.memory_percent = self.gauge("system_memory_usage_percent", "Memory usage percentage")
        self.disk_usage = self.gauge("system_disk_usage_percent", "Disk usage percentage")
        
        # Module-specific metrics
        self.module_status = self.gauge("module_status", "Module status (1=running, 0=stopped)")
        self.api_requests = self.counter("api_requests_total", "Total API requests")
        self.api_request_duration = self.timer("api_request_duration_seconds", "API request duration")
        self.robot_commands = self.counter("robot_commands_total", "Total robot commands")
        self.sensor_readings = self.counter("sensor_readings_total", "Total sensor readings")
        self.websocket_connections = self.gauge("websocket_connections", "Active WebSocket connections")
    
    def counter(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Counter:
        """Create or get a counter metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Counter(name, description, labels)
            return self.metrics[name]
    
    def gauge(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Gauge:
        """Create or get a gauge metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Gauge(name, description, labels)
            return self.metrics[name]
    
    def histogram(self, name: str, description: str = "", 
                 buckets: List[float] = None, labels: Dict[str, str] = None) -> Histogram:
        """Create or get a histogram metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Histogram(name, description, buckets, labels)
            return self.metrics[name]
    
    def timer(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Timer:
        """Create or get a timer metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Timer(name, description, labels)
            return self.metrics[name]
    
    def collect_system_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            self.memory_percent.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage.set((disk.used / disk.total) * 100)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def start_collection(self, interval: float = 30.0):
        """Start background metrics collection."""
        if self._collection_thread is not None:
            return
        
        def collect_loop():
            while not self._stop_collection.wait(interval):
                self.collect_system_metrics()
        
        self._collection_thread = threading.Thread(target=collect_loop, daemon=True)
        self._collection_thread.start()
        self.logger.info("Started metrics collection")
    
    def stop_collection(self):
        """Stop background metrics collection."""
        if self._collection_thread is None:
            return
        
        self._stop_collection.set()
        self._collection_thread.join(timeout=5.0)
        self._collection_thread = None
        self.logger.info("Stopped metrics collection")
    
    def get_all_metrics(self) -> Dict[str, MetricSummary]:
        """Get summary of all metrics."""
        result = {}
        with self._lock:
            for name, metric in self.metrics.items():
                result[name] = metric.get_summary()
        return result
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        with self._lock:
            for name, metric in self.metrics.items():
                # Add help text
                if metric.description:
                    lines.append(f"# HELP {name} {metric.description}")
                
                # Add type
                lines.append(f"# TYPE {name} {metric.type.value}")
                
                # Add values
                if isinstance(metric, (Counter, Gauge)):
                    value = metric.get_value()
                    lines.append(f"{name} {value}")
                elif isinstance(metric, (Timer, Histogram)):
                    summary = metric.get_summary()
                    lines.append(f"{name}_count {summary.count}")
                    lines.append(f"{name}_sum {summary.sum}")
                    lines.append(f"{name}_avg {summary.avg}")
        
        return "\n".join(lines)


# Global metrics collector
_global_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _global_collector
    
    if _global_collector is None:
        _global_collector = MetricsCollector()
    
    return _global_collector


# Convenience functions
def counter(name: str, description: str = "", labels: Dict[str, str] = None) -> Counter:
    """Create or get a counter metric."""
    return get_metrics_collector().counter(name, description, labels)


def gauge(name: str, description: str = "", labels: Dict[str, str] = None) -> Gauge:
    """Create or get a gauge metric."""
    return get_metrics_collector().gauge(name, description, labels)


def histogram(name: str, description: str = "", 
             buckets: List[float] = None, labels: Dict[str, str] = None) -> Histogram:
    """Create or get a histogram metric."""
    return get_metrics_collector().histogram(name, description, buckets, labels)


def timer(name: str, description: str = "", labels: Dict[str, str] = None) -> Timer:
    """Create or get a timer metric."""
    return get_metrics_collector().timer(name, description, labels)


@contextmanager
def time_operation(name: str, labels: Dict[str, str] = None):
    """Context manager for timing operations."""
    timer_metric = timer(f"{name}_duration_seconds", f"Duration of {name} operation", labels)
    with timer_metric.time(labels):
        yield