"""Video Streaming module for t031a5_middleware.

Handles video streaming via WebRTC and HTTP protocols for real-time
video transmission to web dashboard and remote clients.
"""

import cv2
import numpy as np
import asyncio
import threading
import logging
import time
import json
import base64
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty
import websockets
from websockets.server import WebSocketServerProtocol
from aiohttp import web, WSMsgType
from aiohttp.web_ws import WebSocketResponse


class StreamProtocol(Enum):
    """Streaming protocol types."""
    HTTP_MJPEG = "http_mjpeg"
    WEBSOCKET = "websocket"
    WEBRTC = "webrtc"
    RTMP = "rtmp"
    HLS = "hls"


class StreamState(Enum):
    """Stream states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class StreamQuality(Enum):
    """Stream quality presets."""
    LOW = "low"        # 320x240, 15fps, high compression
    MEDIUM = "medium"  # 640x480, 30fps, medium compression
    HIGH = "high"      # 1280x720, 30fps, low compression
    ULTRA = "ultra"    # 1920x1080, 60fps, minimal compression


@dataclass
class StreamConfig:
    """Stream configuration."""
    protocol: StreamProtocol = StreamProtocol.WEBSOCKET
    quality: StreamQuality = StreamQuality.MEDIUM
    port: int = 8080
    host: str = "0.0.0.0"
    max_clients: int = 10
    buffer_size: int = 5
    compression_quality: int = 80  # JPEG quality 1-100
    target_fps: int = 30
    adaptive_quality: bool = True
    enable_audio: bool = False
    cors_enabled: bool = True


@dataclass
class ClientInfo:
    """Client connection information."""
    client_id: str
    protocol: StreamProtocol
    connected_at: float
    last_frame_sent: float
    frames_sent: int
    bytes_sent: int
    quality: StreamQuality
    websocket: Optional[WebSocketResponse] = None
    address: str = ""


@dataclass
class StreamStats:
    """Stream statistics."""
    active_clients: int = 0
    total_frames_sent: int = 0
    total_bytes_sent: int = 0
    current_fps: float = 0.0
    average_latency: float = 0.0
    dropped_frames: int = 0
    compression_ratio: float = 0.0
    bandwidth_usage: float = 0.0  # MB/s


class VideoStreamer:
    """Video streaming manager.
    
    Handles real-time video streaming to multiple clients using various protocols.
    Supports adaptive quality, client management, and performance monitoring.
    """
    
    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.logger = logging.getLogger(__name__)
        
        # State management
        self._state = StreamState.STOPPED
        self._lock = threading.RLock()
        self._running = False
        
        # Client management
        self._clients: Dict[str, ClientInfo] = {}
        self._client_counter = 0
        
        # Frame management
        self._frame_queue: Queue = Queue(maxsize=self.config.buffer_size)
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_timestamp = 0.0
        
        # Streaming components
        self._web_app: Optional[web.Application] = None
        self._web_runner: Optional[web.AppRunner] = None
        self._web_site: Optional[web.TCPSite] = None
        
        # Threading
        self._stream_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._stats = StreamStats()
        self._last_stats_update = time.time()
        self._frame_times: List[float] = []
        
        # Quality management
        self._quality_configs = {
            StreamQuality.LOW: {'width': 320, 'height': 240, 'fps': 15, 'quality': 60},
            StreamQuality.MEDIUM: {'width': 640, 'height': 480, 'fps': 30, 'quality': 80},
            StreamQuality.HIGH: {'width': 1280, 'height': 720, 'fps': 30, 'quality': 90},
            StreamQuality.ULTRA: {'width': 1920, 'height': 1080, 'fps': 60, 'quality': 95}
        }
        
        # Callbacks
        self._client_connected_callbacks: List[Callable] = []
        self._client_disconnected_callbacks: List[Callable] = []
        
        self.logger.info("VideoStreamer initialized")
    
    async def initialize(self) -> bool:
        """Initialize video streamer."""
        try:
            with self._lock:
                if self._state != StreamState.STOPPED:
                    self.logger.warning("VideoStreamer already initialized")
                    return True
                
                self._set_state(StreamState.STARTING)
                
                # Initialize web application
                await self._setup_web_app()
                
                self._set_state(StreamState.RUNNING)
                self.logger.info("VideoStreamer initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize VideoStreamer: {e}")
            self._set_state(StreamState.ERROR)
            return False
    
    async def start(self) -> bool:
        """Start video streaming."""
        try:
            with self._lock:
                if self._state == StreamState.RUNNING:
                    self.logger.warning("VideoStreamer already running")
                    return True
                
                if self._state != StreamState.RUNNING:
                    if not await self.initialize():
                        return False
                
                self._running = True
                
                # Start web server
                await self._start_web_server()
                
                # Start streaming thread
                self._stream_thread = threading.Thread(
                    target=self._stream_loop,
                    name="VideoStreamer-Main",
                    daemon=True
                )
                self._stream_thread.start()
                
                # Start monitor thread
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    name="VideoStreamer-Monitor",
                    daemon=True
                )
                self._monitor_thread.start()
                
                self.logger.info(f"VideoStreamer started on {self.config.host}:{self.config.port}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start VideoStreamer: {e}")
            self._set_state(StreamState.ERROR)
            return False
    
    async def stop(self) -> bool:
        """Stop video streaming."""
        try:
            with self._lock:
                if self._state == StreamState.STOPPED:
                    return True
                
                self._running = False
                
                # Disconnect all clients
                await self._disconnect_all_clients()
                
                # Stop web server
                await self._stop_web_server()
                
                # Wait for threads to finish
                if self._stream_thread and self._stream_thread.is_alive():
                    self._stream_thread.join(timeout=2.0)
                
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=1.0)
                
                # Clear frame queue
                while not self._frame_queue.empty():
                    try:
                        self._frame_queue.get_nowait()
                    except Empty:
                        break
                
                self._latest_frame = None
                self._clients.clear()
                
                self._set_state(StreamState.STOPPED)
                self.logger.info("VideoStreamer stopped successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop VideoStreamer: {e}")
            return False
    
    async def add_frame(self, frame: np.ndarray) -> bool:
        """Add frame to streaming queue."""
        try:
            if self._state != StreamState.RUNNING:
                return False
            
            current_time = time.time()
            
            # Update latest frame
            self._latest_frame = frame.copy()
            self._frame_timestamp = current_time
            
            # Add to queue (non-blocking)
            try:
                self._frame_queue.put_nowait((frame.copy(), current_time))
            except:
                # Queue full, drop oldest frame
                try:
                    self._frame_queue.get_nowait()
                    self._frame_queue.put_nowait((frame.copy(), current_time))
                    self._stats.dropped_frames += 1
                except:
                    pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding frame: {e}")
            return False
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update streaming configuration."""
        try:
            with self._lock:
                # Update config values
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                # Apply quality changes to clients
                if 'quality' in config:
                    for client in self._clients.values():
                        client.quality = self.config.quality
                
                self.logger.info("Streaming configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update streaming configuration: {e}")
            return False
    
    def add_client_connected_callback(self, callback: Callable) -> None:
        """Add client connected callback."""
        self._client_connected_callbacks.append(callback)
    
    def add_client_disconnected_callback(self, callback: Callable) -> None:
        """Add client disconnected callback."""
        self._client_disconnected_callbacks.append(callback)
    
    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)
    
    def get_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients."""
        return [asdict(client) for client in self._clients.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        self._update_statistics()
        return asdict(self._stats)
    
    async def _setup_web_app(self) -> None:
        """Setup web application."""
        self._web_app = web.Application()
        
        # Add CORS middleware if enabled
        if self.config.cors_enabled:
            self._web_app.middlewares.append(self._cors_middleware)
        
        # Setup routes
        self._web_app.router.add_get('/stream', self._handle_websocket)
        self._web_app.router.add_get('/mjpeg', self._handle_mjpeg)
        self._web_app.router.add_get('/stats', self._handle_stats)
        self._web_app.router.add_get('/clients', self._handle_clients)
        self._web_app.router.add_post('/config', self._handle_config_update)
        
        # Health check endpoint
        self._web_app.router.add_get('/health', self._handle_health)
    
    async def _start_web_server(self) -> None:
        """Start web server."""
        self._web_runner = web.AppRunner(self._web_app)
        await self._web_runner.setup()
        
        self._web_site = web.TCPSite(
            self._web_runner,
            self.config.host,
            self.config.port
        )
        await self._web_site.start()
    
    async def _stop_web_server(self) -> None:
        """Stop web server."""
        if self._web_site:
            await self._web_site.stop()
            self._web_site = None
        
        if self._web_runner:
            await self._web_runner.cleanup()
            self._web_runner = None
    
    async def _cors_middleware(self, request, handler):
        """CORS middleware."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    async def _handle_websocket(self, request) -> WebSocketResponse:
        """Handle WebSocket connections."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        # Check client limit
        if len(self._clients) >= self.config.max_clients:
            await ws.close(code=1013, message=b'Server overloaded')
            return ws
        
        # Create client info
        client_id = f"ws_{self._client_counter}"
        self._client_counter += 1
        
        client_info = ClientInfo(
            client_id=client_id,
            protocol=StreamProtocol.WEBSOCKET,
            connected_at=time.time(),
            last_frame_sent=0.0,
            frames_sent=0,
            bytes_sent=0,
            quality=self.config.quality,
            websocket=ws,
            address=request.remote or "unknown"
        )
        
        self._clients[client_id] = client_info
        
        # Notify callbacks
        for callback in self._client_connected_callbacks:
            try:
                await callback(client_info)
            except Exception as e:
                self.logger.error(f"Error in client connected callback: {e}")
        
        self.logger.info(f"WebSocket client connected: {client_id} from {client_info.address}")
        
        try:
            # Handle WebSocket messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_client_message(client_id, data)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON from client {client_id}")
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error from {client_id}: {ws.exception()}")
                    break
        
        except Exception as e:
            self.logger.error(f"WebSocket error for client {client_id}: {e}")
        
        finally:
            # Clean up client
            if client_id in self._clients:
                del self._clients[client_id]
            
            # Notify callbacks
            for callback in self._client_disconnected_callbacks:
                try:
                    await callback(client_info)
                except Exception as e:
                    self.logger.error(f"Error in client disconnected callback: {e}")
            
            self.logger.info(f"WebSocket client disconnected: {client_id}")
        
        return ws
    
    async def _handle_mjpeg(self, request) -> web.StreamResponse:
        """Handle MJPEG stream."""
        # Check client limit
        if len(self._clients) >= self.config.max_clients:
            return web.Response(status=503, text="Server overloaded")
        
        # Create client info
        client_id = f"mjpeg_{self._client_counter}"
        self._client_counter += 1
        
        client_info = ClientInfo(
            client_id=client_id,
            protocol=StreamProtocol.HTTP_MJPEG,
            connected_at=time.time(),
            last_frame_sent=0.0,
            frames_sent=0,
            bytes_sent=0,
            quality=self.config.quality,
            address=request.remote or "unknown"
        )
        
        self._clients[client_id] = client_info
        
        # Notify callbacks
        for callback in self._client_connected_callbacks:
            try:
                await callback(client_info)
            except Exception as e:
                self.logger.error(f"Error in client connected callback: {e}")
        
        self.logger.info(f"MJPEG client connected: {client_id} from {client_info.address}")
        
        # Setup MJPEG response
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
                'Cache-Control': 'no-cache',
                'Connection': 'close'
            }
        )
        
        await response.prepare(request)
        
        try:
            frame_time = 1.0 / self._quality_configs[client_info.quality]['fps']
            last_frame_time = 0.0
            
            while self._running and client_id in self._clients:
                current_time = time.time()
                
                # Control frame rate
                if current_time - last_frame_time < frame_time:
                    await asyncio.sleep(0.01)
                    continue
                
                if self._latest_frame is not None:
                    # Encode frame
                    encoded_frame = await self._encode_frame_for_client(self._latest_frame, client_info)
                    
                    if encoded_frame:
                        # Send MJPEG frame
                        await response.write(b'--frame\r\n')
                        await response.write(b'Content-Type: image/jpeg\r\n')
                        await response.write(f'Content-Length: {len(encoded_frame)}\r\n\r\n'.encode())
                        await response.write(encoded_frame)
                        await response.write(b'\r\n')
                        
                        # Update client stats
                        client_info.frames_sent += 1
                        client_info.bytes_sent += len(encoded_frame)
                        client_info.last_frame_sent = current_time
                        
                        last_frame_time = current_time
                
                await asyncio.sleep(0.001)
        
        except Exception as e:
            self.logger.error(f"MJPEG streaming error for client {client_id}: {e}")
        
        finally:
            # Clean up client
            if client_id in self._clients:
                del self._clients[client_id]
            
            # Notify callbacks
            for callback in self._client_disconnected_callbacks:
                try:
                    await callback(client_info)
                except Exception as e:
                    self.logger.error(f"Error in client disconnected callback: {e}")
            
            self.logger.info(f"MJPEG client disconnected: {client_id}")
        
        return response
    
    async def _handle_stats(self, request) -> web.Response:
        """Handle statistics request."""
        stats = self.get_statistics()
        return web.json_response(stats)
    
    async def _handle_clients(self, request) -> web.Response:
        """Handle clients list request."""
        clients = self.get_clients()
        return web.json_response({'clients': clients})
    
    async def _handle_config_update(self, request) -> web.Response:
        """Handle configuration update request."""
        try:
            data = await request.json()
            success = await self.update_config(data)
            
            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'status': 'error', 'message': 'Failed to update config'}, status=400)
        
        except Exception as e:
            return web.json_response({'status': 'error', 'message': str(e)}, status=400)
    
    async def _handle_health(self, request) -> web.Response:
        """Handle health check request."""
        health_data = {
            'status': self._state.value,
            'running': self._running,
            'clients': len(self._clients),
            'timestamp': time.time()
        }
        return web.json_response(health_data)
    
    async def _handle_client_message(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle message from WebSocket client."""
        try:
            client = self._clients.get(client_id)
            if not client:
                return
            
            message_type = data.get('type')
            
            if message_type == 'quality_change':
                quality_str = data.get('quality', 'medium')
                try:
                    new_quality = StreamQuality(quality_str)
                    client.quality = new_quality
                    self.logger.info(f"Client {client_id} changed quality to {quality_str}")
                except ValueError:
                    self.logger.warning(f"Invalid quality '{quality_str}' from client {client_id}")
            
            elif message_type == 'ping':
                # Send pong response
                if client.websocket:
                    await client.websocket.send_str(json.dumps({'type': 'pong', 'timestamp': time.time()}))
        
        except Exception as e:
            self.logger.error(f"Error handling client message from {client_id}: {e}")
    
    def _stream_loop(self) -> None:
        """Main streaming loop."""
        self.logger.info("Video streaming loop started")
        
        while self._running:
            try:
                if self._state != StreamState.RUNNING or not self._clients:
                    time.sleep(0.1)
                    continue
                
                # Get frame from queue
                try:
                    frame, timestamp = self._frame_queue.get(timeout=0.1)
                except Empty:
                    continue
                
                # Stream to WebSocket clients
                asyncio.create_task(self._stream_to_websocket_clients(frame, timestamp))
                
            except Exception as e:
                self.logger.error(f"Error in streaming loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Video streaming loop stopped")
    
    def _monitor_loop(self) -> None:
        """Statistics monitoring loop."""
        self.logger.info("Video streaming monitor started")
        
        while self._running:
            try:
                # Update statistics
                self._update_statistics()
                
                # Clean up disconnected clients
                self._cleanup_disconnected_clients()
                
                # Adaptive quality adjustment
                if self.config.adaptive_quality:
                    self._adjust_quality_based_on_performance()
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in streaming monitor: {e}")
                time.sleep(1.0)
        
        self.logger.info("Video streaming monitor stopped")
    
    async def _stream_to_websocket_clients(self, frame: np.ndarray, timestamp: float) -> None:
        """Stream frame to WebSocket clients."""
        if not self._clients:
            return
        
        # Group clients by quality for efficient encoding
        quality_groups = {}
        for client in self._clients.values():
            if client.protocol == StreamProtocol.WEBSOCKET and client.websocket:
                if client.quality not in quality_groups:
                    quality_groups[client.quality] = []
                quality_groups[client.quality].append(client)
        
        # Encode frames for each quality level
        for quality, clients in quality_groups.items():
            try:
                # Encode frame for this quality
                encoded_frame = await self._encode_frame_for_quality(frame, quality)
                
                if encoded_frame:
                    # Send to all clients with this quality
                    for client in clients:
                        try:
                            if client.websocket and not client.websocket.closed:
                                # Send as base64 encoded image
                                frame_data = {
                                    'type': 'frame',
                                    'data': base64.b64encode(encoded_frame).decode('utf-8'),
                                    'timestamp': timestamp,
                                    'format': 'jpeg'
                                }
                                
                                await client.websocket.send_str(json.dumps(frame_data))
                                
                                # Update client stats
                                client.frames_sent += 1
                                client.bytes_sent += len(encoded_frame)
                                client.last_frame_sent = timestamp
                        
                        except Exception as e:
                            self.logger.error(f"Error sending frame to WebSocket client {client.client_id}: {e}")
                            # Mark for cleanup
                            if client.websocket:
                                await client.websocket.close()
            
            except Exception as e:
                self.logger.error(f"Error encoding frame for quality {quality}: {e}")
    
    async def _encode_frame_for_client(self, frame: np.ndarray, client: ClientInfo) -> Optional[bytes]:
        """Encode frame for specific client."""
        return await self._encode_frame_for_quality(frame, client.quality)
    
    async def _encode_frame_for_quality(self, frame: np.ndarray, quality: StreamQuality) -> Optional[bytes]:
        """Encode frame for specific quality level."""
        try:
            quality_config = self._quality_configs[quality]
            
            # Resize frame if needed
            target_width = quality_config['width']
            target_height = quality_config['height']
            
            if frame.shape[1] != target_width or frame.shape[0] != target_height:
                frame = cv2.resize(frame, (target_width, target_height))
            
            # Encode as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality_config['quality']]
            success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error encoding frame for quality {quality}: {e}")
            return None
    
    def _cleanup_disconnected_clients(self) -> None:
        """Clean up disconnected clients."""
        disconnected_clients = []
        
        for client_id, client in self._clients.items():
            if client.protocol == StreamProtocol.WEBSOCKET:
                if client.websocket and client.websocket.closed:
                    disconnected_clients.append(client_id)
            elif client.protocol == StreamProtocol.HTTP_MJPEG:
                # Check if client hasn't received frames recently
                if time.time() - client.last_frame_sent > 30.0:  # 30 seconds timeout
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            if client_id in self._clients:
                del self._clients[client_id]
                self.logger.info(f"Cleaned up disconnected client: {client_id}")
    
    def _adjust_quality_based_on_performance(self) -> None:
        """Adjust streaming quality based on performance metrics."""
        try:
            # Simple adaptive quality based on client count and performance
            client_count = len(self._clients)
            
            if client_count > 5 and self.config.quality == StreamQuality.ULTRA:
                self.config.quality = StreamQuality.HIGH
                self.logger.info("Reduced quality to HIGH due to high client count")
            elif client_count > 8 and self.config.quality == StreamQuality.HIGH:
                self.config.quality = StreamQuality.MEDIUM
                self.logger.info("Reduced quality to MEDIUM due to very high client count")
            elif client_count <= 3 and self.config.quality == StreamQuality.MEDIUM:
                self.config.quality = StreamQuality.HIGH
                self.logger.info("Increased quality to HIGH due to low client count")
        
        except Exception as e:
            self.logger.error(f"Error in adaptive quality adjustment: {e}")
    
    def _update_statistics(self) -> None:
        """Update streaming statistics."""
        current_time = time.time()
        
        # Update basic stats
        self._stats.active_clients = len(self._clients)
        
        # Calculate total frames and bytes sent
        total_frames = sum(client.frames_sent for client in self._clients.values())
        total_bytes = sum(client.bytes_sent for client in self._clients.values())
        
        self._stats.total_frames_sent = total_frames
        self._stats.total_bytes_sent = total_bytes
        
        # Calculate FPS
        if self._frame_times:
            recent_frames = [t for t in self._frame_times if current_time - t < 1.0]
            self._stats.current_fps = len(recent_frames)
            
            # Keep only recent frame times
            self._frame_times = recent_frames
        
        # Calculate bandwidth usage (MB/s)
        time_diff = current_time - self._last_stats_update
        if time_diff > 0:
            bytes_diff = total_bytes - getattr(self._stats, '_last_total_bytes', 0)
            self._stats.bandwidth_usage = (bytes_diff / time_diff) / (1024 * 1024)  # MB/s
            self._stats._last_total_bytes = total_bytes
        
        self._last_stats_update = current_time
        
        # Add current frame time
        self._frame_times.append(current_time)
    
    async def _disconnect_all_clients(self) -> None:
        """Disconnect all clients."""
        for client in list(self._clients.values()):
            try:
                if client.websocket and not client.websocket.closed:
                    await client.websocket.close()
            except Exception as e:
                self.logger.error(f"Error disconnecting client {client.client_id}: {e}")
        
        self._clients.clear()
    
    def _set_state(self, new_state: StreamState) -> None:
        """Set streaming state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.logger.info(f"Streaming state changed: {old_state.value} -> {new_state.value}")