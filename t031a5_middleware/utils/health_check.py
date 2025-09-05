"""Health check system for t031a5_middleware.

Provides health monitoring and status checking for all system modules.
"""

import asyncio
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable

from .logger import get_logger
from .metrics import get_metrics_collector, gauge


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration
        }


class HealthCheck(ABC):
    """Base health check class."""
    
    def __init__(self, name: str, description: str = "", 
                 timeout: float = 5.0, critical: bool = False):
        self.name = name
        self.description = description
        self.timeout = timeout
        self.critical = critical
        self.logger = get_logger(f"health.{name}")
    
    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Perform the health check."""
        pass
    
    async def run_check(self) -> HealthCheckResult:
        """Run the health check with timeout and error handling."""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(self.check(), timeout=self.timeout)
            result.duration = time.time() - start_time
            return result
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.logger.warning(f"Health check '{self.name}' timed out after {duration:.2f}s")
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL if self.critical else HealthStatus.WARNING,
                message=f"Health check timed out after {self.timeout}s",
                duration=duration
            )
        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Health check '{self.name}' failed: {e}")
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL if self.critical else HealthStatus.WARNING,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "type": type(e).__name__},
                duration=duration
            )


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity health check."""
    
    def __init__(self, db_connection_func: Callable[[], Awaitable[bool]]):
        super().__init__("database", "Database connectivity check", critical=True)
        self.db_connection_func = db_connection_func
    
    async def check(self) -> HealthCheckResult:
        """Check database connectivity."""
        try:
            is_connected = await self.db_connection_func()
            
            if is_connected:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Database connection is healthy"
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.CRITICAL,
                    message="Database connection failed"
                )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Database check failed: {str(e)}",
                details={"error": str(e)}
            )


class ModuleHealthCheck(HealthCheck):
    """Generic module health check."""
    
    def __init__(self, module_name: str, status_func: Callable[[], Awaitable[Dict[str, Any]]]):
        super().__init__(f"module_{module_name}", f"{module_name} module health check")
        self.module_name = module_name
        self.status_func = status_func
    
    async def check(self) -> HealthCheckResult:
        """Check module status."""
        try:
            status_info = await self.status_func()
            
            # Determine status based on module info
            is_running = status_info.get("running", False)
            error_count = status_info.get("error_count", 0)
            last_error = status_info.get("last_error")
            
            if not is_running:
                status = HealthStatus.CRITICAL
                message = f"Module {self.module_name} is not running"
            elif error_count > 10:
                status = HealthStatus.WARNING
                message = f"Module {self.module_name} has high error count: {error_count}"
            elif last_error and (datetime.now() - last_error).seconds < 300:
                status = HealthStatus.WARNING
                message = f"Module {self.module_name} had recent errors"
            else:
                status = HealthStatus.HEALTHY
                message = f"Module {self.module_name} is healthy"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=status_info
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Module {self.module_name} check failed: {str(e)}",
                details={"error": str(e)}
            )


class ResourceHealthCheck(HealthCheck):
    """System resource health check."""
    
    def __init__(self, cpu_threshold: float = 90.0, memory_threshold: float = 90.0, 
                 disk_threshold: float = 90.0):
        super().__init__("resources", "System resource health check")
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def check(self) -> HealthCheckResult:
        """Check system resources."""
        try:
            import psutil
            
            # Get resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            disk_percent = (disk.used / disk.total) * 100
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk_percent,
                "memory_available": memory.available,
                "disk_free": disk.free
            }
            
            # Determine status
            issues = []
            
            if cpu_percent > self.cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > self.memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            if disk_percent > self.disk_threshold:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            if issues:
                status = HealthStatus.WARNING
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.WARNING,
                message=f"Resource check failed: {str(e)}",
                details={"error": str(e)}
            )


class NetworkHealthCheck(HealthCheck):
    """Network connectivity health check."""
    
    def __init__(self, hosts: List[str] = None, ports: List[int] = None):
        super().__init__("network", "Network connectivity health check")
        self.hosts = hosts or ["8.8.8.8", "1.1.1.1"]
        self.ports = ports or [80, 443]
    
    async def check(self) -> HealthCheckResult:
        """Check network connectivity."""
        try:
            import socket
            
            connectivity_results = []
            
            for host in self.hosts:
                for port in self.ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2.0)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        
                        connectivity_results.append({
                            "host": host,
                            "port": port,
                            "connected": result == 0
                        })
                    
                    except Exception as e:
                        connectivity_results.append({
                            "host": host,
                            "port": port,
                            "connected": False,
                            "error": str(e)
                        })
            
            # Check if any connections succeeded
            successful_connections = sum(1 for r in connectivity_results if r["connected"])
            total_connections = len(connectivity_results)
            
            details = {
                "connectivity_results": connectivity_results,
                "successful_connections": successful_connections,
                "total_connections": total_connections
            }
            
            if successful_connections == 0:
                status = HealthStatus.CRITICAL
                message = "No network connectivity"
            elif successful_connections < total_connections / 2:
                status = HealthStatus.WARNING
                message = f"Limited network connectivity: {successful_connections}/{total_connections}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Network connectivity is healthy: {successful_connections}/{total_connections}"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.WARNING,
                message=f"Network check failed: {str(e)}",
                details={"error": str(e)}
            )


class HealthMonitor:
    """Central health monitoring system."""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.logger = get_logger("health_monitor")
        self.metrics = get_metrics_collector()
        
        # Health metrics
        self.health_status_gauge = gauge("health_status", "Health status (1=healthy, 0=unhealthy)")
        self.health_check_duration = self.metrics.timer("health_check_duration_seconds", "Health check duration")
        
        # Monitoring thread
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        
        # Setup default checks
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """Setup default health checks."""
        # Resource check
        self.add_check(ResourceHealthCheck())
        
        # Network check
        self.add_check(NetworkHealthCheck())
    
    def add_check(self, check: HealthCheck):
        """Add a health check."""
        self.checks[check.name] = check
        self.logger.info(f"Added health check: {check.name}")
    
    def remove_check(self, name: str):
        """Remove a health check."""
        if name in self.checks:
            del self.checks[name]
            if name in self.results:
                del self.results[name]
            self.logger.info(f"Removed health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}
        
        # Run checks concurrently
        tasks = []
        for name, check in self.checks.items():
            task = asyncio.create_task(check.run_check())
            tasks.append((name, task))
        
        # Wait for all checks to complete
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                
                # Update metrics
                status_value = 1.0 if result.status == HealthStatus.HEALTHY else 0.0
                self.health_status_gauge.set(status_value, {"check": name})
                self.health_check_duration.record(result.duration, {"check": name})
                
            except Exception as e:
                self.logger.error(f"Failed to run health check '{name}': {e}")
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Check execution failed: {str(e)}"
                )
        
        self.results = results
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self.results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        overall_status = self.get_overall_status()
        
        summary = {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in self.results.items()}
        }
        
        # Add statistics
        if self.results:
            statuses = [result.status for result in self.results.values()]
            summary["statistics"] = {
                "total_checks": len(self.results),
                "healthy": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
                "warning": sum(1 for s in statuses if s == HealthStatus.WARNING),
                "critical": sum(1 for s in statuses if s == HealthStatus.CRITICAL),
                "unknown": sum(1 for s in statuses if s == HealthStatus.UNKNOWN)
            }
        
        return summary
    
    def start_monitoring(self, interval: float = 60.0):
        """Start background health monitoring."""
        if self._monitoring_thread is not None:
            return
        
        def monitor_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                while not self._stop_monitoring.wait(interval):
                    try:
                        loop.run_until_complete(self.run_all_checks())
                        
                        # Log overall status
                        overall_status = self.get_overall_status()
                        if overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                            self.logger.warning(f"System health status: {overall_status.value}")
                        
                    except Exception as e:
                        self.logger.error(f"Error during health monitoring: {e}")
            
            finally:
                loop.close()
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
        self.logger.info("Started health monitoring")
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        if self._monitoring_thread is None:
            return
        
        self._stop_monitoring.set()
        self._monitoring_thread.join(timeout=5.0)
        self._monitoring_thread = None
        self.logger.info("Stopped health monitoring")


# Global health monitor
_global_monitor = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor."""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = HealthMonitor()
    
    return _global_monitor


# Convenience functions
def add_health_check(check: HealthCheck):
    """Add a health check to the global monitor."""
    get_health_monitor().add_check(check)


def add_module_check(module_name: str, status_func: Callable[[], Awaitable[Dict[str, Any]]]):
    """Add a module health check."""
    check = ModuleHealthCheck(module_name, status_func)
    add_health_check(check)


def add_database_check(db_connection_func: Callable[[], Awaitable[bool]]):
    """Add a database health check."""
    check = DatabaseHealthCheck(db_connection_func)
    add_health_check(check)


async def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
    monitor = get_health_monitor()
    await monitor.run_all_checks()
    return monitor.get_health_summary()