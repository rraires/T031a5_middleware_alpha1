"""API Gateway Manager for t031a5_middleware.

Main gateway manager that coordinates REST API, WebSocket connections,
authentication, and communication with robot modules.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

# Import other gateway components
from .rest_router import RESTRouter
from .websocket_manager import WebSocketManager
from .auth_manager import AuthManager
from .rate_limiter import RateLimiter
from .response_formatter import ResponseFormatter, ResponseStatus


class GatewayState(Enum):
    """API Gateway states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class GatewayConfig:
    """API Gateway configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Security settings
    enable_auth: bool = True
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    
    # Rate limiting
    enable_rate_limiting: bool = True
    default_rate_limit: int = 100  # requests per minute
    
    # WebSocket settings
    max_connections: int = 100
    heartbeat_interval: int = 30  # seconds
    
    # Static files
    static_directory: Optional[str] = None
    static_url_path: str = "/static"
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    
    # Performance
    enable_gzip: bool = True
    gzip_minimum_size: int = 1000
    
    # Health check
    health_check_interval: int = 60  # seconds


@dataclass
class GatewayStats:
    """API Gateway statistics."""
    start_time: float = field(default_factory=time.time)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    websocket_connections: int = 0
    active_connections: int = 0
    average_response_time: float = 0.0
    last_request_time: float = 0.0
    
    # Error tracking
    error_count_by_type: Dict[str, int] = field(default_factory=dict)
    rate_limit_violations: int = 0
    auth_failures: int = 0
    
    # Performance metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    def get_uptime(self) -> float:
        """Get gateway uptime in seconds."""
        return time.time() - self.start_time
    
    def get_success_rate(self) -> float:
        """Get request success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class APIGateway:
    """Main API Gateway manager.
    
    Coordinates all gateway components including REST API, WebSocket connections,
    authentication, rate limiting, and communication with robot modules.
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Gateway state
        self.state = GatewayState.STOPPED
        self.stats = GatewayStats()
        
        # FastAPI app
        self.app: Optional[FastAPI] = None
        self.server: Optional[uvicorn.Server] = None
        
        # Gateway components
        self.rest_router: Optional[RESTRouter] = None
        self.websocket_manager: Optional[WebSocketManager] = None
        self.auth_manager: Optional[AuthManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.response_formatter: Optional[ResponseFormatter] = None
        
        # Robot modules (injected)
        self.robot_modules: Dict[str, Any] = {}
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Callbacks
        self.request_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        self.connection_callbacks: List[Callable] = []
        
        self.logger.info("API Gateway initialized")
    
    async def initialize(self, robot_modules: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize API Gateway.
        
        Args:
            robot_modules: Dictionary of robot modules to integrate
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.state = GatewayState.STARTING
            
            # Store robot modules
            if robot_modules:
                self.robot_modules = robot_modules
            
            # Initialize components
            await self._initialize_components()
            
            # Create FastAPI app
            await self._create_app()
            
            # Setup routes and middleware
            await self._setup_routes()
            await self._setup_middleware()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info("API Gateway initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing API Gateway: {e}")
            self.state = GatewayState.ERROR
            return False
    
    async def _initialize_components(self) -> None:
        """Initialize gateway components."""
        # Initialize response formatter
        self.response_formatter = ResponseFormatter()
        
        # Initialize authentication manager
        self.auth_manager = AuthManager(
            secret_key=self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            expiration=self.config.jwt_expiration
        )
        await self.auth_manager.initialize()
        
        # Initialize rate limiter
        if self.config.enable_rate_limiting:
            self.rate_limiter = RateLimiter(
                default_limit=self.config.default_rate_limit
            )
            await self.rate_limiter.initialize()
        
        # Initialize WebSocket manager
        self.websocket_manager = WebSocketManager(
            max_connections=self.config.max_connections,
            heartbeat_interval=self.config.heartbeat_interval
        )
        await self.websocket_manager.initialize()
        
        # Initialize REST router
        self.rest_router = RESTRouter(
            auth_manager=self.auth_manager,
            rate_limiter=self.rate_limiter,
            response_formatter=self.response_formatter
        )
        await self.rest_router.initialize(self.robot_modules)
    
    async def _create_app(self) -> None:
        """Create FastAPI application."""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            self.logger.info("API Gateway starting up")
            yield
            # Shutdown
            self.logger.info("API Gateway shutting down")
            await self.shutdown()
        
        self.app = FastAPI(
            title="Unitree G1 Robot API",
            description="API Gateway for Unitree G1 robot middleware",
            version="1.0.0",
            debug=self.config.debug,
            lifespan=lifespan
        )
    
    async def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        if not self.app:
            return
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=self.config.cors_methods,
            allow_headers=self.config.cors_headers,
        )
        
        # Gzip compression
        if self.config.enable_gzip:
            self.app.add_middleware(
                GZipMiddleware,
                minimum_size=self.config.gzip_minimum_size
            )
        
        # Request logging middleware
        if self.config.log_requests:
            @self.app.middleware("http")
            async def log_requests(request: Request, call_next):
                start_time = time.time()
                
                # Process request
                response = await call_next(request)
                
                # Log request
                process_time = time.time() - start_time
                self._update_request_stats(response.status_code, process_time)
                
                if self.config.debug:
                    self.logger.info(
                        f"{request.method} {request.url.path} - "
                        f"{response.status_code} - {process_time:.3f}s"
                    )
                
                return response
    
    async def _setup_routes(self) -> None:
        """Setup API routes."""
        if not self.app or not self.rest_router:
            return
        
        # Include REST router
        self.app.include_router(
            self.rest_router.router,
            prefix="/api/v1",
            tags=["API"]
        )
        
        # WebSocket endpoint
        if self.websocket_manager:
            self.app.add_websocket_route(
                "/ws",
                self.websocket_manager.websocket_endpoint
            )
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return await self._get_health_status()
        
        # Stats endpoint
        @self.app.get("/stats")
        async def get_stats():
            return self._get_stats()
        
        # Static files
        if self.config.static_directory:
            static_path = Path(self.config.static_directory)
            if static_path.exists():
                self.app.mount(
                    self.config.static_url_path,
                    StaticFiles(directory=str(static_path)),
                    name="static"
                )
    
    async def start_server(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        """Start the API Gateway server.
        
        Args:
            host: Server host (overrides config)
            port: Server port (overrides config)
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            if not self.app:
                self.logger.error("FastAPI app not initialized")
                return False
            
            server_host = host or self.config.host
            server_port = port or self.config.port
            
            # Create server configuration
            config = uvicorn.Config(
                app=self.app,
                host=server_host,
                port=server_port,
                log_level=self.config.log_level.lower(),
                access_log=self.config.log_requests
            )
            
            self.server = uvicorn.Server(config)
            
            self.state = GatewayState.RUNNING
            self.logger.info(f"API Gateway server starting on {server_host}:{server_port}")
            
            # Start server
            await self.server.serve()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            self.state = GatewayState.ERROR
            return False
    
    async def shutdown(self) -> None:
        """Shutdown API Gateway."""
        try:
            self.state = GatewayState.STOPPING
            self.logger.info("Shutting down API Gateway")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Shutdown components
            if self.websocket_manager:
                await self.websocket_manager.shutdown()
            
            if self.rest_router:
                await self.rest_router.shutdown()
            
            if self.auth_manager:
                await self.auth_manager.shutdown()
            
            if self.rate_limiter:
                await self.rate_limiter.shutdown()
            
            # Stop server
            if self.server:
                self.server.should_exit = True
            
            self.state = GatewayState.STOPPED
            self.logger.info("API Gateway shutdown complete")
        
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.state = GatewayState.ERROR
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Health monitoring task
        task = asyncio.create_task(self._health_monitor_loop())
        self._background_tasks.append(task)
        
        # Stats collection task
        task = asyncio.create_task(self._stats_collection_loop())
        self._background_tasks.append(task)
        
        # Cleanup task
        task = asyncio.create_task(self._cleanup_loop())
        self._background_tasks.append(task)
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._background_tasks.clear()
    
    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_component_health()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(10)
    
    async def _stats_collection_loop(self) -> None:
        """Background statistics collection loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._collect_system_stats()
                await asyncio.sleep(30)  # Collect stats every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error collecting stats: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_cleanup()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _check_component_health(self) -> None:
        """Check health of all components."""
        try:
            # Check WebSocket manager
            if self.websocket_manager:
                ws_health = await self.websocket_manager.get_health_status()
                if not ws_health.get('healthy', False):
                    self.logger.warning("WebSocket manager unhealthy")
            
            # Check auth manager
            if self.auth_manager:
                auth_health = await self.auth_manager.get_health_status()
                if not auth_health.get('healthy', False):
                    self.logger.warning("Auth manager unhealthy")
            
            # Check rate limiter
            if self.rate_limiter:
                rate_health = await self.rate_limiter.get_health_status()
                if not rate_health.get('healthy', False):
                    self.logger.warning("Rate limiter unhealthy")
            
            # Check robot modules
            for name, module in self.robot_modules.items():
                if hasattr(module, 'get_health_status'):
                    try:
                        module_health = await module.get_health_status()
                        if not module_health.get('healthy', False):
                            self.logger.warning(f"Robot module {name} unhealthy")
                    except Exception as e:
                        self.logger.error(f"Error checking {name} health: {e}")
        
        except Exception as e:
            self.logger.error(f"Error checking component health: {e}")
    
    async def _collect_system_stats(self) -> None:
        """Collect system statistics."""
        try:
            import psutil
            
            # Update system stats
            self.stats.cpu_usage = psutil.cpu_percent()
            self.stats.memory_usage = psutil.virtual_memory().percent
            
            # Update WebSocket stats
            if self.websocket_manager:
                ws_stats = await self.websocket_manager.get_stats()
                self.stats.websocket_connections = ws_stats.get('total_connections', 0)
                self.stats.active_connections = ws_stats.get('active_connections', 0)
        
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error(f"Error collecting system stats: {e}")
    
    async def _perform_cleanup(self) -> None:
        """Perform periodic cleanup tasks."""
        try:
            # Cleanup expired tokens
            if self.auth_manager:
                await self.auth_manager.cleanup_expired_tokens()
            
            # Cleanup rate limiter
            if self.rate_limiter:
                await self.rate_limiter.cleanup()
            
            # Cleanup WebSocket connections
            if self.websocket_manager:
                await self.websocket_manager.cleanup_stale_connections()
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _update_request_stats(self, status_code: int, response_time: float) -> None:
        """Update request statistics."""
        self.stats.total_requests += 1
        self.stats.last_request_time = time.time()
        
        if 200 <= status_code < 400:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
        
        # Update average response time
        if self.stats.total_requests == 1:
            self.stats.average_response_time = response_time
        else:
            self.stats.average_response_time = (
                (self.stats.average_response_time * (self.stats.total_requests - 1) + response_time) /
                self.stats.total_requests
            )
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        health_status = {
            'status': 'healthy' if self.state == GatewayState.RUNNING else 'unhealthy',
            'state': self.state.value,
            'uptime': self.stats.get_uptime(),
            'components': {}
        }
        
        # Check component health
        if self.websocket_manager:
            health_status['components']['websocket'] = await self.websocket_manager.get_health_status()
        
        if self.auth_manager:
            health_status['components']['auth'] = await self.auth_manager.get_health_status()
        
        if self.rate_limiter:
            health_status['components']['rate_limiter'] = await self.rate_limiter.get_health_status()
        
        return health_status
    
    def _get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            'uptime': self.stats.get_uptime(),
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'success_rate': self.stats.get_success_rate(),
            'average_response_time': self.stats.average_response_time,
            'websocket_connections': self.stats.websocket_connections,
            'active_connections': self.stats.active_connections,
            'cpu_usage': self.stats.cpu_usage,
            'memory_usage': self.stats.memory_usage,
            'error_count_by_type': self.stats.error_count_by_type,
            'rate_limit_violations': self.stats.rate_limit_violations,
            'auth_failures': self.stats.auth_failures
        }
    
    # Public API methods
    def add_request_callback(self, callback: Callable) -> None:
        """Add request callback."""
        self.request_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable) -> None:
        """Add error callback."""
        self.error_callbacks.append(callback)
    
    def add_connection_callback(self, callback: Callable) -> None:
        """Add connection callback."""
        self.connection_callbacks.append(callback)
    
    def get_state(self) -> GatewayState:
        """Get current gateway state."""
        return self.state
    
    def get_stats(self) -> GatewayStats:
        """Get gateway statistics."""
        return self.stats
    
    def get_config(self) -> GatewayConfig:
        """Get gateway configuration."""
        return self.config
    
    async def broadcast_message(self, message: Dict[str, Any], 
                              connection_filter: Optional[Callable] = None) -> int:
        """Broadcast message to WebSocket connections.
        
        Args:
            message: Message to broadcast
            connection_filter: Optional filter function for connections
        
        Returns:
            Number of connections message was sent to
        """
        if self.websocket_manager:
            return await self.websocket_manager.broadcast_message(message, connection_filter)
        return 0
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific WebSocket connection.
        
        Args:
            connection_id: Target connection ID
            message: Message to send
        
        Returns:
            True if message sent successfully, False otherwise
        """
        if self.websocket_manager:
            return await self.websocket_manager.send_to_connection(connection_id, message)
        return False