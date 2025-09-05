"""API Gateway module for t031a5_middleware.

Provides FastAPI-based REST API and WebSocket communication interfaces
for the Unitree G1 robot middleware system.

Components:
- APIGateway: Main gateway manager
- RESTRouter: REST API endpoints
- WebSocketManager: WebSocket connection management
- AuthManager: Authentication and authorization
- RateLimiter: Request rate limiting
- ResponseFormatter: Standardized response formatting

Example:
    from modules.api_gateway import APIGateway, RESTRouter, WebSocketManager
    
    # Initialize API Gateway
    gateway = APIGateway()
    await gateway.initialize()
    
    # Start server
    await gateway.start_server(host="0.0.0.0", port=8000)
"""

from .manager import APIGateway, GatewayConfig, GatewayStats
from .rest_router import RESTRouter, APIResponse, APIError
from .websocket_manager import WebSocketManager, ConnectionInfo, MessageType
from .auth_manager import AuthManager, UserInfo, TokenInfo
from .rate_limiter import RateLimiter, RateLimit
from .response_formatter import ResponseFormatter, ResponseStatus

__all__ = [
    # Main components
    'APIGateway',
    'RESTRouter', 
    'WebSocketManager',
    'AuthManager',
    'RateLimiter',
    'ResponseFormatter',
    
    # Configuration and data structures
    'GatewayConfig',
    'GatewayStats',
    'APIResponse',
    'APIError',
    'ConnectionInfo',
    'MessageType',
    'UserInfo',
    'TokenInfo',
    'RateLimit',
    'ResponseStatus'
]

__version__ = "1.0.0"
__