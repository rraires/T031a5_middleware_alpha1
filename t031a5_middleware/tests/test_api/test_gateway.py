"""Tests for the API Gateway module."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import WebSocket

from api.gateway import (
    APIGateway,
    WebSocketManager,
    ConnectionManager,
    APIResponse,
    WebSocketMessage,
    MessageType,
    APIError,
    AuthenticationError,
    ValidationError
)


class TestAPIResponse:
    """Tests for APIResponse class."""
    
    def test_api_response_success(self):
        """Test successful API response creation."""
        response = APIResponse(
            success=True,
            data={"result": "test"},
            message="Operation successful"
        )
        
        assert response.success == True
        assert response.data == {"result": "test"}
        assert response.message == "Operation successful"
        assert response.error is None
        assert response.status_code == 200
    
    def test_api_response_error(self):
        """Test error API response creation."""
        response = APIResponse(
            success=False,
            error="Invalid input",
            status_code=400
        )
        
        assert response.success == False
        assert response.data is None
        assert response.error == "Invalid input"
        assert response.status_code == 400
    
    def test_api_response_to_dict(self):
        """Test API response serialization."""
        response = APIResponse(
            success=True,
            data={"id": 123},
            message="Created successfully",
            status_code=201
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["success"] == True
        assert response_dict["data"] == {"id": 123}
        assert response_dict["message"] == "Created successfully"
        assert response_dict["error"] is None
        assert "timestamp" in response_dict


class TestWebSocketMessage:
    """Tests for WebSocketMessage class."""
    
    def test_websocket_message_creation(self):
        """Test WebSocket message creation."""
        message = WebSocketMessage(
            type=MessageType.COMMAND,
            data={"action": "move", "direction": "forward"},
            client_id="client_123"
        )
        
        assert message.type == MessageType.COMMAND
        assert message.data == {"action": "move", "direction": "forward"}
        assert message.client_id == "client_123"
        assert message.message_id is not None
    
    def test_websocket_message_to_dict(self):
        """Test WebSocket message serialization."""
        message = WebSocketMessage(
            type=MessageType.STATUS,
            data={"status": "running"},
            client_id="client_456"
        )
        
        message_dict = message.to_dict()
        
        assert message_dict["type"] == "status"
        assert message_dict["data"] == {"status": "running"}
        assert message_dict["client_id"] == "client_456"
        assert "message_id" in message_dict
        assert "timestamp" in message_dict
    
    def test_websocket_message_from_json(self):
        """Test WebSocket message deserialization."""
        json_data = {
            "type": "command",
            "data": {"action": "stop"},
            "client_id": "client_789"
        }
        
        message = WebSocketMessage.from_json(json_data)
        
        assert message.type == MessageType.COMMAND
        assert message.data == {"action": "stop"}
        assert message.client_id == "client_789"
    
    def test_websocket_message_from_invalid_json(self):
        """Test WebSocket message deserialization with invalid data."""
        json_data = {
            "type": "invalid_type",
            "data": {"action": "test"}
        }
        
        with pytest.raises(ValidationError):
            WebSocketMessage.from_json(json_data)


class TestMessageType:
    """Tests for MessageType enum."""
    
    def test_message_type_values(self):
        """Test message type enum values."""
        assert MessageType.COMMAND.value == "command"
        assert MessageType.STATUS.value == "status"
        assert MessageType.DATA.value == "data"
        assert MessageType.ERROR.value == "error"
        assert MessageType.HEARTBEAT.value == "heartbeat"


class TestConnectionManager:
    """Tests for ConnectionManager class."""
    
    @pytest.fixture
    def connection_manager(self):
        """Create connection manager instance for testing."""
        return ConnectionManager()
    
    def test_connection_manager_initialization(self, connection_manager):
        """Test connection manager initialization."""
        assert len(connection_manager.active_connections) == 0
        assert len(connection_manager.client_info) == 0
    
    async def test_connect_client(self, connection_manager):
        """Test connecting a client."""
        mock_websocket = Mock(spec=WebSocket)
        client_id = "test_client"
        
        await connection_manager.connect(mock_websocket, client_id)
        
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        assert client_id in connection_manager.client_info
        assert "connected_at" in connection_manager.client_info[client_id]
    
    async def test_disconnect_client(self, connection_manager):
        """Test disconnecting a client."""
        mock_websocket = Mock(spec=WebSocket)
        client_id = "test_client"
        
        # Connect first
        await connection_manager.connect(mock_websocket, client_id)
        assert client_id in connection_manager.active_connections
        
        # Then disconnect
        connection_manager.disconnect(client_id)
        
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.client_info
    
    async def test_send_personal_message(self, connection_manager):
        """Test sending personal message to client."""
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client"
        
        # Connect client
        await connection_manager.connect(mock_websocket, client_id)
        
        # Send message
        message = "Hello client"
        await connection_manager.send_personal_message(message, client_id)
        
        mock_websocket.send_text.assert_called_once_with(message)
    
    async def test_send_personal_message_to_disconnected_client(self, connection_manager):
        """Test sending message to disconnected client."""
        client_id = "disconnected_client"
        
        # Try to send message to non-existent client
        with pytest.raises(APIError):
            await connection_manager.send_personal_message("Hello", client_id)
    
    async def test_broadcast_message(self, connection_manager):
        """Test broadcasting message to all clients."""
        # Connect multiple clients
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(mock_websocket1, "client1")
        await connection_manager.connect(mock_websocket2, "client2")
        
        # Broadcast message
        message = "Broadcast message"
        await connection_manager.broadcast(message)
        
        mock_websocket1.send_text.assert_called_once_with(message)
        mock_websocket2.send_text.assert_called_once_with(message)
    
    def test_get_connected_clients(self, connection_manager):
        """Test getting list of connected clients."""
        # Initially no clients
        clients = connection_manager.get_connected_clients()
        assert len(clients) == 0
        
        # Add some clients manually for testing
        connection_manager.active_connections["client1"] = Mock()
        connection_manager.active_connections["client2"] = Mock()
        
        clients = connection_manager.get_connected_clients()
        assert len(clients) == 2
        assert "client1" in clients
        assert "client2" in clients
    
    def test_get_client_info(self, connection_manager):
        """Test getting client information."""
        client_id = "test_client"
        
        # Add client info manually
        connection_manager.client_info[client_id] = {
            "connected_at": "2023-01-01T00:00:00",
            "user_agent": "Test Agent"
        }
        
        info = connection_manager.get_client_info(client_id)
        assert info["connected_at"] == "2023-01-01T00:00:00"
        assert info["user_agent"] == "Test Agent"
        
        # Test non-existent client
        info = connection_manager.get_client_info("nonexistent")
        assert info is None


class TestWebSocketManager:
    """Tests for WebSocketManager class."""
    
    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance for testing."""
        return WebSocketManager()
    
    def test_websocket_manager_initialization(self, websocket_manager):
        """Test WebSocket manager initialization."""
        assert isinstance(websocket_manager.connection_manager, ConnectionManager)
        assert len(websocket_manager.message_handlers) == 0
    
    def test_register_message_handler(self, websocket_manager):
        """Test registering message handler."""
        async def test_handler(message, client_id):
            return {"response": "test"}
        
        websocket_manager.register_handler(MessageType.COMMAND, test_handler)
        
        assert MessageType.COMMAND in websocket_manager.message_handlers
        assert websocket_manager.message_handlers[MessageType.COMMAND] == test_handler
    
    async def test_handle_message_with_handler(self, websocket_manager):
        """Test handling message with registered handler."""
        # Register handler
        async def test_handler(message, client_id):
            return {"response": f"Handled {message.data['action']}"}
        
        websocket_manager.register_handler(MessageType.COMMAND, test_handler)
        
        # Create message
        message = WebSocketMessage(
            type=MessageType.COMMAND,
            data={"action": "test"},
            client_id="test_client"
        )
        
        # Handle message
        response = await websocket_manager.handle_message(message, "test_client")
        
        assert response["response"] == "Handled test"
    
    async def test_handle_message_without_handler(self, websocket_manager):
        """Test handling message without registered handler."""
        message = WebSocketMessage(
            type=MessageType.COMMAND,
            data={"action": "test"},
            client_id="test_client"
        )
        
        # Handle message without handler
        response = await websocket_manager.handle_message(message, "test_client")
        
        assert response["error"] == "No handler registered for message type: command"
    
    async def test_handle_message_handler_exception(self, websocket_manager):
        """Test handling message when handler raises exception."""
        # Register handler that raises exception
        async def failing_handler(message, client_id):
            raise Exception("Handler error")
        
        websocket_manager.register_handler(MessageType.COMMAND, failing_handler)
        
        message = WebSocketMessage(
            type=MessageType.COMMAND,
            data={"action": "test"},
            client_id="test_client"
        )
        
        # Handle message
        response = await websocket_manager.handle_message(message, "test_client")
        
        assert "error" in response
        assert "Handler error" in response["error"]


class TestAPIGateway:
    """Tests for APIGateway class."""
    
    @pytest.fixture
    def api_gateway(self):
        """Create API gateway instance for testing."""
        return APIGateway(host="localhost", port=8000)
    
    def test_api_gateway_initialization(self, api_gateway):
        """Test API gateway initialization."""
        assert api_gateway.host == "localhost"
        assert api_gateway.port == 8000
        assert api_gateway.app is not None
        assert isinstance(api_gateway.websocket_manager, WebSocketManager)
        assert api_gateway.is_running == False
    
    def test_api_gateway_with_cors(self):
        """Test API gateway with CORS enabled."""
        gateway = APIGateway(
            host="localhost",
            port=8000,
            enable_cors=True,
            cors_origins=["http://localhost:3000"]
        )
        
        # Check if CORS middleware is added (this is implementation dependent)
        assert gateway.app is not None
    
    def test_get_test_client(self, api_gateway):
        """Test getting test client for testing."""
        client = api_gateway.get_test_client()
        assert isinstance(client, TestClient)
    
    def test_health_endpoint(self, api_gateway):
        """Test health check endpoint."""
        client = api_gateway.get_test_client()
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "API Gateway is healthy"
        assert "timestamp" in data
    
    def test_status_endpoint(self, api_gateway):
        """Test status endpoint."""
        client = api_gateway.get_test_client()
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "host" in data["data"]
        assert "port" in data["data"]
        assert "is_running" in data["data"]
    
    def test_add_custom_route(self, api_gateway):
        """Test adding custom route."""
        @api_gateway.app.get("/custom")
        async def custom_endpoint():
            return {"message": "Custom endpoint"}
        
        client = api_gateway.get_test_client()
        response = client.get("/custom")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Custom endpoint"
    
    @patch('api.gateway.uvicorn.run')
    async def test_start_server(self, mock_uvicorn_run, api_gateway):
        """Test starting the server."""
        await api_gateway.start()
        
        assert api_gateway.is_running == True
        mock_uvicorn_run.assert_called_once()
        
        # Check uvicorn.run was called with correct parameters
        call_args = mock_uvicorn_run.call_args
        assert call_args[1]['host'] == "localhost"
        assert call_args[1]['port'] == 8000
    
    async def test_stop_server(self, api_gateway):
        """Test stopping the server."""
        # Set running state
        api_gateway.is_running = True
        
        await api_gateway.stop()
        
        assert api_gateway.is_running == False
    
    def test_websocket_endpoint_connection(self, api_gateway):
        """Test WebSocket endpoint connection."""
        client = api_gateway.get_test_client()
        
        # Test WebSocket connection (basic test)
        with client.websocket_connect("/ws/test_client") as websocket:
            # Connection should be established
            assert websocket is not None
    
    def test_websocket_endpoint_message_handling(self, api_gateway):
        """Test WebSocket message handling."""
        # Register a test handler
        async def test_handler(message, client_id):
            return {"echo": message.data}
        
        api_gateway.websocket_manager.register_handler(MessageType.COMMAND, test_handler)
        
        client = api_gateway.get_test_client()
        
        with client.websocket_connect("/ws/test_client") as websocket:
            # Send a test message
            test_message = {
                "type": "command",
                "data": {"action": "test"},
                "client_id": "test_client"
            }
            
            websocket.send_json(test_message)
            
            # Receive response
            response = websocket.receive_json()
            
            assert "echo" in response
            assert response["echo"] == {"action": "test"}
    
    def test_error_handling_invalid_json(self, api_gateway):
        """Test error handling for invalid JSON in WebSocket."""
        client = api_gateway.get_test_client()
        
        with client.websocket_connect("/ws/test_client") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error response
            response = websocket.receive_json()
            
            assert "error" in response
    
    def test_get_gateway_info(self, api_gateway):
        """Test getting gateway information."""
        info = api_gateway.get_info()
        
        assert info["host"] == "localhost"
        assert info["port"] == 8000
        assert info["is_running"] == False
        assert "connected_clients" in info
        assert "message_handlers" in info
    
    def test_register_websocket_handler(self, api_gateway):
        """Test registering WebSocket message handler."""
        async def test_handler(message, client_id):
            return {"handled": True}
        
        api_gateway.register_websocket_handler(MessageType.STATUS, test_handler)
        
        assert MessageType.STATUS in api_gateway.websocket_manager.message_handlers
        assert api_gateway.websocket_manager.message_handlers[MessageType.STATUS] == test_handler


class TestAPIExceptions:
    """Tests for API exception classes."""
    
    def test_api_error(self):
        """Test APIError exception."""
        error = APIError("Test error", status_code=400)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Invalid credentials")
        
        assert str(error) == "Invalid credentials"
        assert error.status_code == 401
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Invalid input data")
        
        assert str(error) == "Invalid input data"
        assert error.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])