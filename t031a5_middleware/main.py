#!/usr/bin/env python3
"""
Main entry point for the t031a5_middleware system.
This module initializes and orchestrates all middleware components.
"""

import asyncio
import signal
import sys
import os
from pathlib import Path
from typing import Optional
import argparse
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core components
from core.orchestrator import CoreOrchestrator, Task, TaskPriority
from core.state_machine import StateMachine, SystemState
from modules.audio_manager import AudioManager
from modules.motion_manager import MotionManager
from modules.led_manager import LEDManager
from modules.video_manager import VideoManager
from modules.sensor_fusion import SensorFusion
from api.gateway import APIGateway
from utils.logger import get_logger, setup_logging
from utils.metrics import get_metrics_collector
from utils.health_check import get_health_monitor

# Global logger
logger = get_logger(__name__)

class MiddlewareSystem:
    """
    Main middleware system that coordinates all components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.orchestrator = None
        self.state_machine = None
        self.modules = {}
        self.api_gateway = None
        self.running = False
        self._shutdown_event = asyncio.Event()
        
    def _load_config(self, config_path: Optional[str]) -> dict:
        """
        Load configuration from file or use defaults.
        """
        default_config = {
            "system": {
                "name": "t031a5_middleware",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "websocket_port": 8001
            },
            "modules": {
                "audio": {
                    "enabled": True,
                    "sample_rate": 44100,
                    "channels": 2
                },
                "motion": {
                    "enabled": True,
                    "simulation_mode": True
                },
                "led": {
                    "enabled": True,
                    "num_leds": 64
                },
                "video": {
                    "enabled": True,
                    "camera_index": 0,
                    "resolution": [640, 480]
                },
                "sensor_fusion": {
                    "enabled": True,
                    "update_rate": 50
                }
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True,
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "metrics": {
                "enabled": True,
                "collection_interval": 10
            },
            "health_check": {
                "enabled": True,
                "check_interval": 30
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                self._deep_merge(default_config, user_config)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("Using default configuration")
            
        return default_config
    
    def _deep_merge(self, base: dict, update: dict) -> None:
        """
        Deep merge two dictionaries.
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    async def initialize(self) -> None:
        """
        Initialize all system components.
        """
        logger.info("Initializing middleware system...")
        
        try:
            # Setup logging
            setup_logging(
                level=self.config["logging"]["level"],
                file_enabled=self.config["logging"]["file_enabled"],
                console_enabled=self.config["logging"]["console_enabled"]
            )
            
            # Initialize state machine
            self.state_machine = StateMachine()
            self._setup_state_transitions()
            
            # Initialize orchestrator
            self.orchestrator = CoreOrchestrator()
            await self.orchestrator.initialize()
            
            # Initialize modules
            await self._initialize_modules()
            
            # Initialize API Gateway
            if self.config["api"]:
                self.api_gateway = APIGateway(
                    host=self.config["api"]["host"],
                    port=self.config["api"]["port"],
                    websocket_port=self.config["api"]["websocket_port"]
                )
                await self.api_gateway.initialize()
            
            # Start metrics collection
            if self.config["metrics"]["enabled"]:
                metrics_collector = get_metrics_collector()
                await metrics_collector.start_collection(
                    interval=self.config["metrics"]["collection_interval"]
                )
            
            # Start health monitoring
            if self.config["health_check"]["enabled"]:
                health_monitor = get_health_monitor()
                await health_monitor.start_monitoring(
                    interval=self.config["health_check"]["check_interval"]
                )
            
            # Transition to initialized state
            await self.state_machine.trigger("initialize")
            
            logger.info("Middleware system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize middleware system: {e}")
            await self.state_machine.trigger("error")
            raise
    
    def _setup_state_transitions(self) -> None:
        """
        Setup state machine transitions.
        """
        # Add states
        states = [
            SystemState.IDLE,
            SystemState.INITIALIZING,
            SystemState.RUNNING,
            SystemState.PAUSED,
            SystemState.STOPPING,
            SystemState.ERROR
        ]
        
        # Add transitions
        transitions = [
            ("initialize", SystemState.IDLE, SystemState.INITIALIZING),
            ("start", SystemState.INITIALIZING, SystemState.RUNNING),
            ("pause", SystemState.RUNNING, SystemState.PAUSED),
            ("resume", SystemState.PAUSED, SystemState.RUNNING),
            ("stop", SystemState.RUNNING, SystemState.STOPPING),
            ("stop", SystemState.PAUSED, SystemState.STOPPING),
            ("shutdown", SystemState.STOPPING, SystemState.IDLE),
            ("error", "*", SystemState.ERROR),
            ("reset", SystemState.ERROR, SystemState.IDLE)
        ]
        
        for trigger, from_state, to_state in transitions:
            self.state_machine.add_transition(trigger, from_state, to_state)
    
    async def _initialize_modules(self) -> None:
        """
        Initialize all enabled modules.
        """
        module_configs = self.config["modules"]
        
        # Initialize Audio Manager
        if module_configs["audio"]["enabled"]:
            self.modules["audio"] = AudioManager()
            await self.modules["audio"].initialize()
            self.orchestrator.register_module("audio", self.modules["audio"])
            logger.info("Audio Manager initialized")
        
        # Initialize Motion Manager
        if module_configs["motion"]["enabled"]:
            self.modules["motion"] = MotionManager(
                simulation_mode=module_configs["motion"]["simulation_mode"]
            )
            await self.modules["motion"].initialize()
            self.orchestrator.register_module("motion", self.modules["motion"])
            logger.info("Motion Manager initialized")
        
        # Initialize LED Manager
        if module_configs["led"]["enabled"]:
            self.modules["led"] = LEDManager(
                num_leds=module_configs["led"]["num_leds"]
            )
            await self.modules["led"].initialize()
            self.orchestrator.register_module("led", self.modules["led"])
            logger.info("LED Manager initialized")
        
        # Initialize Video Manager
        if module_configs["video"]["enabled"]:
            self.modules["video"] = VideoManager(
                camera_index=module_configs["video"]["camera_index"]
            )
            await self.modules["video"].initialize()
            self.orchestrator.register_module("video", self.modules["video"])
            logger.info("Video Manager initialized")
        
        # Initialize Sensor Fusion
        if module_configs["sensor_fusion"]["enabled"]:
            self.modules["sensor_fusion"] = SensorFusion(
                update_rate=module_configs["sensor_fusion"]["update_rate"]
            )
            await self.modules["sensor_fusion"].initialize()
            self.orchestrator.register_module("sensor_fusion", self.modules["sensor_fusion"])
            logger.info("Sensor Fusion initialized")
    
    async def start(self) -> None:
        """
        Start the middleware system.
        """
        logger.info("Starting middleware system...")
        
        try:
            # Start orchestrator
            await self.orchestrator.start()
            
            # Start API Gateway
            if self.api_gateway:
                await self.api_gateway.start()
            
            # Transition to running state
            await self.state_machine.trigger("start")
            
            self.running = True
            logger.info("Middleware system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start middleware system: {e}")
            await self.state_machine.trigger("error")
            raise
    
    async def stop(self) -> None:
        """
        Stop the middleware system.
        """
        logger.info("Stopping middleware system...")
        
        try:
            self.running = False
            
            # Transition to stopping state
            await self.state_machine.trigger("stop")
            
            # Stop API Gateway
            if self.api_gateway:
                await self.api_gateway.stop()
            
            # Stop orchestrator
            if self.orchestrator:
                await self.orchestrator.stop()
            
            # Stop modules
            for name, module in self.modules.items():
                try:
                    await module.shutdown()
                    logger.info(f"{name} module stopped")
                except Exception as e:
                    logger.error(f"Error stopping {name} module: {e}")
            
            # Stop monitoring services
            health_monitor = get_health_monitor()
            await health_monitor.stop_monitoring()
            
            metrics_collector = get_metrics_collector()
            await metrics_collector.stop_collection()
            
            # Transition to idle state
            await self.state_machine.trigger("shutdown")
            
            logger.info("Middleware system stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            await self.state_machine.trigger("error")
    
    async def run(self) -> None:
        """
        Main run loop.
        """
        await self.initialize()
        await self.start()
        
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        finally:
            await self.stop()
    
    def shutdown(self) -> None:
        """
        Signal shutdown.
        """
        logger.info("Shutdown signal received")
        self._shutdown_event.set()


def setup_signal_handlers(middleware: MiddlewareSystem) -> None:
    """
    Setup signal handlers for graceful shutdown.
    """
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        middleware.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="t031a5_middleware - Unitree Robot Middleware System"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="t031a5_middleware 1.0.0"
    )
    
    return parser.parse_args()


async def main() -> None:
    """
    Main entry point.
    """
    args = parse_arguments()
    
    # Create middleware system
    middleware = MiddlewareSystem(config_path=args.config)
    
    # Override config with command line arguments
    if args.debug:
        middleware.config["system"]["debug"] = True
        middleware.config["logging"]["level"] = "DEBUG"
    
    if args.log_level:
        middleware.config["logging"]["level"] = args.log_level
    
    # Setup signal handlers
    setup_signal_handlers(middleware)
    
    try:
        # Run the middleware system
        await middleware.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    logger.info("Middleware system exited")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())