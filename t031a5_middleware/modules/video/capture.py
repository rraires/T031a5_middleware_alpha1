"""Video Capture module for t031a5_middleware.

Handles video capture from multiple sources including webcams, IP cameras,
and Unitree robot cameras using OpenCV.
"""

import cv2
import numpy as np
import asyncio
import threading
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum
from queue import Queue, Empty


class CameraSource(Enum):
    """Camera source types."""
    WEBCAM = "webcam"
    IP_CAMERA = "ip_camera"
    UNITREE_HEAD = "unitree_head"
    UNITREE_CHEST = "unitree_chest"
    FILE = "file"
    RTSP = "rtsp"


class CaptureState(Enum):
    """Capture states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class CameraConfig:
    """Camera configuration."""
    source: CameraSource = CameraSource.WEBCAM
    device_id: int = 0
    url: str = ""
    width: int = 640
    height: int = 480
    fps: int = 30
    auto_exposure: bool = True
    exposure: float = 0.5
    brightness: float = 0.5
    contrast: float = 1.0
    saturation: float = 1.0
    gain: float = 0.5
    focus: float = 0.5
    auto_focus: bool = True
    buffer_size: int = 1


@dataclass
class FrameInfo:
    """Frame information."""
    timestamp: float
    frame_id: int
    source: CameraSource
    width: int
    height: int
    channels: int
    format: str


class VideoCapture:
    """Video capture manager.
    
    Handles video capture from multiple sources with OpenCV integration.
    Supports webcams, IP cameras, RTSP streams, and Unitree robot cameras.
    """
    
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self.logger = logging.getLogger(__name__)
        
        # State management
        self._state = CaptureState.STOPPED
        self._lock = threading.RLock()
        self._running = False
        
        # OpenCV capture objects
        self._captures: Dict[CameraSource, cv2.VideoCapture] = {}
        self._active_sources: List[CameraSource] = []
        
        # Frame management
        self._frame_queue: Queue = Queue(maxsize=10)
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_frame_info: Optional[FrameInfo] = None
        self._frame_id = 0
        
        # Threading
        self._capture_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._frames_captured = 0
        self._frames_dropped = 0
        self._last_frame_time = 0.0
        self._capture_fps = 0.0
        
        # Health monitoring
        self._last_health_check = time.time()
        self._consecutive_failures = 0
        self._max_failures = 5
        
        self.logger.info("VideoCapture initialized")
    
    async def initialize(self) -> bool:
        """Initialize video capture."""
        try:
            with self._lock:
                if self._state != CaptureState.STOPPED:
                    self.logger.warning("VideoCapture already initialized")
                    return True
                
                self._set_state(CaptureState.STARTING)
                
                # Initialize primary camera source
                if not await self._initialize_source(self.config.source):
                    raise Exception(f"Failed to initialize primary source: {self.config.source}")
                
                self._set_state(CaptureState.RUNNING)
                self.logger.info("VideoCapture initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize VideoCapture: {e}")
            self._set_state(CaptureState.ERROR)
            return False
    
    async def start(self) -> bool:
        """Start video capture."""
        try:
            with self._lock:
                if self._state == CaptureState.RUNNING:
                    self.logger.warning("VideoCapture already running")
                    return True
                
                if self._state != CaptureState.RUNNING:
                    if not await self.initialize():
                        return False
                
                self._running = True
                
                # Start capture thread
                self._capture_thread = threading.Thread(
                    target=self._capture_loop,
                    name="VideoCapture-Main",
                    daemon=True
                )
                self._capture_thread.start()
                
                # Start monitor thread
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    name="VideoCapture-Monitor",
                    daemon=True
                )
                self._monitor_thread.start()
                
                self.logger.info("VideoCapture started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start VideoCapture: {e}")
            self._set_state(CaptureState.ERROR)
            return False
    
    async def stop(self) -> bool:
        """Stop video capture."""
        try:
            with self._lock:
                if self._state == CaptureState.STOPPED:
                    return True
                
                self._running = False
                
                # Release all capture objects
                for source, capture in self._captures.items():
                    try:
                        if capture and capture.isOpened():
                            capture.release()
                    except Exception as e:
                        self.logger.error(f"Error releasing capture {source}: {e}")
                
                self._captures.clear()
                self._active_sources.clear()
                
                # Wait for threads to finish
                if self._capture_thread and self._capture_thread.is_alive():
                    self._capture_thread.join(timeout=2.0)
                
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=1.0)
                
                # Clear frame data
                while not self._frame_queue.empty():
                    try:
                        self._frame_queue.get_nowait()
                    except Empty:
                        break
                
                self._latest_frame = None
                self._latest_frame_info = None
                
                self._set_state(CaptureState.STOPPED)
                self.logger.info("VideoCapture stopped successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop VideoCapture: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause video capture."""
        try:
            with self._lock:
                if self._state != CaptureState.RUNNING:
                    return False
                
                self._set_state(CaptureState.PAUSED)
                self.logger.info("VideoCapture paused")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to pause VideoCapture: {e}")
            return False
    
    async def resume(self) -> bool:
        """Resume video capture."""
        try:
            with self._lock:
                if self._state != CaptureState.PAUSED:
                    return False
                
                self._set_state(CaptureState.RUNNING)
                self.logger.info("VideoCapture resumed")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to resume VideoCapture: {e}")
            return False
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest captured frame."""
        return self._latest_frame
    
    def get_latest_frame_info(self) -> Optional[FrameInfo]:
        """Get information about the latest frame."""
        return self._latest_frame_info
    
    def get_frame_from_queue(self, timeout: float = 0.1) -> Optional[Tuple[np.ndarray, FrameInfo]]:
        """Get frame from queue with timeout."""
        try:
            return self._frame_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def is_healthy(self) -> bool:
        """Check if capture is healthy."""
        if self._state != CaptureState.RUNNING:
            return False
        
        # Check if we're receiving frames
        if time.time() - self._last_frame_time > 5.0:  # No frame for 5 seconds
            return False
        
        # Check consecutive failures
        if self._consecutive_failures >= self._max_failures:
            return False
        
        return True
    
    async def add_source(self, source: CameraSource, config: Optional[Dict[str, Any]] = None) -> bool:
        """Add additional camera source."""
        try:
            with self._lock:
                if source in self._captures:
                    self.logger.warning(f"Source {source} already exists")
                    return True
                
                if await self._initialize_source(source, config):
                    self._active_sources.append(source)
                    self.logger.info(f"Added camera source: {source}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add source {source}: {e}")
            return False
    
    async def remove_source(self, source: CameraSource) -> bool:
        """Remove camera source."""
        try:
            with self._lock:
                if source not in self._captures:
                    return True
                
                # Release capture
                capture = self._captures[source]
                if capture and capture.isOpened():
                    capture.release()
                
                del self._captures[source]
                
                if source in self._active_sources:
                    self._active_sources.remove(source)
                
                self.logger.info(f"Removed camera source: {source}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove source {source}: {e}")
            return False
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update capture configuration."""
        try:
            with self._lock:
                # Update config values
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                # Apply configuration to active captures
                for source, capture in self._captures.items():
                    if capture and capture.isOpened():
                        await self._apply_config_to_capture(capture, self.config)
                
                self.logger.info("Capture configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update capture configuration: {e}")
            return False
    
    async def process_external_frame(self, frame_data: Any) -> bool:
        """Process frame from external source (e.g., Unitree SDK)."""
        try:
            # Convert external frame data to OpenCV format
            # This would need proper implementation based on the external source format
            if isinstance(frame_data, np.ndarray):
                frame = frame_data
            else:
                # Convert from other formats (bytes, etc.)
                frame = self._convert_external_frame(frame_data)
            
            if frame is not None:
                await self._process_frame(frame, CameraSource.UNITREE_HEAD)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to process external frame: {e}")
            return False
    
    async def _initialize_source(self, source: CameraSource, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize a camera source."""
        try:
            capture = None
            
            if source == CameraSource.WEBCAM:
                capture = cv2.VideoCapture(self.config.device_id)
            
            elif source == CameraSource.IP_CAMERA or source == CameraSource.RTSP:
                if self.config.url:
                    capture = cv2.VideoCapture(self.config.url)
                else:
                    raise Exception(f"URL required for {source}")
            
            elif source == CameraSource.FILE:
                if self.config.url:
                    capture = cv2.VideoCapture(self.config.url)
                else:
                    raise Exception("File path required for FILE source")
            
            elif source in [CameraSource.UNITREE_HEAD, CameraSource.UNITREE_CHEST]:
                # Unitree cameras are handled externally via SDK
                # We create a placeholder that will receive frames via process_external_frame
                self._captures[source] = None
                return True
            
            if capture is None:
                raise Exception(f"Failed to create capture for {source}")
            
            if not capture.isOpened():
                capture.release()
                raise Exception(f"Failed to open capture for {source}")
            
            # Apply configuration
            await self._apply_config_to_capture(capture, self.config)
            
            # Test capture
            ret, frame = capture.read()
            if not ret or frame is None:
                capture.release()
                raise Exception(f"Failed to read test frame from {source}")
            
            self._captures[source] = capture
            self.logger.info(f"Initialized camera source: {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize source {source}: {e}")
            return False
    
    async def _apply_config_to_capture(self, capture: cv2.VideoCapture, config: CameraConfig) -> None:
        """Apply configuration to OpenCV capture."""
        try:
            # Set resolution
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
            
            # Set FPS
            capture.set(cv2.CAP_PROP_FPS, config.fps)
            
            # Set buffer size
            capture.set(cv2.CAP_PROP_BUFFERSIZE, config.buffer_size)
            
            # Set exposure
            if config.auto_exposure:
                capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto exposure on
            else:
                capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
                capture.set(cv2.CAP_PROP_EXPOSURE, config.exposure)
            
            # Set other properties
            capture.set(cv2.CAP_PROP_BRIGHTNESS, config.brightness)
            capture.set(cv2.CAP_PROP_CONTRAST, config.contrast)
            capture.set(cv2.CAP_PROP_SATURATION, config.saturation)
            capture.set(cv2.CAP_PROP_GAIN, config.gain)
            
            # Set focus
            if config.auto_focus:
                capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            else:
                capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                capture.set(cv2.CAP_PROP_FOCUS, config.focus)
            
        except Exception as e:
            self.logger.warning(f"Some capture properties could not be set: {e}")
    
    def _capture_loop(self) -> None:
        """Main capture loop."""
        self.logger.info("Video capture loop started")
        
        frame_time = 1.0 / self.config.fps
        last_capture_time = time.time()
        
        while self._running:
            try:
                if self._state != CaptureState.RUNNING:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                # Control capture rate
                if current_time - last_capture_time < frame_time:
                    time.sleep(0.001)
                    continue
                
                # Capture from all active sources
                for source in self._active_sources:
                    capture = self._captures.get(source)
                    if capture and capture.isOpened():
                        ret, frame = capture.read()
                        if ret and frame is not None:
                            asyncio.create_task(self._process_frame(frame, source))
                            self._consecutive_failures = 0
                        else:
                            self._consecutive_failures += 1
                            if self._consecutive_failures >= self._max_failures:
                                self.logger.error(f"Too many capture failures for {source}")
                                self._set_state(CaptureState.ERROR)
                
                last_capture_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                self._consecutive_failures += 1
                time.sleep(0.1)
        
        self.logger.info("Video capture loop stopped")
    
    def _monitor_loop(self) -> None:
        """Health monitoring loop."""
        self.logger.info("Video capture monitor started")
        
        while self._running:
            try:
                current_time = time.time()
                
                # Health check every 5 seconds
                if current_time - self._last_health_check >= 5.0:
                    if not self.is_healthy():
                        self.logger.warning("Video capture health check failed")
                        # Attempt recovery
                        asyncio.create_task(self._attempt_recovery())
                    
                    self._last_health_check = current_time
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in capture monitor: {e}")
                time.sleep(1.0)
        
        self.logger.info("Video capture monitor stopped")
    
    async def _process_frame(self, frame: np.ndarray, source: CameraSource) -> None:
        """Process captured frame."""
        try:
            self._frame_id += 1
            current_time = time.time()
            
            # Create frame info
            frame_info = FrameInfo(
                timestamp=current_time,
                frame_id=self._frame_id,
                source=source,
                width=frame.shape[1],
                height=frame.shape[0],
                channels=frame.shape[2] if len(frame.shape) > 2 else 1,
                format="BGR"
            )
            
            # Update latest frame
            self._latest_frame = frame.copy()
            self._latest_frame_info = frame_info
            self._last_frame_time = current_time
            self._frames_captured += 1
            
            # Add to queue (non-blocking)
            try:
                self._frame_queue.put_nowait((frame.copy(), frame_info))
            except:
                # Queue full, drop oldest frame
                try:
                    self._frame_queue.get_nowait()
                    self._frame_queue.put_nowait((frame.copy(), frame_info))
                    self._frames_dropped += 1
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
    
    def _convert_external_frame(self, frame_data: Any) -> Optional[np.ndarray]:
        """Convert external frame data to OpenCV format."""
        try:
            # This would need proper implementation based on the external format
            # For now, assume it's already in a compatible format
            if isinstance(frame_data, bytes):
                # Convert bytes to numpy array
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return frame
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error converting external frame: {e}")
            return None
    
    async def _attempt_recovery(self) -> None:
        """Attempt to recover from capture errors."""
        try:
            self.logger.info("Attempting capture recovery")
            
            # Reinitialize failed sources
            for source in self._active_sources.copy():
                capture = self._captures.get(source)
                if not capture or not capture.isOpened():
                    self.logger.info(f"Reinitializing source: {source}")
                    await self.remove_source(source)
                    await self.add_source(source)
            
            # Reset failure counter
            self._consecutive_failures = 0
            
            if self._state == CaptureState.ERROR:
                self._set_state(CaptureState.RUNNING)
            
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
    
    def _set_state(self, new_state: CaptureState) -> None:
        """Set capture state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.logger.info(f"Capture state changed: {old_state.value} -> {new_state.value}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get capture statistics."""
        current_time = time.time()
        
        # Calculate FPS
        if self._frames_captured > 0 and self._last_frame_time > 0:
            elapsed = current_time - (self._last_frame_time - (self._frames_captured / self.config.fps))
            self._capture_fps = self._frames_captured / elapsed if elapsed > 0 else 0
        
        return {
            'state': self._state.value,
            'active_sources': [s.value for s in self._active_sources],
            'frames_captured': self._frames_captured,
            'frames_dropped': self._frames_dropped,
            'capture_fps': self._capture_fps,
            'consecutive_failures': self._consecutive_failures,
            'last_frame_age': current_time - self._last_frame_time if self._last_frame_time > 0 else 0,
            'queue_size': self._frame_queue.qsize(),
            'healthy': self.is_healthy()
        }