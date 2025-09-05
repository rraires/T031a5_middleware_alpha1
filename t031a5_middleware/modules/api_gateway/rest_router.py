"""REST Router for API Gateway.

Manages REST API routes and endpoints for robot module communication.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Import gateway components
from .auth_manager import AuthManager
from .rate_limiter import RateLimiter
from .response_formatter import ResponseFormatter, ResponseStatus


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# Pydantic models for API requests/responses
class BaseRequest(BaseModel):
    """Base request model."""
    timestamp: Optional[float] = Field(default_factory=time.time)
    request_id: Optional[str] = None


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool
    message: str
    timestamp: float = Field(default_factory=time.time)
    request_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Robot control models
class MotionCommand(BaseRequest):
    """Motion command request."""
    action: str = Field(..., description="Motion action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[float] = None
    priority: int = Field(default=5, ge=1, le=10)


class AudioCommand(BaseRequest):
    """Audio command request."""
    action: str = Field(..., description="Audio action to perform")
    text: Optional[str] = None
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    language: Optional[str] = "en"
    voice: Optional[str] = None


class LEDCommand(BaseRequest):
    """LED command request."""
    pattern: str = Field(..., description="LED pattern to display")
    color: Optional[str] = None
    brightness: Optional[float] = Field(None, ge=0.0, le=1.0)
    duration: Optional[float] = None
    repeat: Optional[int] = None


class VideoCommand(BaseRequest):
    """Video command request."""
    action: str = Field(..., description="Video action to perform")
    source: Optional[str] = None
    quality: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SensorQuery(BaseRequest):
    """Sensor data query request."""
    sensor_types: Optional[List[str]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    limit: Optional[int] = Field(None, ge=1, le=1000)


class ConfigUpdate(BaseRequest):
    """Configuration update request."""
    module: str = Field(..., description="Module to configure")
    config: Dict[str, Any] = Field(..., description="Configuration parameters")
    restart_required: bool = Field(default=False)


@dataclass
class RouteConfig:
    """Route configuration."""
    path: str
    method: HTTPMethod
    handler: Callable
    auth_required: bool = True
    rate_limit: Optional[int] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)


class RESTRouter:
    """REST API router manager.
    
    Manages REST API routes and endpoints for robot module communication.
    """
    
    def __init__(self, 
                 auth_manager: Optional[AuthManager] = None,
                 rate_limiter: Optional[RateLimiter] = None,
                 response_formatter: Optional[ResponseFormatter] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Dependencies
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        self.response_formatter = response_formatter or ResponseFormatter()
        
        # FastAPI router
        self.router = APIRouter()
        
        # Robot modules (injected)
        self.robot_modules: Dict[str, Any] = {}
        
        # Route registry
        self.routes: List[RouteConfig] = []
        
        # Security
        self.security = HTTPBearer(auto_error=False)
        
        self.logger.info("REST Router initialized")
    
    async def initialize(self, robot_modules: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize REST router.
        
        Args:
            robot_modules: Dictionary of robot modules to integrate
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Store robot modules
            if robot_modules:
                self.robot_modules = robot_modules
            
            # Setup routes
            await self._setup_routes()
            
            self.logger.info("REST Router initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing REST Router: {e}")
            return False
    
    async def _setup_routes(self) -> None:
        """Setup API routes."""
        # System routes
        self._setup_system_routes()
        
        # Robot module routes
        self._setup_motion_routes()
        self._setup_audio_routes()
        self._setup_led_routes()
        self._setup_video_routes()
        self._setup_sensor_routes()
        
        # Configuration routes
        self._setup_config_routes()
    
    def _setup_system_routes(self) -> None:
        """Setup system management routes."""
        
        @self.router.get("/system/status", 
                        response_model=BaseResponse,
                        tags=["System"],
                        summary="Get system status")
        async def get_system_status(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Get overall system status."""
            try:
                # Authenticate if required
                if self.auth_manager and credentials:
                    user = await self.auth_manager.verify_token(credentials.credentials)
                    if not user:
                        raise HTTPException(status_code=401, detail="Invalid token")
                
                # Check rate limit
                if self.rate_limiter:
                    client_ip = request.client.host
                    if not await self.rate_limiter.check_rate_limit(client_ip):
                        raise HTTPException(status_code=429, detail="Rate limit exceeded")
                
                # Collect system status
                status_data = {
                    'timestamp': time.time(),
                    'modules': {}
                }
                
                # Get module statuses
                for name, module in self.robot_modules.items():
                    try:
                        if hasattr(module, 'get_state'):
                            module_state = module.get_state()
                            status_data['modules'][name] = {
                                'state': module_state.value if hasattr(module_state, 'value') else str(module_state),
                                'healthy': True
                            }
                        else:
                            status_data['modules'][name] = {
                                'state': 'unknown',
                                'healthy': False
                            }
                    except Exception as e:
                        status_data['modules'][name] = {
                            'state': 'error',
                            'healthy': False,
                            'error': str(e)
                        }
                
                return self.response_formatter.success(
                    message="System status retrieved",
                    data=status_data
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                return self.response_formatter.error(
                    message="Failed to get system status",
                    error=str(e)
                )
        
        @self.router.post("/system/shutdown",
                         response_model=BaseResponse,
                         tags=["System"],
                         summary="Shutdown system")
        async def shutdown_system(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Shutdown the robot system."""
            try:
                # Authenticate (required for shutdown)
                if not self.auth_manager or not credentials:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                user = await self.auth_manager.verify_token(credentials.credentials)
                if not user or not user.get('admin', False):
                    raise HTTPException(status_code=403, detail="Admin access required")
                
                # Shutdown modules
                shutdown_results = {}
                for name, module in self.robot_modules.items():
                    try:
                        if hasattr(module, 'shutdown'):
                            await module.shutdown()
                            shutdown_results[name] = 'success'
                        else:
                            shutdown_results[name] = 'no_shutdown_method'
                    except Exception as e:
                        shutdown_results[name] = f'error: {e}'
                
                return self.response_formatter.success(
                    message="System shutdown initiated",
                    data={'shutdown_results': shutdown_results}
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error shutting down system: {e}")
                return self.response_formatter.error(
                    message="Failed to shutdown system",
                    error=str(e)
                )
    
    def _setup_motion_routes(self) -> None:
        """Setup motion control routes."""
        
        @self.router.post("/motion/command",
                         response_model=BaseResponse,
                         tags=["Motion"],
                         summary="Send motion command")
        async def send_motion_command(
            command: MotionCommand,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Send motion command to robot."""
            try:
                # Authenticate
                if self.auth_manager and credentials:
                    user = await self.auth_manager.verify_token(credentials.credentials)
                    if not user:
                        raise HTTPException(status_code=401, detail="Invalid token")
                
                # Check rate limit
                if self.rate_limiter:
                    client_ip = request.client.host
                    if not await self.rate_limiter.check_rate_limit(client_ip, limit=20):  # Higher limit for motion
                        raise HTTPException(status_code=429, detail="Rate limit exceeded")
                
                # Get motion manager
                motion_manager = self.robot_modules.get('motion')
                if not motion_manager:
                    raise HTTPException(status_code=503, detail="Motion manager not available")
                
                # Execute command
                if hasattr(motion_manager, 'execute_command'):
                    result = await motion_manager.execute_command(
                        action=command.action,
                        parameters=command.parameters,
                        duration=command.duration,
                        priority=command.priority
                    )
                    
                    return self.response_formatter.success(
                        message=f"Motion command '{command.action}' executed",
                        data={'result': result, 'command_id': command.request_id}
                    )
                else:
                    raise HTTPException(status_code=501, detail="Motion command execution not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error executing motion command: {e}")
                return self.response_formatter.error(
                    message="Failed to execute motion command",
                    error=str(e)
                )
        
        @self.router.get("/motion/status",
                        response_model=BaseResponse,
                        tags=["Motion"],
                        summary="Get motion status")
        async def get_motion_status(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Get current motion status."""
            try:
                # Get motion manager
                motion_manager = self.robot_modules.get('motion')
                if not motion_manager:
                    raise HTTPException(status_code=503, detail="Motion manager not available")
                
                # Get status
                if hasattr(motion_manager, 'get_status'):
                    status_data = await motion_manager.get_status()
                    return self.response_formatter.success(
                        message="Motion status retrieved",
                        data=status_data
                    )
                else:
                    raise HTTPException(status_code=501, detail="Motion status not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting motion status: {e}")
                return self.response_formatter.error(
                    message="Failed to get motion status",
                    error=str(e)
                )
    
    def _setup_audio_routes(self) -> None:
        """Setup audio control routes."""
        
        @self.router.post("/audio/command",
                         response_model=BaseResponse,
                         tags=["Audio"],
                         summary="Send audio command")
        async def send_audio_command(
            command: AudioCommand,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Send audio command to robot."""
            try:
                # Get audio manager
                audio_manager = self.robot_modules.get('audio')
                if not audio_manager:
                    raise HTTPException(status_code=503, detail="Audio manager not available")
                
                # Execute command based on action
                result = None
                if command.action == "speak" and command.text:
                    if hasattr(audio_manager, 'speak'):
                        result = await audio_manager.speak(
                            text=command.text,
                            volume=command.volume,
                            language=command.language,
                            voice=command.voice
                        )
                elif command.action == "set_volume" and command.volume is not None:
                    if hasattr(audio_manager, 'set_volume'):
                        result = await audio_manager.set_volume(command.volume)
                elif command.action == "stop":
                    if hasattr(audio_manager, 'stop'):
                        result = await audio_manager.stop()
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown audio action: {command.action}")
                
                return self.response_formatter.success(
                    message=f"Audio command '{command.action}' executed",
                    data={'result': result, 'command_id': command.request_id}
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error executing audio command: {e}")
                return self.response_formatter.error(
                    message="Failed to execute audio command",
                    error=str(e)
                )
    
    def _setup_led_routes(self) -> None:
        """Setup LED control routes."""
        
        @self.router.post("/led/command",
                         response_model=BaseResponse,
                         tags=["LED"],
                         summary="Send LED command")
        async def send_led_command(
            command: LEDCommand,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Send LED command to robot."""
            try:
                # Get LED manager
                led_manager = self.robot_modules.get('leds')
                if not led_manager:
                    raise HTTPException(status_code=503, detail="LED manager not available")
                
                # Execute command
                if hasattr(led_manager, 'set_pattern'):
                    result = await led_manager.set_pattern(
                        pattern=command.pattern,
                        color=command.color,
                        brightness=command.brightness,
                        duration=command.duration,
                        repeat=command.repeat
                    )
                    
                    return self.response_formatter.success(
                        message=f"LED pattern '{command.pattern}' set",
                        data={'result': result, 'command_id': command.request_id}
                    )
                else:
                    raise HTTPException(status_code=501, detail="LED pattern control not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error executing LED command: {e}")
                return self.response_formatter.error(
                    message="Failed to execute LED command",
                    error=str(e)
                )
    
    def _setup_video_routes(self) -> None:
        """Setup video control routes."""
        
        @self.router.post("/video/command",
                         response_model=BaseResponse,
                         tags=["Video"],
                         summary="Send video command")
        async def send_video_command(
            command: VideoCommand,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Send video command to robot."""
            try:
                # Get video manager
                video_manager = self.robot_modules.get('video')
                if not video_manager:
                    raise HTTPException(status_code=503, detail="Video manager not available")
                
                # Execute command based on action
                result = None
                if command.action == "start_capture":
                    if hasattr(video_manager, 'start_capture'):
                        result = await video_manager.start_capture(
                            source=command.source,
                            **command.parameters
                        )
                elif command.action == "stop_capture":
                    if hasattr(video_manager, 'stop_capture'):
                        result = await video_manager.stop_capture()
                elif command.action == "start_streaming":
                    if hasattr(video_manager, 'start_streaming'):
                        result = await video_manager.start_streaming(
                            quality=command.quality,
                            **command.parameters
                        )
                elif command.action == "stop_streaming":
                    if hasattr(video_manager, 'stop_streaming'):
                        result = await video_manager.stop_streaming()
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown video action: {command.action}")
                
                return self.response_formatter.success(
                    message=f"Video command '{command.action}' executed",
                    data={'result': result, 'command_id': command.request_id}
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error executing video command: {e}")
                return self.response_formatter.error(
                    message="Failed to execute video command",
                    error=str(e)
                )
    
    def _setup_sensor_routes(self) -> None:
        """Setup sensor data routes."""
        
        @self.router.post("/sensors/query",
                         response_model=BaseResponse,
                         tags=["Sensors"],
                         summary="Query sensor data")
        async def query_sensor_data(
            query: SensorQuery,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Query sensor data from robot."""
            try:
                # Get sensor fusion manager
                sensor_fusion = self.robot_modules.get('sensor_fusion')
                if not sensor_fusion:
                    raise HTTPException(status_code=503, detail="Sensor fusion not available")
                
                # Query sensor data
                if hasattr(sensor_fusion, 'get_sensor_data'):
                    sensor_data = await sensor_fusion.get_sensor_data(
                        sensor_types=query.sensor_types,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit
                    )
                    
                    return self.response_formatter.success(
                        message="Sensor data retrieved",
                        data={'sensors': sensor_data, 'query_id': query.request_id}
                    )
                else:
                    raise HTTPException(status_code=501, detail="Sensor data query not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error querying sensor data: {e}")
                return self.response_formatter.error(
                    message="Failed to query sensor data",
                    error=str(e)
                )
        
        @self.router.get("/sensors/current",
                        response_model=BaseResponse,
                        tags=["Sensors"],
                        summary="Get current sensor readings")
        async def get_current_sensors(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Get current sensor readings."""
            try:
                # Get sensor fusion manager
                sensor_fusion = self.robot_modules.get('sensor_fusion')
                if not sensor_fusion:
                    raise HTTPException(status_code=503, detail="Sensor fusion not available")
                
                # Get current state
                if hasattr(sensor_fusion, 'get_current_state'):
                    current_state = await sensor_fusion.get_current_state()
                    return self.response_formatter.success(
                        message="Current sensor readings retrieved",
                        data=current_state
                    )
                else:
                    raise HTTPException(status_code=501, detail="Current sensor readings not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting current sensors: {e}")
                return self.response_formatter.error(
                    message="Failed to get current sensor readings",
                    error=str(e)
                )
    
    def _setup_config_routes(self) -> None:
        """Setup configuration routes."""
        
        @self.router.post("/config/update",
                         response_model=BaseResponse,
                         tags=["Configuration"],
                         summary="Update module configuration")
        async def update_config(
            config_update: ConfigUpdate,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Update module configuration."""
            try:
                # Authenticate (required for config changes)
                if not self.auth_manager or not credentials:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                user = await self.auth_manager.verify_token(credentials.credentials)
                if not user:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                # Get target module
                module = self.robot_modules.get(config_update.module)
                if not module:
                    raise HTTPException(status_code=404, detail=f"Module '{config_update.module}' not found")
                
                # Update configuration
                if hasattr(module, 'update_config'):
                    result = await module.update_config(
                        config_update.config,
                        restart_required=config_update.restart_required
                    )
                    
                    return self.response_formatter.success(
                        message=f"Configuration updated for module '{config_update.module}'",
                        data={'result': result, 'restart_required': config_update.restart_required}
                    )
                else:
                    raise HTTPException(status_code=501, detail="Configuration update not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating configuration: {e}")
                return self.response_formatter.error(
                    message="Failed to update configuration",
                    error=str(e)
                )
        
        @self.router.get("/config/{module}",
                        response_model=BaseResponse,
                        tags=["Configuration"],
                        summary="Get module configuration")
        async def get_config(
            module: str,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ):
            """Get module configuration."""
            try:
                # Get target module
                target_module = self.robot_modules.get(module)
                if not target_module:
                    raise HTTPException(status_code=404, detail=f"Module '{module}' not found")
                
                # Get configuration
                if hasattr(target_module, 'get_config'):
                    config = target_module.get_config()
                    return self.response_formatter.success(
                        message=f"Configuration retrieved for module '{module}'",
                        data={'config': config}
                    )
                else:
                    raise HTTPException(status_code=501, detail="Configuration retrieval not implemented")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting configuration: {e}")
                return self.response_formatter.error(
                    message="Failed to get configuration",
                    error=str(e)
                )
    
    async def shutdown(self) -> None:
        """Shutdown REST router."""
        try:
            self.logger.info("Shutting down REST Router")
            # Cleanup if needed
            self.logger.info("REST Router shutdown complete")
        
        except Exception as e:
            self.logger.error(f"Error during REST Router shutdown: {e}")
    
    def add_route(self, route_config: RouteConfig) -> None:
        """Add custom route.
        
        Args:
            route_config: Route configuration
        """
        self.routes.append(route_config)
        
        # Add route to FastAPI router
        if route_config.method == HTTPMethod.GET:
            self.router.get(
                route_config.path,
                tags=route_config.tags,
                summary=route_config.description
            )(route_config.handler)
        elif route_config.method == HTTPMethod.POST:
            self.router.post(
                route_config.path,
                tags=route_config.tags,
                summary=route_config.description
            )(route_config.handler)
        elif route_config.method == HTTPMethod.PUT:
            self.router.put(
                route_config.path,
                tags=route_config.tags,
                summary=route_config.description
            )(route_config.handler)
        elif route_config.method == HTTPMethod.DELETE:
            self.router.delete(
                route_config.path,
                tags=route_config.tags,
                summary=route_config.description
            )(route_config.handler)
        elif route_config.method == HTTPMethod.PATCH:
            self.router.patch(
                route_config.path,
                tags=route_config.tags,
                summary=route_config.description
            )(route_config.handler)
    
    def get_routes(self) -> List[RouteConfig]:
        """Get registered routes."""
        return self.routes.copy()