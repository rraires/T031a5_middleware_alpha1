"""Video Manager for t031a5_middleware.

Manages video capture, streaming, and processing operations for the Unitree G1 robot.
"""

import asyncio
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import time

try:
    from unitree_sdk2py.core.channel import ChannelSubscriber
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__Image_
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import Image_
except ImportError:
    logging.warning("Unitree SDK not available, using mock implementations")
    ChannelSubscriber = None
    unitree_go_msg_dds__Image_ = None
    Image_ = None

from .capture import VideoCapture, CameraSource
from .streaming import VideoStreamer, StreamingProtocol
from .processing import VideoProcessor, ProcessingMode


class VideoState(Enum):
    """Video system states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class VideoQuality(Enum):
    """Video quality presets."""
    LOW = "low"      # 480p, 15fps
    MEDIUM = "medium" # 720p, 30fps
    HIGH = "high"     # 1080p, 30fps
    ULTRA = "ultra"   # 1080p, 60fps


@dataclass
class VideoConfig:
    """Video configuration."""
    quality: VideoQuality = VideoQuality.MEDIUM
    enable_streaming: bool = True
    enable_processing: bool = True
    enable_recording: bool = False
    max_fps: int = 30
    buffer_size: int = 10
    auto_exposure: bool = True
    brightness: float = 0.5
    contrast: float = 1.0
    saturation: float = 1.0


@dataclass
class VideoStats:
    """Video statistics."""
    fps: float = 0.0
    frame_count: int = 0
    dropped_frames: int = 0
    processing_latency: float = 0.0
    streaming_clients: int = 0
    last_frame_time: float = 0.0


class VideoManager:
    """Main video manager for the t031a5_middleware.
    
    Coordinates video capture, streaming, and processing operations.
    Integrates with Unitree SDK for robot camera access.
    """
    
    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
        self.logger = logging.getLogger(__name__)
        
        # State management
        self._state = VideoState.STOPPED
        self._lock = threading.RLock()
        self._running = False
        
        # Components
        self.capture: Optional[VideoCapture] = None
        self.streamer: Optional[VideoStreamer] = None
        self.processor: Optional[VideoProcessor] = None
        
        # Statistics and monitoring
        self.stats = VideoStats()
        self._last_stats_update = time.time()
        
        # Callbacks
        self._frame_callbacks: List[Callable] = []
        self._state_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []
        
        # Unitree SDK integration
        self._unitree_subscriber: Optional[ChannelSubscriber] = None
        self._unitree_enabled = False
        
        # Threading
        self._main_thread: Optional[threading.Thread] = None
        self._stats_thread: Optional[threading.Thread] = None
        
        self.logger.info("VideoManager initialized")
    
    async def initialize(self) -> bool:
        """Initialize video manager and components."""
        try:
            with self._lock:
                if self._state != VideoState.STOPPED:
                    self.logger.warning("VideoManager already initialized")
                    return True
                
                self._set_state(VideoState.STARTING)
                
                # Initialize capture
                self.capture = VideoCapture()
                if not await self.capture.initialize():
                    raise Exception("Failed to initialize video capture")
                
                # Initialize streaming if enabled
                if self.config.enable_streaming:
                    self.streamer = VideoStreamer()
                    if not await self.streamer.initialize():
                        raise Exception("Failed to initialize video streamer")
                
                # Initialize processing if enabled
                if self.config.enable_processing:
                    self.processor = VideoProcessor()
                    if not await self.processor.initialize():
                        raise Exception("Failed to initialize video processor")
                
                # Try to initialize Unitree SDK
                await self._initialize_unitree_sdk()
                
                self._set_state(VideoState.RUNNING)
                self.logger.info("VideoManager initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize VideoManager: {e}")
            self._set_state(VideoState.ERROR)
            return False
    
    async def start(self) -> bool:
        """Start video operations."""
        try:
            with self._lock:
                if self._state == VideoState.RUNNING:
                    self.logger.warning("VideoManager already running")
                    return True
                
                if self._state != VideoState.RUNNING:
                    if not await self.initialize():
                        return False
                
                self._running = True
                
                # Start capture
                if self.capture and not await self.capture.start():
                    raise Exception("Failed to start video capture")
                
                # Start streaming
                if self.streamer and not await self.streamer.start():
                    raise Exception("Failed to start video streaming")
                
                # Start processing
                if self.processor and not await self.processor.start():
                    raise Exception("Failed to start video processing")
                
                # Start main processing thread
                self._main_thread = threading.Thread(
                    target=self._main_loop,
                    name="VideoManager-Main",
                    daemon=True
                )
                self._main_thread.start()
                
                # Start statistics thread
                self._stats_thread = threading.Thread(
                    target=self._stats_loop,
                    name="VideoManager-Stats",
                    daemon=True
                )
                self._stats_thread.start()
                
                self.logger.info("VideoManager started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start VideoManager: {e}")
            self._set_state(VideoState.ERROR)
            await self._trigger_error_callbacks(str(e))
            return False
    
    async def stop(self) -> bool:
        """Stop video operations."""
        try:
            with self._lock:
                if self._state == VideoState.STOPPED:
                    return True
                
                self._running = False
                
                # Stop components
                if self.processor:
                    await self.processor.stop()
                
                if self.streamer:
                    await self.streamer.stop()
                
                if self.capture:
                    await self.capture.stop()
                
                # Stop Unitree SDK
                if self._unitree_subscriber:
                    # Note: Unitree SDK doesn't have explicit stop method
                    self._unitree_subscriber = None
                    self._unitree_enabled = False
                
                # Wait for threads to finish
                if self._main_thread and self._main_thread.is_alive():
                    self._main_thread.join(timeout=2.0)
                
                if self._stats_thread and self._stats_thread.is_alive():
                    self._stats_thread.join(timeout=1.0)
                
                self._set_state(VideoState.STOPPED)
                self.logger.info("VideoManager stopped successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop VideoManager: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause video operations."""
        try:
            with self._lock:
                if self._state != VideoState.RUNNING:
                    return False
                
                if self.capture:
                    await self.capture.pause()
                
                if self.streamer:
                    await self.streamer.pause()
                
                if self.processor:
                    await self.processor.pause()
                
                self._set_state(VideoState.PAUSED)
                self.logger.info("VideoManager paused")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to pause VideoManager: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume video operations."""
        try:
            with self._lock:
                if self._state != VideoState.PAUSED:
                    return False
                
                if self.capture:
                    await self.capture.resume()
                
                if self.streamer:
                    await self.streamer.resume()
                
                if self.processor:
                    await self.processor.resume()
                
                self._set_state(VideoState.RUNNING)
                self.logger.info("VideoManager resumed")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to resume VideoManager: {e}")
            return False
    
    def get_state(self) -> VideoState:
        """Get current video state."""
        return self._state
    
    def get_stats(self) -> VideoStats:
        """Get current video statistics."""
        return self.stats
    
    def is_running(self) -> bool:
        """Check if video manager is running."""
        return self._state == VideoState.RUNNING
    
    def add_frame_callback(self, callback: Callable) -> None:
        """Add frame processing callback."""
        if callback not in self._frame_callbacks:
            self._frame_callbacks.append(callback)
    
    def remove_frame_callback(self, callback: Callable) -> None:
        """Remove frame processing callback."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)
    
    def add_state_callback(self, callback: Callable) -> None:
        """Add state change callback."""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)
    
    def remove_state_callback(self, callback: Callable) -> None:
        """Remove state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)
    
    def add_error_callback(self, callback: Callable) -> None:
        """Add error callback."""
        if callback not in self._error_callbacks:
            self._error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable) -> None:
        """Remove error callback."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)
    
    async def update_config(self, config: VideoConfig) -> bool:
        """Update video configuration."""
        try:
            with self._lock:
                self.config = config
                
                # Update components with new config
                if self.capture:
                    await self.capture.update_config({
                        'quality': config.quality,
                        'max_fps': config.max_fps,
                        'auto_exposure': config.auto_exposure,
                        'brightness': config.brightness,
                        'contrast': config.contrast,
                        'saturation': config.saturation
                    })
                
                if self.streamer:
                    await self.streamer.update_config({
                        'quality': config.quality,
                        'max_fps': config.max_fps
                    })
                
                if self.processor:
                    await self.processor.update_config({
                        'quality': config.quality,
                        'enable_processing': config.enable_processing
                    })
                
                self.logger.info("Video configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update video configuration: {e}")
            return False
    
    async def _initialize_unitree_sdk(self) -> None:
        """Initialize Unitree SDK for camera access."""
        try:
            if not ChannelSubscriber or not Image_:
                self.logger.warning("Unitree SDK not available")
                return
            
            # Subscribe to camera topic
            self._unitree_subscriber = ChannelSubscriber(
                "rt/image_sample",
                Image_
            )
            self._unitree_subscriber.Init(self._on_unitree_frame, 10)
            self._unitree_enabled = True
            
            self.logger.info("Unitree SDK camera initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize Unitree SDK: {e}")
            self._unitree_enabled = False
    
    def _on_unitree_frame(self, msg: Any) -> None:
        """Handle Unitree camera frame."""
        try:
            if not self._running or self._state != VideoState.RUNNING:
                return
            
            # Convert Unitree frame to OpenCV format
            # This would need proper implementation based on Unitree SDK
            frame_data = msg.data if hasattr(msg, 'data') else None
            
            if frame_data and self.capture:
                # Process frame through capture system
                asyncio.create_task(self.capture.process_external_frame(frame_data))
            
        except Exception as e:
            self.logger.error(f"Error processing Unitree frame: {e}")
    
    def _main_loop(self) -> None:
        """Main processing loop."""
        self.logger.info("Video main loop started")
        
        while self._running:
            try:
                if self._state != VideoState.RUNNING:
                    time.sleep(0.1)
                    continue
                
                # Get frame from capture
                if self.capture:
                    frame = self.capture.get_latest_frame()
                    if frame is not None:
                        # Update statistics
                        self.stats.frame_count += 1
                        self.stats.last_frame_time = time.time()
                        
                        # Process frame
                        if self.processor:
                            processed_frame = self.processor.process_frame(frame)
                            if processed_frame is not None:
                                frame = processed_frame
                        
                        # Stream frame
                        if self.streamer:
                            self.streamer.send_frame(frame)
                        
                        # Trigger callbacks
                        for callback in self._frame_callbacks:
                            try:
                                callback(frame)
                            except Exception as e:
                                self.logger.error(f"Frame callback error: {e}")
                
                # Control frame rate
                time.sleep(1.0 / self.config.max_fps)
                
            except Exception as e:
                self.logger.error(f"Error in video main loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Video main loop stopped")
    
    def _stats_loop(self) -> None:
        """Statistics monitoring loop."""
        self.logger.info("Video stats loop started")
        
        last_frame_count = 0
        
        while self._running:
            try:
                current_time = time.time()
                time_delta = current_time - self._last_stats_update
                
                if time_delta >= 1.0:  # Update every second
                    # Calculate FPS
                    frame_delta = self.stats.frame_count - last_frame_count
                    self.stats.fps = frame_delta / time_delta
                    
                    # Update streaming clients count
                    if self.streamer:
                        self.stats.streaming_clients = self.streamer.get_client_count()
                    
                    # Update processing latency
                    if self.processor:
                        self.stats.processing_latency = self.processor.get_average_latency()
                    
                    last_frame_count = self.stats.frame_count
                    self._last_stats_update = current_time
                
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error in video stats loop: {e}")
                time.sleep(1.0)
        
        self.logger.info("Video stats loop stopped")
    
    def _set_state(self, new_state: VideoState) -> None:
        """Set video state and trigger callbacks."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            
            self.logger.info(f"Video state changed: {old_state.value} -> {new_state.value}")
            
            # Trigger state callbacks
            for callback in self._state_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    self.logger.error(f"State callback error: {e}")
    
    async def _trigger_error_callbacks(self, error_message: str) -> None:
        """Trigger error callbacks."""
        for callback in self._error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error_message)
                else:
                    callback(error_message)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring."""
        return {
            'state': self._state.value,
            'running': self._running,
            'fps': self.stats.fps,
            'frame_count': self.stats.frame_count,
            'dropped_frames': self.stats.dropped_frames,
            'streaming_clients': self.stats.streaming_clients,
            'unitree_enabled': self._unitree_enabled,
            'capture_healthy': self.capture.is_healthy() if self.capture else False,
            'streamer_healthy': self.streamer.is_healthy() if self.streamer else False,
            'processor_healthy': self.processor.is_healthy() if self.processor else False,
            'last_frame_age': time.time() - self.stats.