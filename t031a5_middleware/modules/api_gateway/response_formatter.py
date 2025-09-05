"""Response Formatter for API Gateway.

Standardizes API responses with consistent format and error handling.
"""

import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class ResponseStatus(Enum):
    """Response status types."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorCode(Enum):
    """Standard error codes."""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Robot errors
    ROBOT_OFFLINE = "ROBOT_OFFLINE"
    ROBOT_BUSY = "ROBOT_BUSY"
    ROBOT_ERROR = "ROBOT_ERROR"
    MOTION_ERROR = "MOTION_ERROR"
    SENSOR_ERROR = "SENSOR_ERROR"
    
    # System errors
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class ResponseMetadata:
    """Response metadata."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    processing_time: Optional[float] = None
    version: str = "1.0"
    server: str = "unitree-middleware"
    
    # Pagination
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None
    
    # Additional metadata
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorDetail:
    """Error detail information."""
    code: ErrorCode
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None


@dataclass
class FormatterConfig:
    """Response formatter configuration."""
    # Format settings
    include_metadata: bool = True
    include_request_id: bool = True
    include_processing_time: bool = True
    include_timestamp: bool = True
    
    # Error settings
    include_stack_trace: bool = False  # Only in debug mode
    include_error_details: bool = True
    mask_sensitive_data: bool = True
    
    # Pagination settings
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Response settings
    pretty_print: bool = False
    ensure_ascii: bool = False
    
    # Custom fields
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseFormatter:
    """Response formatter for standardizing API responses.
    
    Provides consistent response format across all API endpoints.
    """
    
    def __init__(self, config: Optional[FormatterConfig] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or FormatterConfig()
        
        # Error code to HTTP status mapping
        self.error_status_map = {
            ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
            ErrorCode.AUTHENTICATION_ERROR: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
            ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
            ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.ROBOT_OFFLINE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.ROBOT_BUSY: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.TIMEOUT: status.HTTP_408_REQUEST_TIMEOUT,
            ErrorCode.SYSTEM_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.UNKNOWN_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        
        self.logger.info("Response Formatter initialized")
    
    def _create_metadata(self, request: Optional[Request] = None, 
                        processing_time: Optional[float] = None,
                        **kwargs) -> ResponseMetadata:
        """Create response metadata.
        
        Args:
            request: HTTP request
            processing_time: Request processing time
            **kwargs: Additional metadata
        
        Returns:
            Response metadata
        """
        metadata = ResponseMetadata(
            processing_time=processing_time,
            **self.config.custom_metadata
        )
        
        # Add request ID if available
        if request and self.config.include_request_id:
            request_id = getattr(request.state, 'request_id', None)
            if request_id:
                metadata.request_id = request_id
        
        # Add pagination info if provided
        for key in ['page', 'page_size', 'total_count', 'total_pages']:
            if key in kwargs:
                setattr(metadata, key, kwargs[key])
        
        # Add extra metadata
        extra_keys = set(kwargs.keys()) - {'page', 'page_size', 'total_count', 'total_pages'}
        for key in extra_keys:
            metadata.extra[key] = kwargs[key]
        
        return metadata
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive data in response.
        
        Args:
            data: Data to mask
        
        Returns:
            Masked data
        """
        if not self.config.mask_sensitive_data:
            return data
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                # Mask sensitive fields
                if any(sensitive in key.lower() for sensitive in 
                      ['password', 'token', 'secret', 'key', 'auth']):
                    masked_data[key] = "***masked***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        
        else:
            return data
    
    def success(self, data: Any = None, message: str = "Success", 
               request: Optional[Request] = None, 
               processing_time: Optional[float] = None,
               status_code: int = status.HTTP_200_OK,
               headers: Optional[Dict[str, str]] = None,
               **metadata_kwargs) -> JSONResponse:
        """Create success response.
        
        Args:
            data: Response data
            message: Success message
            request: HTTP request
            processing_time: Request processing time
            status_code: HTTP status code
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        response_data = {
            "status": ResponseStatus.SUCCESS.value,
            "message": message
        }
        
        # Add data if provided
        if data is not None:
            response_data["data"] = self._mask_sensitive_data(data)
        
        # Add metadata if enabled
        if self.config.include_metadata:
            metadata = self._create_metadata(request, processing_time, **metadata_kwargs)
            response_data["metadata"] = {
                "timestamp": metadata.timestamp.isoformat() if self.config.include_timestamp else None,
                "request_id": metadata.request_id if self.config.include_request_id else None,
                "processing_time": metadata.processing_time if self.config.include_processing_time else None,
                "version": metadata.version,
                "server": metadata.server
            }
            
            # Add pagination info
            if any(getattr(metadata, field, None) is not None for field in 
                  ['page', 'page_size', 'total_count', 'total_pages']):
                response_data["metadata"]["pagination"] = {
                    "page": metadata.page,
                    "page_size": metadata.page_size,
                    "total_count": metadata.total_count,
                    "total_pages": metadata.total_pages
                }
            
            # Add extra metadata
            if metadata.extra:
                response_data["metadata"]["extra"] = metadata.extra
            
            # Remove None values from metadata
            response_data["metadata"] = {
                k: v for k, v in response_data["metadata"].items() 
                if v is not None
            }
        
        # Prepare headers
        response_headers = self.config.custom_headers.copy()
        if headers:
            response_headers.update(headers)
        
        return JSONResponse(
            content=jsonable_encoder(response_data),
            status_code=status_code,
            headers=response_headers
        )
    
    def error(self, error: Union[ErrorCode, str, Exception], 
             message: Optional[str] = None,
             details: Optional[Dict[str, Any]] = None,
             field: Optional[str] = None,
             request: Optional[Request] = None,
             processing_time: Optional[float] = None,
             status_code: Optional[int] = None,
             headers: Optional[Dict[str, str]] = None,
             **metadata_kwargs) -> JSONResponse:
        """Create error response.
        
        Args:
            error: Error code, message, or exception
            message: Error message
            details: Error details
            field: Field that caused the error
            request: HTTP request
            processing_time: Request processing time
            status_code: HTTP status code
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        # Parse error
        if isinstance(error, Exception):
            error_code = ErrorCode.UNKNOWN_ERROR
            error_message = message or str(error)
            
            # Add stack trace in debug mode
            if self.config.include_stack_trace:
                if details is None:
                    details = {}
                details["stack_trace"] = traceback.format_exc()
        
        elif isinstance(error, ErrorCode):
            error_code = error
            error_message = message or error.value.replace("_", " ").title()
        
        else:  # string
            error_code = ErrorCode.UNKNOWN_ERROR
            error_message = str(error)
        
        # Create error detail
        error_detail = ErrorDetail(
            code=error_code,
            message=error_message,
            field=field,
            details=details
        )
        
        # Determine status code
        if status_code is None:
            status_code = self.error_status_map.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = {
            "status": ResponseStatus.ERROR.value,
            "message": error_message,
            "error": {
                "code": error_code.value,
                "message": error_message
            }
        }
        
        # Add error details if enabled
        if self.config.include_error_details:
            if field:
                response_data["error"]["field"] = field
            if details:
                response_data["error"]["details"] = self._mask_sensitive_data(details)
        
        # Add metadata if enabled
        if self.config.include_metadata:
            metadata = self._create_metadata(request, processing_time, **metadata_kwargs)
            response_data["metadata"] = {
                "timestamp": metadata.timestamp.isoformat() if self.config.include_timestamp else None,
                "request_id": metadata.request_id if self.config.include_request_id else None,
                "processing_time": metadata.processing_time if self.config.include_processing_time else None,
                "version": metadata.version,
                "server": metadata.server
            }
            
            # Add extra metadata
            if metadata.extra:
                response_data["metadata"]["extra"] = metadata.extra
            
            # Remove None values from metadata
            response_data["metadata"] = {
                k: v for k, v in response_data["metadata"].items() 
                if v is not None
            }
        
        # Prepare headers
        response_headers = self.config.custom_headers.copy()
        if headers:
            response_headers.update(headers)
        
        # Log error
        self.logger.error(f"API Error: {error_code.value} - {error_message}")
        
        return JSONResponse(
            content=jsonable_encoder(response_data),
            status_code=status_code,
            headers=response_headers
        )
    
    def warning(self, message: str, data: Any = None,
               request: Optional[Request] = None,
               processing_time: Optional[float] = None,
               status_code: int = status.HTTP_200_OK,
               headers: Optional[Dict[str, str]] = None,
               **metadata_kwargs) -> JSONResponse:
        """Create warning response.
        
        Args:
            message: Warning message
            data: Response data
            request: HTTP request
            processing_time: Request processing time
            status_code: HTTP status code
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        response_data = {
            "status": ResponseStatus.WARNING.value,
            "message": message
        }
        
        # Add data if provided
        if data is not None:
            response_data["data"] = self._mask_sensitive_data(data)
        
        # Add metadata if enabled
        if self.config.include_metadata:
            metadata = self._create_metadata(request, processing_time, **metadata_kwargs)
            response_data["metadata"] = {
                "timestamp": metadata.timestamp.isoformat() if self.config.include_timestamp else None,
                "request_id": metadata.request_id if self.config.include_request_id else None,
                "processing_time": metadata.processing_time if self.config.include_processing_time else None,
                "version": metadata.version,
                "server": metadata.server
            }
            
            # Add extra metadata
            if metadata.extra:
                response_data["metadata"]["extra"] = metadata.extra
            
            # Remove None values from metadata
            response_data["metadata"] = {
                k: v for k, v in response_data["metadata"].items() 
                if v is not None
            }
        
        # Prepare headers
        response_headers = self.config.custom_headers.copy()
        if headers:
            response_headers.update(headers)
        
        # Log warning
        self.logger.warning(f"API Warning: {message}")
        
        return JSONResponse(
            content=jsonable_encoder(response_data),
            status_code=status_code,
            headers=response_headers
        )
    
    def info(self, message: str, data: Any = None,
            request: Optional[Request] = None,
            processing_time: Optional[float] = None,
            status_code: int = status.HTTP_200_OK,
            headers: Optional[Dict[str, str]] = None,
            **metadata_kwargs) -> JSONResponse:
        """Create info response.
        
        Args:
            message: Info message
            data: Response data
            request: HTTP request
            processing_time: Request processing time
            status_code: HTTP status code
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        response_data = {
            "status": ResponseStatus.INFO.value,
            "message": message
        }
        
        # Add data if provided
        if data is not None:
            response_data["data"] = self._mask_sensitive_data(data)
        
        # Add metadata if enabled
        if self.config.include_metadata:
            metadata = self._create_metadata(request, processing_time, **metadata_kwargs)
            response_data["metadata"] = {
                "timestamp": metadata.timestamp.isoformat() if self.config.include_timestamp else None,
                "request_id": metadata.request_id if self.config.include_request_id else None,
                "processing_time": metadata.processing_time if self.config.include_processing_time else None,
                "version": metadata.version,
                "server": metadata.server
            }
            
            # Add extra metadata
            if metadata.extra:
                response_data["metadata"]["extra"] = metadata.extra
            
            # Remove None values from metadata
            response_data["metadata"] = {
                k: v for k, v in response_data["metadata"].items() 
                if v is not None
            }
        
        # Prepare headers
        response_headers = self.config.custom_headers.copy()
        if headers:
            response_headers.update(headers)
        
        return JSONResponse(
            content=jsonable_encoder(response_data),
            status_code=status_code,
            headers=response_headers
        )
    
    def paginated(self, data: List[Any], page: int, page_size: int, 
                 total_count: int, message: str = "Success",
                 request: Optional[Request] = None,
                 processing_time: Optional[float] = None,
                 status_code: int = status.HTTP_200_OK,
                 headers: Optional[Dict[str, str]] = None,
                 **metadata_kwargs) -> JSONResponse:
        """Create paginated response.
        
        Args:
            data: Response data (current page)
            page: Current page number
            page_size: Page size
            total_count: Total number of items
            message: Success message
            request: HTTP request
            processing_time: Request processing time
            status_code: HTTP status code
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return self.success(
            data=data,
            message=message,
            request=request,
            processing_time=processing_time,
            status_code=status_code,
            headers=headers,
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            **metadata_kwargs
        )
    
    def validation_error(self, errors: List[Dict[str, Any]], 
                        message: str = "Validation failed",
                        request: Optional[Request] = None,
                        processing_time: Optional[float] = None,
                        headers: Optional[Dict[str, str]] = None,
                        **metadata_kwargs) -> JSONResponse:
        """Create validation error response.
        
        Args:
            errors: List of validation errors
            message: Error message
            request: HTTP request
            processing_time: Request processing time
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        return self.error(
            error=ErrorCode.VALIDATION_ERROR,
            message=message,
            details={"validation_errors": errors},
            request=request,
            processing_time=processing_time,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
            **metadata_kwargs
        )
    
    def not_found(self, resource: str = "Resource",
                 request: Optional[Request] = None,
                 processing_time: Optional[float] = None,
                 headers: Optional[Dict[str, str]] = None,
                 **metadata_kwargs) -> JSONResponse:
        """Create not found error response.
        
        Args:
            resource: Resource name
            request: HTTP request
            processing_time: Request processing time
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        return self.error(
            error=ErrorCode.NOT_FOUND,
            message=f"{resource} not found",
            request=request,
            processing_time=processing_time,
            status_code=status.HTTP_404_NOT_FOUND,
            headers=headers,
            **metadata_kwargs
        )
    
    def unauthorized(self, message: str = "Authentication required",
                    request: Optional[Request] = None,
                    processing_time: Optional[float] = None,
                    headers: Optional[Dict[str, str]] = None,
                    **metadata_kwargs) -> JSONResponse:
        """Create unauthorized error response.
        
        Args:
            message: Error message
            request: HTTP request
            processing_time: Request processing time
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        return self.error(
            error=ErrorCode.AUTHENTICATION_ERROR,
            message=message,
            request=request,
            processing_time=processing_time,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers,
            **metadata_kwargs
        )
    
    def forbidden(self, message: str = "Access denied",
                 request: Optional[Request] = None,
                 processing_time: Optional[float] = None,
                 headers: Optional[Dict[str, str]] = None,
                 **metadata_kwargs) -> JSONResponse:
        """Create forbidden error response.
        
        Args:
            message: Error message
            request: HTTP request
            processing_time: Request processing time
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        return self.error(
            error=ErrorCode.AUTHORIZATION_ERROR,
            message=message,
            request=request,
            processing_time=processing_time,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers,
            **metadata_kwargs
        )
    
    def rate_limited(self, message: str = "Rate limit exceeded",
                    retry_after: Optional[int] = None,
                    request: Optional[Request] = None,
                    processing_time: Optional[float] = None,
                    **metadata_kwargs) -> JSONResponse:
        """Create rate limited error response.
        
        Args:
            message: Error message
            retry_after: Retry after seconds
            request: HTTP request
            processing_time: Request processing time
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        return self.error(
            error=ErrorCode.RATE_LIMITED,
            message=message,
            details={"retry_after": retry_after} if retry_after else None,
            request=request,
            processing_time=processing_time,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
            **metadata_kwargs
        )
    
    def robot_error(self, error_type: str, message: str,
                   request: Optional[Request] = None,
                   processing_time: Optional[float] = None,
                   headers: Optional[Dict[str, str]] = None,
                   **metadata_kwargs) -> JSONResponse:
        """Create robot error response.
        
        Args:
            error_type: Type of robot error
            message: Error message
            request: HTTP request
            processing_time: Request processing time
            headers: Additional headers
            **metadata_kwargs: Additional metadata
        
        Returns:
            JSON response
        """
        # Map error type to error code
        error_map = {
            "offline": ErrorCode.ROBOT_OFFLINE,
            "busy": ErrorCode.ROBOT_BUSY,
            "motion": ErrorCode.MOTION_ERROR,
            "sensor": ErrorCode.SENSOR_ERROR,
        }
        
        error_code = error_map.get(error_type, ErrorCode.ROBOT_ERROR)
        
        return self.error(
            error=error_code,
            message=message,
            details={"error_type": error_type},
            request=request,
            processing_time=processing_time,
            headers=headers,
            **metadata_kwargs
        )
    
    def middleware(self, request: Request, call_next):
        """Response formatting middleware.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response
        """
        start_time = time.time()
        
        # Add request ID to state
        if not hasattr(request.state, 'request_id'):
            import uuid
            request.state.request_id = str(uuid.uuid4())
        
        try:
            response = call_next(request)
            processing_time = time.time() - start_time
            
            # Add processing time header
            if hasattr(response, 'headers'):
                response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
                response.headers["X-Request-ID"] = request.state.request_id
            
            return response
        
        except Exception as e:
            processing_time = time.time() - start_time
            return self.error(
                error=e,
                request=request,
                processing_time=processing_time
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get formatter configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "include_metadata": self.config.include_metadata,
            "include_request_id": self.config.include_request_id,
            "include_processing_time": self.config.include_processing_time,
            "include_timestamp": self.config.include_timestamp,
            "include_stack_trace": self.config.