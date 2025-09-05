"""Logging system for t031a5_middleware.

Provides structured logging with different levels, formatters, and handlers.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Log levels enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class MiddlewareLogger:
    """Main logger class for the middleware."""
    
    def __init__(self, name: str = "t031a5_middleware"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers."""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "middleware.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "errors.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
    
    def log_module_start(self, module_name: str, **kwargs):
        """Log module startup."""
        self.info(f"Starting module: {module_name}", 
                 module=module_name, event="module_start", **kwargs)
    
    def log_module_stop(self, module_name: str, **kwargs):
        """Log module shutdown."""
        self.info(f"Stopping module: {module_name}", 
                 module=module_name, event="module_stop", **kwargs)
    
    def log_api_request(self, method: str, endpoint: str, 
                       status_code: int = None, duration: float = None, **kwargs):
        """Log API request."""
        self.info(f"API {method} {endpoint}", 
                 method=method, endpoint=endpoint, 
                 status_code=status_code, duration=duration,
                 event="api_request", **kwargs)
    
    def log_robot_command(self, command: str, parameters: Dict[str, Any] = None, **kwargs):
        """Log robot command."""
        self.info(f"Robot command: {command}", 
                 command=command, parameters=parameters,
                 event="robot_command", **kwargs)
    
    def log_sensor_data(self, sensor_type: str, data: Dict[str, Any], **kwargs):
        """Log sensor data."""
        self.debug(f"Sensor data: {sensor_type}", 
                  sensor_type=sensor_type, sensor_data=data,
                  event="sensor_data", **kwargs)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        self.info(f"Performance: {operation} took {duration:.3f}s", 
                 operation=operation, duration=duration,
                 event="performance", **kwargs)


# Global logger instance
_global_logger = None


def get_logger(name: str = None) -> MiddlewareLogger:
    """Get logger instance."""
    global _global_logger
    
    if name:
        return MiddlewareLogger(name)
    
    if _global_logger is None:
        _global_logger = MiddlewareLogger()
    
    return _global_logger


def setup_logging(level: str = "INFO", log_dir: str = "logs"):
    """Setup global logging configuration."""
    global _global_logger
    
    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    
    # Create logs directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Initialize global logger
    _global_logger = MiddlewareLogger()
    
    return _global_logger


# Convenience functions
def debug(message: str, **kwargs):
    """Log debug message using global logger."""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log info message using global logger."""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log warning message using global logger."""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log error message using global logger."""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log critical message using global logger."""
    get_logger().critical(message, **kwargs)


def exception(message: str, **kwargs):
    """Log exception using