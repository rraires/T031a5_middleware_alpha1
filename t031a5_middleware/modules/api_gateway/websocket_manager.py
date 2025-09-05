"""WebSocket Manager for API Gateway.

Manages WebSocket connections for real-time communication with clients.
"""

import asyncio
import logging
import time
import json
import uuid
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState
import websockets


class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types."""
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # Data messages
    SENSOR_DATA = "sensor_data"
    MOTION_STATUS = "motion_status"
    AUDIO_STATUS = "audio_status"
    VIDEO_FRAME = "video_frame"
    LED_STATUS = "led_status"
    
    # Command messages
    COMMAND = "command"
    RESPONSE = "response"
    
    # Subscription messages
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    NOTIFICATION = "notification"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None


@dataclass
class ConnectionInfo:
    """WebSocket connection information."""
    connection_id: str
    websocket: WebSocket
    state: ConnectionState
    connect_time: float
    last_ping: float
    last_pong: float
    user_id: Optional[str] = None
    client_info: Dict[str, Any] = field(default_factory=dict)
    subscriptions: Set[str] = field(default_factory=set)
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class WebSocketStats:
    """WebSocket manager statistics."""
    total_connections: int = 0
    active_connections: int = 0
    peak_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    connection_errors: int = 0
    message_errors: int = 0
    average_connection_duration: float = 0.0
    
    # Subscription stats
    subscription_counts: Dict[str, int] = field(default_factory=dict)
    
    def update_connection_stats(self, connection: ConnectionInfo) -> None:
        """Update connection statistics."""
        if connection.state == ConnectionState.CONNECTED:
            self.active_connections += 1
            if self.active_connections > self.peak_connections:
                self.peak_connections = self.active_connections
        elif connection.state == ConnectionState.DISCONNECTED:
            self.active_connections = max(0, self.active_connections - 1)
            
            # Update average connection duration
            duration = time.time() - connection.connect_time
            if self.total_connections > 0:
                self.average_connection_duration = (
                    (self.average_connection_duration * (self.total_connections - 1) + duration) /
                    self.total_connections
                )
            else:
                self.average_connection_duration = duration


class WebSocketManager:
    """WebSocket connection manager.
    
    Manages WebSocket connections for real-time communication with clients.
    """
    
    def __init__(self, 
                 max_connections: int = 100,
                 heartbeat_interval: int = 30,
                 message_queue_size: int = 1000):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.message_queue_size = message_queue_size
        
        # Connection management
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        
        # Statistics
        self.stats = WebSocketStats()
        
        # Message handling
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.subscription_handlers: Dict[str, Callable] = {}
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Message queues for broadcasting
        self._broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=message_queue_size)
        
        # Callbacks
        self.connection_callbacks: List[Callable] = []
        self.disconnection_callbacks: List[Callable] = []
        self.message_callbacks: List[Callable] = []
        
        self.logger.info("WebSocket Manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize WebSocket manager.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Setup default message handlers
            self._setup_default_handlers()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info("WebSocket Manager initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing WebSocket Manager: {e}")
            return False
    
    def _setup_default_handlers(self) -> None:
        """Setup default message handlers."""
        self.message_handlers[MessageType.PING] = self._handle_ping
        self.message_handlers[MessageType.PONG] = self._handle_pong
        self.message_handlers[MessageType.SUBSCRIBE] = self._handle_subscribe
        self.message_handlers[MessageType.UNSUBSCRIBE] = self._handle_unsubscribe
        self.message_handlers[MessageType.COMMAND] = self._handle_command
    
    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """WebSocket endpoint handler.
        
        Args:
            websocket: WebSocket connection
        """
        connection_id = str(uuid.uuid4())
        connection_info = None
        
        try:
            # Check connection limit
            if len(self.connections) >= self.max_connections:
                await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
                self.logger.warning(f"Connection limit reached, rejecting connection {connection_id}")
                return
            
            # Accept connection
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                state=ConnectionState.CONNECTED,
                connect_time=time.time(),
                last_ping=time.time(),
                last_pong=time.time()
            )
            
            # Store connection
            self.connections[connection_id] = connection_info
            self.stats.total_connections += 1
            self.stats.update_connection_stats(connection_info)
            
            self.logger.info(f"WebSocket connection established: {connection_id}")
            
            # Notify connection callbacks
            await self._notify_connection_callbacks(connection_info, connected=True)
            
            # Send welcome message
            welcome_msg = WebSocketMessage(
                type=MessageType.CONNECT,
                data={
                    'connection_id': connection_id,
                    'server_time': time.time(),
                    'heartbeat_interval': self.heartbeat_interval
                }
            )
            await self._send_message(connection_info, welcome_msg)
            
            # Handle messages
            await self._handle_connection(connection_info)
        
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            self.logger.error(f"Error in WebSocket connection {connection_id}: {e}")
            self.stats.connection_errors += 1
        finally:
            # Cleanup connection
            if connection_info:
                await self._cleanup_connection(connection_info)
    
    async def _handle_connection(self, connection: ConnectionInfo) -> None:
        """Handle WebSocket connection messages.
        
        Args:
            connection: Connection information
        """
        try:
            while connection.state == ConnectionState.CONNECTED:
                try:
                    # Receive message with timeout
                    data = await asyncio.wait_for(
                        connection.websocket.receive_text(),
                        timeout=self.heartbeat_interval * 2
                    )
                    
                    # Parse message
                    try:
                        message_data = json.loads(data)
                        message = WebSocketMessage(
                            type=MessageType(message_data.get('type')),
                            data=message_data.get('data'),
                            message_id=message_data.get('message_id', str(uuid.uuid4())),
                            correlation_id=message_data.get('correlation_id'),
                            source=message_data.get('source'),
                            target=message_data.get('target')
                        )
                    except (json.JSONDecodeError, ValueError) as e:
                        self.logger.warning(f"Invalid message format from {connection.connection_id}: {e}")
                        continue
                    
                    # Update connection stats
                    connection.message_count += 1
                    connection.bytes_received += len(data)
                    self.stats.total_messages_received += 1
                    self.stats.total_bytes_received += len(data)
                    
                    # Handle message
                    await self._handle_message(connection, message)
                    
                    # Notify message callbacks
                    await self._notify_message_callbacks(connection, message)
                
                except asyncio.TimeoutError:
                    # Send ping if no recent activity
                    if time.time() - connection.last_ping > self.heartbeat_interval:
                        await self._send_ping(connection)
                
                except WebSocketDisconnect:
                    break
                
                except Exception as e:
                    self.logger.error(f"Error handling message from {connection.connection_id}: {e}")
                    self.stats.message_errors += 1
        
        except Exception as e:
            self.logger.error(f"Error in connection handler for {connection.connection_id}: {e}")
        finally:
            connection.state = ConnectionState.DISCONNECTED
    
    async def _handle_message(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle incoming WebSocket message.
        
        Args:
            connection: Connection information
            message: Received message
        """
        try:
            # Get message handler
            handler = self.message_handlers.get(message.type)
            if handler:
                await handler(connection, message)
            else:
                self.logger.warning(f"No handler for message type: {message.type}")
                
                # Send error response
                error_msg = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={'error': f'Unknown message type: {message.type}'},
                    correlation_id=message.message_id
                )
                await self._send_message(connection, error_msg)
        
        except Exception as e:
            self.logger.error(f"Error handling message {message.type} from {connection.connection_id}: {e}")
            
            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                data={'error': str(e)},
                correlation_id=message.message_id
            )
            await self._send_message(connection, error_msg)
    
    async def _handle_ping(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle ping message."""
        connection.last_ping = time.time()
        
        # Send pong response
        pong_msg = WebSocketMessage(
            type=MessageType.PONG,
            data=message.data,
            correlation_id=message.message_id
        )
        await self._send_message(connection, pong_msg)
    
    async def _handle_pong(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle pong message."""
        connection.last_pong = time.time()
    
    async def _handle_subscribe(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle subscription message."""
        try:
            subscription_topic = message.data.get('topic')
            if not subscription_topic:
                raise ValueError("Missing subscription topic")
            
            # Add subscription
            connection.subscriptions.add(subscription_topic)
            
            # Update stats
            if subscription_topic not in self.stats.subscription_counts:
                self.stats.subscription_counts[subscription_topic] = 0
            self.stats.subscription_counts[subscription_topic] += 1
            
            # Send confirmation
            response_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    'action': 'subscribe',
                    'topic': subscription_topic,
                    'success': True
                },
                correlation_id=message.message_id
            )
            await self._send_message(connection, response_msg)
            
            self.logger.debug(f"Connection {connection.connection_id} subscribed to {subscription_topic}")
        
        except Exception as e:
            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                data={'error': str(e)},
                correlation_id=message.message_id
            )
            await self._send_message(connection, error_msg)
    
    async def _handle_unsubscribe(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle unsubscription message."""
        try:
            subscription_topic = message.data.get('topic')
            if not subscription_topic:
                raise ValueError("Missing subscription topic")
            
            # Remove subscription
            connection.subscriptions.discard(subscription_topic)
            
            # Update stats
            if subscription_topic in self.stats.subscription_counts:
                self.stats.subscription_counts[subscription_topic] = max(
                    0, self.stats.subscription_counts[subscription_topic] - 1
                )
            
            # Send confirmation
            response_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    'action': 'unsubscribe',
                    'topic': subscription_topic,
                    'success': True
                },
                correlation_id=message.message_id
            )
            await self._send_message(connection, response_msg)
            
            self.logger.debug(f"Connection {connection.connection_id} unsubscribed from {subscription_topic}")
        
        except Exception as e:
            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                data={'error': str(e)},
                correlation_id=message.message_id
            )
            await self._send_message(connection, error_msg)
    
    async def _handle_command(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Handle command message."""
        # This would be implemented to handle specific commands
        # For now, just send a not implemented response
        response_msg = WebSocketMessage(
            type=MessageType.RESPONSE,
            data={
                'command': message.data.get('command'),
                'success': False,
                'error': 'Command handling not implemented'
            },
            correlation_id=message.message_id
        )
        await self._send_message(connection, response_msg)
    
    async def _send_message(self, connection: ConnectionInfo, message: WebSocketMessage) -> bool:
        """Send message to WebSocket connection.
        
        Args:
            connection: Target connection
            message: Message to send
        
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if connection.state != ConnectionState.CONNECTED:
                return False
            
            # Serialize message
            message_data = {
                'type': message.type.value,
                'data': message.data,
                'timestamp': message.timestamp,
                'message_id': message.message_id
            }
            
            if message.correlation_id:
                message_data['correlation_id'] = message.correlation_id
            if message.source:
                message_data['source'] = message.source
            if message.target:
                message_data['target'] = message.target
            
            message_json = json.dumps(message_data)
            
            # Send message
            await connection.websocket.send_text(message_json)
            
            # Update stats
            connection.bytes_sent += len(message_json)
            self.stats.total_messages_sent += 1
            self.stats.total_bytes_sent += len(message_json)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending message to {connection.connection_id}: {e}")
            return False
    
    async def _send_ping(self, connection: ConnectionInfo) -> None:
        """Send ping to connection."""
        ping_msg = WebSocketMessage(
            type=MessageType.PING,
            data={'timestamp': time.time()}
        )
        await self._send_message(connection, ping_msg)
        connection.last_ping = time.time()
    
    async def _cleanup_connection(self, connection: ConnectionInfo) -> None:
        """Cleanup connection.
        
        Args:
            connection: Connection to cleanup
        """
        try:
            connection.state = ConnectionState.DISCONNECTED
            
            # Remove from connections
            self.connections.pop(connection.connection_id, None)
            
            # Remove from user connections
            if connection.user_id:
                user_connections = self.user_connections.get(connection.user_id, set())
                user_connections.discard(connection.connection_id)
                if not user_connections:
                    self.user_connections.pop(connection.user_id, None)
            
            # Update subscription stats
            for topic in connection.subscriptions:
                if topic in self.stats.subscription_counts:
                    self.stats.subscription_counts[topic] = max(
                        0, self.stats.subscription_counts[topic] - 1
                    )
            
            # Update connection stats
            self.stats.update_connection_stats(connection)
            
            # Notify disconnection callbacks
            await self._notify_connection_callbacks(connection, connected=False)
            
            # Close WebSocket if still open
            if connection.websocket.client_state != WebSocketState.DISCONNECTED:
                try:
                    await connection.websocket.close()
                except Exception:
                    pass
            
            self.logger.info(f"Connection {connection.connection_id} cleaned up")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up connection {connection.connection_id}: {e}")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Heartbeat task
        task = asyncio.create_task(self._heartbeat_loop())
        self._background_tasks.append(task)
        
        # Broadcast task
        task = asyncio.create_task(self._broadcast_loop())
        self._background_tasks.append(task)
        
        # Cleanup task
        task = asyncio.create_task(self._cleanup_loop())
        self._background_tasks.append(task)
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop."""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                stale_connections = []
                
                # Check for stale connections
                for connection in self.connections.values():
                    if (current_time - connection.last_pong) > (self.heartbeat_interval * 3):
                        stale_connections.append(connection)
                    elif (current_time - connection.last_ping) > self.heartbeat_interval:
                        await self._send_ping(connection)
                
                # Cleanup stale connections
                for connection in stale_connections:
                    self.logger.warning(f"Closing stale connection: {connection.connection_id}")
                    await self._cleanup_connection(connection)
                
                await asyncio.sleep(self.heartbeat_interval / 2)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_loop(self) -> None:
        """Background broadcast loop."""
        while not self._shutdown_event.is_set():
            try:
                # Get message from broadcast queue
                message_data = await asyncio.wait_for(
                    self._broadcast_queue.get(),
                    timeout=1.0
                )
                
                message = message_data['message']
                connection_filter = message_data.get('filter')
                topic = message_data.get('topic')
                
                # Send to matching connections
                sent_count = 0
                for connection in list(self.connections.values()):
                    try:
                        # Check filter
                        if connection_filter and not connection_filter(connection):
                            continue
                        
                        # Check topic subscription
                        if topic and topic not in connection.subscriptions:
                            continue
                        
                        # Send message
                        if await self._send_message(connection, message):
                            sent_count += 1
                    
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to {connection.connection_id}: {e}")
                
                self.logger.debug(f"Broadcast message sent to {sent_count} connections")
            
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.cleanup_stale_connections()
                await asyncio.sleep(60)  # Cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(10)
    
    async def cleanup_stale_connections(self) -> None:
        """Cleanup stale connections."""
        try:
            current_time = time.time()
            stale_connections = []
            
            for connection in self.connections.values():
                # Check if connection is stale
                if (current_time - connection.last_pong) > (self.heartbeat_interval * 4):
                    stale_connections.append(connection)
                elif connection.websocket.client_state == WebSocketState.DISCONNECTED:
                    stale_connections.append(connection)
            
            # Cleanup stale connections
            for connection in stale_connections:
                await self._cleanup_connection(connection)
            
            if stale_connections:
                self.logger.info(f"Cleaned up {len(stale_connections)} stale connections")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up stale connections: {e}")
    
    async def _notify_connection_callbacks(self, connection: ConnectionInfo, connected: bool) -> None:
        """Notify connection callbacks."""
        for callback in self.connection_callbacks:
            try:
                await callback(connection, connected)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    async def _notify_disconnection_callbacks(self, connection: ConnectionInfo) -> None:
        """Notify disconnection callbacks."""
        for callback in self.disconnection_callbacks:
            try:
                await callback(connection)
            except Exception as e:
                self.logger.error(f"Error in disconnection callback: {e}")
    
    async def _notify_message_callbacks(self, connection: ConnectionInfo, message: WebSocketMessage) -> None:
        """Notify message callbacks."""
        for callback in self.message_callbacks:
            try:
                await callback(connection, message)
            except Exception as e:
                self.logger.error(f"Error in message callback: {e}")
    
    # Public API methods
    async def broadcast_message(self, message: WebSocketMessage, 
                              connection_filter: Optional[Callable] = None,
                              topic: Optional[str] = None) -> int:
        """Broadcast message to connections.
        
        Args:
            message: Message to broadcast
            connection_filter: Optional filter function for connections
            topic: Optional topic for subscription filtering
        
        Returns:
            Number of connections message was queued for
        """
        try:
            message_data = {
                'message': message,
                'filter': connection_filter,
                'topic': topic
            }
            
            await self._broadcast_queue.put(message_data)
            return len(self.connections)
        
        except Exception as e:
            self.logger.error(f"Error queueing broadcast message: {e}")
            return 0
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message to send
        
        Returns:
            True if message sent successfully, False otherwise
        """
        connection = self.connections.get(connection_id)
        if connection:
            return await self._send_message(connection, message)
        return False
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections of a user.
        
        Args:
            user_id: Target user ID
            message: Message to send
        
        Returns:
            Number of connections message was sent to
        """
        user_connections = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in user_connections:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information.
        
        Args:
            connection_id: Connection ID
        
        Returns:
            Connection information or None if not found
        """
        return self.connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of connection information
        """
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'total_connections': self.stats.total_connections,
            'active_connections': self.stats.active_connections,
            'peak_connections': self.stats.peak_connections,
            'total_messages_sent': self.stats.total_messages_sent,
            'total_messages_received': self.stats.total_messages_received,
            'total_bytes_sent': self.stats.total_bytes_sent,
            'total_bytes_received': self.stats.total_bytes_received,
            'connection_errors': self.stats.connection_errors,
            'message_errors': self.stats.message_errors,
            'average_connection_duration': self.stats.average_connection_duration,
            'subscription_counts': self.stats.subscription_counts.copy()
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status.
        
        Returns:
            Health status dictionary
        """
        return {
            'healthy': True,
            'active_connections': self.stats.active_connections,
            'error_rate': (
                (self.stats.connection_errors + self.stats.message_errors) /
                max(1, self.stats.total_connections + self.stats.total_messages_received)
            ),
            'queue_size': self._broadcast_queue.qsize()
        }
    
    def add_connection_callback(self, callback: Callable) -> None:
        """Add connection callback."""
        self.connection_callbacks.append(callback)
    
    def add_disconnection_callback(self, callback: Callable) -> None:
        """Add disconnection callback."""
        self.disconnection_callbacks.append(callback)
    
    def add_message_callback(self, callback: Callable) -> None:
        """Add message callback."""
        self.message_callbacks.append(callback)
    
    def add_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Add message handler."""
        self.message_handlers[message_type] = handler
    
    async def shutdown(self) -> None:
        """Shutdown WebSocket manager."""
        try:
            self.logger.info("Shutting down WebSocket Manager")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Stop background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._background_tasks.clear()
            
            # Close all connections
            for connection in list(self.connections.values()):
                await self._cleanup_connection(connection)
            
            self.logger.info("WebSocket Manager shutdown complete")
        
        except Exception as e:
            self.logger.error(f"Error during WebSocket Manager shutdown: {e}")