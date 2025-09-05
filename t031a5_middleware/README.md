# t031a5_middleware

🤖 **Advanced Middleware System for Unitree Quadruped Robots**

A comprehensive, modular middleware system designed for Unitree quadruped robots, providing seamless integration of audio, video, motion control, LED management, and sensor fusion capabilities.

## 🚀 Features

### Core Components
- **🎯 Core Orchestrator**: Central coordination engine for all middleware components
- **🔄 State Machine**: Robust state management with transition handling
- **📊 Real-time Metrics**: Performance monitoring and system health tracking
- **🔍 Health Monitoring**: Automated system health checks and diagnostics

### Module Capabilities
- **🎵 Audio Manager**: TTS/ASR integration with volume control and audio processing
- **🎥 Video Manager**: Camera capture, streaming, and video processing
- **🚶 Motion Manager**: High-level and low-level motion control for quadruped robots
- **💡 LED Manager**: RGB LED control with customizable patterns and effects
- **🔬 Sensor Fusion**: Multi-sensor data integration with advanced filtering
- **🌐 API Gateway**: RESTful API and WebSocket communication interface

### Advanced Features
- **📈 Prometheus Metrics**: Built-in metrics export for monitoring
- **🔐 Security**: Authentication, rate limiting, and access control
- **⚡ Async Architecture**: High-performance asynchronous processing
- **🧪 Comprehensive Testing**: Full test suite with unit and integration tests
- **📱 Web Dashboard**: React-based control interface

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux (Ubuntu 18.04+), macOS, Windows 10+
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 1GB free space

### Hardware Support
- **Unitree Robots**: Go1, A1, Aliengo, Laikago
- **Cameras**: USB cameras, IP cameras
- **Audio**: USB microphones, speakers
- **LEDs**: WS2812B/NeoPixel strips (Raspberry Pi)

## 🛠️ Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/unitree/t031a5_middleware.git
cd t031a5_middleware

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Run the middleware
python main.py
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

### Docker Installation

```bash
# Build Docker image
docker build -t t031a5_middleware .

# Run container
docker run -p 8000:8000 -p 8001:8001 t031a5_middleware
```

## 🚀 Quick Start Guide

### Basic Usage

```python
import asyncio
from main import MiddlewareSystem

async def main():
    # Create middleware system
    middleware = MiddlewareSystem(config_path="config.json")
    
    # Initialize and start
    await middleware.initialize()
    await middleware.start()
    
    # Your application logic here
    await asyncio.sleep(10)
    
    # Stop the system
    await middleware.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Usage

```bash
# Start with default configuration
python main.py

# Start with custom configuration
python main.py --config custom_config.json

# Enable debug mode
python main.py --debug

# Set log level
python main.py --log-level DEBUG
```

### Configuration

Create a `config.json` file to customize the middleware behavior:

```json
{
  "system": {
    "name": "t031a5_middleware",
    "debug": false,
    "log_level": "INFO"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "websocket_port": 8001
  },
  "modules": {
    "audio": {
      "enabled": true,
      "sample_rate": 44100
    },
    "motion": {
      "enabled": true,
      "simulation_mode": true
    },
    "led": {
      "enabled": true,
      "num_leds": 64
    }
  }
}
```

## 📚 API Documentation

### REST API Endpoints

#### System Status
```http
GET /api/v1/status
GET /api/v1/health
GET /api/v1/metrics
```

#### Module Control
```http
POST /api/v1/modules/{module_name}/start
POST /api/v1/modules/{module_name}/stop
GET /api/v1/modules/{module_name}/status
```

#### Audio Control
```http
POST /api/v1/audio/speak
POST /api/v1/audio/listen
POST /api/v1/audio/volume
```

#### Motion Control
```http
POST /api/v1/motion/move
POST /api/v1/motion/stop
GET /api/v1/motion/pose
```

### WebSocket API

Connect to `ws://localhost:8001/ws` for real-time communication:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

// Send command
ws.send(JSON.stringify({
  type: 'command',
  module: 'motion',
  action: 'move',
  data: { x: 1.0, y: 0.0, yaw: 0.5 }
}));

// Receive updates
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=t031a5_middleware

# Run specific test module
pytest tests/test_core/

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── test_core/          # Core system tests
├── test_modules/       # Module-specific tests
├── test_api/          # API endpoint tests
└── conftest.py        # Test configuration
```

## 📊 Monitoring

### Metrics Collection

The middleware automatically collects and exports metrics:

- **System Metrics**: CPU, memory, disk usage
- **Module Metrics**: Performance, error rates, latency
- **Custom Metrics**: Application-specific measurements

### Prometheus Integration

Metrics are available at `http://localhost:9090/metrics` in Prometheus format.

### Health Checks

Health status is available at `http://localhost:8000/api/v1/health`:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "modules": "healthy",
    "system_resources": "healthy",
    "network": "healthy"
  }
}
```

## 🔧 Development

### Project Structure

```
t031a5_middleware/
├── api/                # API Gateway components
├── core/              # Core orchestration engine
├── modules/           # Hardware interface modules
├── utils/             # Utility functions
├── tests/             # Test suite
├── web_dashboard/     # React web interface
├── docs/              # Documentation
├── main.py           # Main entry point
├── config.json       # Default configuration
└── requirements.txt  # Python dependencies
```

### Adding New Modules

1. Create module directory in `modules/`
2. Implement module interface
3. Register with orchestrator
4. Add configuration options
5. Write tests

```python
from modules.base import BaseModule

class CustomModule(BaseModule):
    async def initialize(self):
        # Module initialization
        pass
    
    async def start(self):
        # Start module operations
        pass
    
    async def stop(self):
        # Stop module operations
        pass
```

### Code Style

We use the following tools for code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **isort**: Import sorting

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

## 🐳 Docker Deployment

### Building Image

```bash
docker build -t t031a5_middleware:latest .
```

### Running Container

```bash
docker run -d \
  --name middleware \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 9090:9090 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/logs:/app/logs \
  t031a5_middleware:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  middleware:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
      - "9090:9090"
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Reporting Issues

Please use the [GitHub Issues](https://github.com/unitree/t031a5_middleware/issues) page to report bugs or request features.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Unitree Robotics** for hardware support and specifications
- **FastAPI** for the excellent web framework
- **OpenCV** for computer vision capabilities
- **PyAudio** for audio processing
- **React** for the web dashboard interface

## 📞 Support

- **Documentation**: [https://docs.unitree.com/middleware](https://docs.unitree.com/middleware)
- **Issues**: [GitHub Issues](https://github.com/unitree/t031a5_middleware/issues)
- **Email**: support@unitree.com
- **Discord**: [Unitree Community](https://discord.gg/unitree)

---

**Made with ❤️ by the Unitree Robotics Team**