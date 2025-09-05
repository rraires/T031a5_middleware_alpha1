"""Sensor Fusion Manager for t031a5_middleware.

Manages sensor data aggregation, fusion, and processing for the Unitree G1 robot.
Integrates multiple sensor inputs including IMU, lidar, cameras, and odometry
for enhanced perception, localization, and navigation.
"""

import asyncio
import threading
import logging
import time
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from queue import Queue, Empty
import json
from collections import deque

# Unitree SDK imports (would be actual imports in real implementation)
try:
    from unitree_sdk2py.core.channel import ChannelSubscriber
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
except ImportError:
    # Mock classes for development
    class ChannelSubscriber:
        pass
    class unitree_go_msg_dds__LowState_:
        pass
    class unitree_go_msg_dds__SportModeState_:
        pass


class SensorType(Enum):
    """Types of sensors."""
    IMU = "imu"
    LIDAR = "lidar"
    CAMERA = "camera"
    ODOMETRY = "odometry"
    GPS = "gps"
    ULTRASONIC = "ultrasonic"
    FORCE_TORQUE = "force_torque"
    JOINT_ENCODER = "joint_encoder"
    BATTERY = "battery"
    TEMPERATURE = "temperature"


class SensorState(Enum):
    """Sensor states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    ERROR = "error"
    CALIBRATING = "calibrating"


class FusionMode(Enum):
    """Sensor fusion modes."""
    DISABLED = "disabled"
    BASIC = "basic"
    ADVANCED = "advanced"
    SLAM = "slam"
    NAVIGATION = "navigation"
    CUSTOM = "custom"


class FusionState(Enum):
    """Fusion system states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    CALIBRATING = "calibrating"


@dataclass
class SensorData:
    """Generic sensor data structure."""
    sensor_type: SensorType
    sensor_id: str
    timestamp: float
    data: Dict[str, Any]
    quality: float = 1.0
    confidence: float = 1.0
    frame_id: str = "base_link"
    sequence: int = 0


@dataclass
class IMUData:
    """IMU sensor data."""
    acceleration: Tuple[float, float, float]  # x, y, z (m/s²)
    angular_velocity: Tuple[float, float, float]  # x, y, z (rad/s)
    orientation: Tuple[float, float, float, float]  # quaternion (x, y, z, w)
    linear_acceleration: Tuple[float, float, float]  # without gravity
    magnetic_field: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    temperature: float = 0.0
    timestamp: float = 0.0


@dataclass
class OdometryData:
    """Odometry data."""
    position: Tuple[float, float, float]  # x, y, z
    orientation: Tuple[float, float, float, float]  # quaternion
    linear_velocity: Tuple[float, float, float]  # x, y, z
    angular_velocity: Tuple[float, float, float]  # x, y, z
    covariance: List[float] = field(default_factory=lambda: [0.0] * 36)
    timestamp: float = 0.0


@dataclass
class LidarData:
    """Lidar sensor data."""
    points: np.ndarray  # Point cloud data
    intensities: Optional[np.ndarray] = None
    ranges: Optional[np.ndarray] = None
    angles: Optional[np.ndarray] = None
    min_range: float = 0.0
    max_range: float = 100.0
    timestamp: float = 0.0


@dataclass
class FusionConfig:
    """Sensor fusion configuration."""
    mode: FusionMode = FusionMode.BASIC
    update_rate: float = 100.0  # Hz
    buffer_size: int = 1000
    enable_prediction: bool = True
    enable_smoothing: bool = True
    outlier_threshold: float = 3.0
    confidence_threshold: float = 0.5
    sync_tolerance: float = 0.01  # seconds
    
    # Sensor weights for fusion
    sensor_weights: Dict[SensorType, float] = field(default_factory=lambda: {
        SensorType.IMU: 1.0,
        SensorType.ODOMETRY: 0.8,
        SensorType.LIDAR: 0.9,
        SensorType.CAMERA: 0.7,
        SensorType.GPS: 0.6
    })
    
    # Kalman filter parameters
    process_noise: float = 0.01
    measurement_noise: float = 0.1
    initial_uncertainty: float = 1.0


@dataclass
class FusionStats:
    """Sensor fusion statistics."""
    total_updates: int = 0
    fusion_rate: float = 0.0
    average_latency: float = 0.0
    sensor_counts: Dict[SensorType, int] = field(default_factory=dict)
    outliers_rejected: int = 0
    prediction_accuracy: float = 0.0
    system_health: float = 1.0
    last_update: float = 0.0


@dataclass
class RobotState:
    """Fused robot state."""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    linear_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    angular_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    linear_acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    angular_acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    
    # Uncertainty estimates
    position_covariance: List[float] = field(default_factory=lambda: [0.0] * 9)
    orientation_covariance: List[float] = field(default_factory=lambda: [0.0] * 9)
    velocity_covariance: List[float] = field(default_factory=lambda: [0.0] * 9)
    
    # Additional state information
    battery_level: float = 1.0
    temperature: float = 25.0
    system_health: float = 1.0
    timestamp: float = 0.0
    confidence: float = 1.0


class SensorFusion:
    """Sensor Fusion Manager.
    
    Manages sensor data aggregation, fusion, and processing for the Unitree G1 robot.
    Provides real-time state estimation by combining multiple sensor inputs.
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.logger = logging.getLogger(__name__)
        
        # State management
        self._state = FusionState.STOPPED
        self._lock = threading.RLock()
        self._running = False
        
        # Sensor management
        self._sensors: Dict[str, Dict[str, Any]] = {}
        self._sensor_states: Dict[str, SensorState] = {}
        self._sensor_subscribers: Dict[str, Any] = {}
        
        # Data buffers
        self._sensor_buffers: Dict[str, deque] = {}
        self._fusion_buffer: deque = deque(maxlen=self.config.buffer_size)
        
        # Current robot state
        self._current_state = RobotState()
        self._predicted_state = RobotState()
        
        # Filters and processors
        self._kalman_filter = None
        self._complementary_filter = None
        self._processors: Dict[SensorType, Any] = {}
        
        # Threading
        self._fusion_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._prediction_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._stats = FusionStats()
        self._update_times: deque = deque(maxlen=100)
        self._last_stats_update = time.time()
        
        # Callbacks
        self._state_callbacks: List[Callable] = []
        self._sensor_callbacks: Dict[SensorType, List[Callable]] = {}
        self._fusion_callbacks: List[Callable] = []
        
        # Synchronization
        self._sync_queues: Dict[SensorType, Queue] = {}
        self._sync_tolerance = self.config.sync_tolerance
        
        self.logger.info("SensorFusion initialized")
    
    async def initialize(self) -> bool:
        """Initialize sensor fusion system."""
        try:
            with self._lock:
                if self._state != FusionState.STOPPED:
                    self.logger.warning("SensorFusion already initialized")
                    return True
                
                self._set_state(FusionState.STARTING)
                
                # Initialize filters
                await self._initialize_filters()
                
                # Initialize processors
                await self._initialize_processors()
                
                # Initialize sensor subscribers
                await self._initialize_sensors()
                
                # Initialize synchronization queues
                for sensor_type in SensorType:
                    self._sync_queues[sensor_type] = Queue(maxsize=100)
                    self._sensor_callbacks[sensor_type] = []
                
                self._set_state(FusionState.RUNNING)
                self.logger.info("SensorFusion initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize SensorFusion: {e}")
            self._set_state(FusionState.ERROR)
            return False
    
    async def start(self) -> bool:
        """Start sensor fusion."""
        try:
            with self._lock:
                if self._state == FusionState.RUNNING:
                    self.logger.warning("SensorFusion already running")
                    return True
                
                if self._state != FusionState.RUNNING:
                    if not await self.initialize():
                        return False
                
                self._running = True
                
                # Start fusion thread
                self._fusion_thread = threading.Thread(
                    target=self._fusion_loop,
                    name="SensorFusion-Main",
                    daemon=True
                )
                self._fusion_thread.start()
                
                # Start prediction thread
                if self.config.enable_prediction:
                    self._prediction_thread = threading.Thread(
                        target=self._prediction_loop,
                        name="SensorFusion-Prediction",
                        daemon=True
                    )
                    self._prediction_thread.start()
                
                # Start monitor thread
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    name="SensorFusion-Monitor",
                    daemon=True
                )
                self._monitor_thread.start()
                
                self.logger.info("SensorFusion started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start SensorFusion: {e}")
            self._set_state(FusionState.ERROR)
            return False
    
    async def stop(self) -> bool:
        """Stop sensor fusion."""
        try:
            with self._lock:
                if self._state == FusionState.STOPPED:
                    return True
                
                self._running = False
                
                # Stop sensor subscribers
                for subscriber in self._sensor_subscribers.values():
                    try:
                        if hasattr(subscriber, 'close'):
                            subscriber.close()
                    except Exception as e:
                        self.logger.error(f"Error stopping sensor subscriber: {e}")
                
                # Wait for threads to finish
                for thread in [self._fusion_thread, self._prediction_thread, self._monitor_thread]:
                    if thread and thread.is_alive():
                        thread.join(timeout=2.0)
                
                # Clear buffers
                self._sensor_buffers.clear()
                self._fusion_buffer.clear()
                
                # Clear queues
                for queue in self._sync_queues.values():
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                        except Empty:
                            break
                
                self._set_state(FusionState.STOPPED)
                self.logger.info("SensorFusion stopped successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop SensorFusion: {e}")
            return False
    
    async def add_sensor(self, sensor_id: str, sensor_type: SensorType, config: Dict[str, Any]) -> bool:
        """Add a sensor to the fusion system."""
        try:
            with self._lock:
                if sensor_id in self._sensors:
                    self.logger.warning(f"Sensor {sensor_id} already exists")
                    return False
                
                self._sensors[sensor_id] = {
                    'type': sensor_type,
                    'config': config,
                    'last_update': 0.0,
                    'update_count': 0,
                    'error_count': 0
                }
                
                self._sensor_states[sensor_id] = SensorState.DISCONNECTED
                self._sensor_buffers[sensor_id] = deque(maxlen=self.config.buffer_size)
                
                # Initialize sensor subscriber if system is running
                if self._state == FusionState.RUNNING:
                    await self._initialize_sensor_subscriber(sensor_id, sensor_type, config)
                
                self.logger.info(f"Added sensor: {sensor_id} ({sensor_type.value})")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add sensor {sensor_id}: {e}")
            return False
    
    async def remove_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor from the fusion system."""
        try:
            with self._lock:
                if sensor_id not in self._sensors:
                    self.logger.warning(f"Sensor {sensor_id} not found")
                    return False
                
                # Stop sensor subscriber
                if sensor_id in self._sensor_subscribers:
                    subscriber = self._sensor_subscribers[sensor_id]
                    if hasattr(subscriber, 'close'):
                        subscriber.close()
                    del self._sensor_subscribers[sensor_id]
                
                # Remove sensor data
                del self._sensors[sensor_id]
                del self._sensor_states[sensor_id]
                if sensor_id in self._sensor_buffers:
                    del self._sensor_buffers[sensor_id]
                
                self.logger.info(f"Removed sensor: {sensor_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove sensor {sensor_id}: {e}")
            return False
    
    async def process_sensor_data(self, sensor_data: SensorData) -> bool:
        """Process incoming sensor data."""
        try:
            sensor_id = sensor_data.sensor_id
            
            if sensor_id not in self._sensors:
                self.logger.warning(f"Unknown sensor: {sensor_id}")
                return False
            
            # Update sensor state
            self._sensor_states[sensor_id] = SensorState.ACTIVE
            self._sensors[sensor_id]['last_update'] = sensor_data.timestamp
            self._sensors[sensor_id]['update_count'] += 1
            
            # Add to sensor buffer
            self._sensor_buffers[sensor_id].append(sensor_data)
            
            # Add to synchronization queue
            sensor_type = sensor_data.sensor_type
            if sensor_type in self._sync_queues:
                try:
                    self._sync_queues[sensor_type].put_nowait(sensor_data)
                except:
                    # Queue full, drop oldest data
                    try:
                        self._sync_queues[sensor_type].get_nowait()
                        self._sync_queues[sensor_type].put_nowait(sensor_data)
                    except:
                        pass
            
            # Trigger sensor-specific callbacks
            if sensor_type in self._sensor_callbacks:
                for callback in self._sensor_callbacks[sensor_type]:
                    try:
                        await callback(sensor_data)
                    except Exception as e:
                        self.logger.error(f"Error in sensor callback: {e}")
            
            # Update statistics
            if sensor_type not in self._stats.sensor_counts:
                self._stats.sensor_counts[sensor_type] = 0
            self._stats.sensor_counts[sensor_type] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            if sensor_data.sensor_id in self._sensors:
                self._sensors[sensor_data.sensor_id]['error_count'] += 1
            return False
    
    def get_current_state(self) -> RobotState:
        """Get current fused robot state."""
        with self._lock:
            return self._current_state
    
    def get_predicted_state(self, prediction_time: float = 0.1) -> RobotState:
        """Get predicted robot state."""
        with self._lock:
            if self.config.enable_prediction:
                return self._predict_state(self._current_state, prediction_time)
            return self._current_state
    
    def get_sensor_states(self) -> Dict[str, SensorState]:
        """Get all sensor states."""
        return self._sensor_states.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        self._update_statistics()
        return asdict(self._stats)
    
    def add_state_callback(self, callback: Callable) -> None:
        """Add state update callback."""
        self._state_callbacks.append(callback)
    
    def add_sensor_callback(self, sensor_type: SensorType, callback: Callable) -> None:
        """Add sensor-specific callback."""
        if sensor_type not in self._sensor_callbacks:
            self._sensor_callbacks[sensor_type] = []
        self._sensor_callbacks[sensor_type].append(callback)
    
    def add_fusion_callback(self, callback: Callable) -> None:
        """Add fusion update callback."""
        self._fusion_callbacks.append(callback)
    
    async def calibrate_sensors(self, duration: float = 10.0) -> bool:
        """Calibrate sensors."""
        try:
            self._set_state(FusionState.CALIBRATING)
            self.logger.info(f"Starting sensor calibration for {duration} seconds")
            
            # Collect calibration data
            calibration_data = {}
            start_time = time.time()
            
            while time.time() - start_time < duration:
                for sensor_id, buffer in self._sensor_buffers.items():
                    if buffer:
                        if sensor_id not in calibration_data:
                            calibration_data[sensor_id] = []
                        calibration_data[sensor_id].extend(list(buffer))
                        buffer.clear()
                
                await asyncio.sleep(0.1)
            
            # Process calibration data
            await self._process_calibration_data(calibration_data)
            
            self._set_state(FusionState.RUNNING)
            self.logger.info("Sensor calibration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Sensor calibration failed: {e}")
            self._set_state(FusionState.ERROR)
            return False
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update fusion configuration."""
        try:
            with self._lock:
                # Update config values
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                # Reinitialize filters if necessary
                if any(key in config for key in ['process_noise', 'measurement_noise', 'initial_uncertainty']):
                    await self._initialize_filters()
                
                self.logger.info("Fusion configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update fusion configuration: {e}")
            return False
    
    async def _initialize_filters(self) -> None:
        """Initialize sensor fusion filters."""
        try:
            # Initialize Kalman filter for state estimation
            from .filters import KalmanFilter
            
            state_dim = 12  # position, velocity, acceleration, orientation
            measurement_dim = 6  # typical measurement dimension
            
            self._kalman_filter = KalmanFilter(
                state_dim=state_dim,
                measurement_dim=measurement_dim,
                process_noise=self.config.process_noise,
                measurement_noise=self.config.measurement_noise
            )
            
            # Initialize complementary filter for IMU fusion
            from .filters import ComplementaryFilter
            
            self._complementary_filter = ComplementaryFilter(
                alpha=0.98  # Weight for gyroscope vs accelerometer
            )
            
            self.logger.info("Fusion filters initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing filters: {e}")
            raise
    
    async def _initialize_processors(self) -> None:
        """Initialize sensor processors."""
        try:
            from .processors import IMUProcessor, LidarProcessor, VisionProcessor, OdometryProcessor
            
            self._processors[SensorType.IMU] = IMUProcessor()
            self._processors[SensorType.LIDAR] = LidarProcessor()
            self._processors[SensorType.CAMERA] = VisionProcessor()
            self._processors[SensorType.ODOMETRY] = OdometryProcessor()
            
            self.logger.info("Sensor processors initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing processors: {e}")
            raise
    
    async def _initialize_sensors(self) -> None:
        """Initialize sensor subscribers."""
        try:
            # Initialize Unitree SDK subscribers
            for sensor_id, sensor_info in self._sensors.items():
                sensor_type = sensor_info['type']
                config = sensor_info['config']
                await self._initialize_sensor_subscriber(sensor_id, sensor_type, config)
            
            self.logger.info("Sensor subscribers initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing sensors: {e}")
            raise
    
    async def _initialize_sensor_subscriber(self, sensor_id: str, sensor_type: SensorType, config: Dict[str, Any]) -> None:
        """Initialize individual sensor subscriber."""
        try:
            if sensor_type == SensorType.IMU:
                # Subscribe to IMU data from Unitree SDK
                subscriber = ChannelSubscriber("rt/lowstate", unitree_go_msg_dds__LowState_)
                subscriber.Init(self._imu_callback, 10)
                self._sensor_subscribers[sensor_id] = subscriber
                
            elif sensor_type == SensorType.ODOMETRY:
                # Subscribe to odometry data
                subscriber = ChannelSubscriber("rt/sportmodestate", unitree_go_msg_dds__SportModeState_)
                subscriber.Init(self._odometry_callback, 10)
                self._sensor_subscribers[sensor_id] = subscriber
                
            # Add other sensor types as needed
            
            self._sensor_states[sensor_id] = SensorState.CONNECTED
            self.logger.info(f"Initialized subscriber for sensor: {sensor_id}")
            
        except Exception as e:
            self.logger.error(f"Error initializing sensor subscriber {sensor_id}: {e}")
            self._sensor_states[sensor_id] = SensorState.ERROR
    
    def _imu_callback(self, msg) -> None:
        """IMU data callback."""
        try:
            # Extract IMU data from Unitree message
            imu_data = IMUData(
                acceleration=(msg.imu.accelerometer[0], msg.imu.accelerometer[1], msg.imu.accelerometer[2]),
                angular_velocity=(msg.imu.gyroscope[0], msg.imu.gyroscope[1], msg.imu.gyroscope[2]),
                orientation=(msg.imu.quaternion[0], msg.imu.quaternion[1], msg.imu.quaternion[2], msg.imu.quaternion[3]),
                linear_acceleration=(msg.imu.accelerometer[0], msg.imu.accelerometer[1], msg.imu.accelerometer[2] - 9.81),
                timestamp=time.time()
            )
            
            sensor_data = SensorData(
                sensor_type=SensorType.IMU,
                sensor_id="unitree_imu",
                timestamp=imu_data.timestamp,
                data=asdict(imu_data)
            )
            
            # Process asynchronously
            asyncio.create_task(self.process_sensor_data(sensor_data))
            
        except Exception as e:
            self.logger.error(f"Error in IMU callback: {e}")
    
    def _odometry_callback(self, msg) -> None:
        """Odometry data callback."""
        try:
            # Extract odometry data from Unitree message
            odometry_data = OdometryData(
                position=(msg.position[0], msg.position[1], msg.position[2]),
                orientation=(msg.imu.quaternion[0], msg.imu.quaternion[1], msg.imu.quaternion[2], msg.imu.quaternion[3]),
                linear_velocity=(msg.velocity[0], msg.velocity[1], msg.velocity[2]),
                angular_velocity=(msg.imu.gyroscope[0], msg.imu.gyroscope[1], msg.imu.gyroscope[2]),
                timestamp=time.time()
            )
            
            sensor_data = SensorData(
                sensor_type=SensorType.ODOMETRY,
                sensor_id="unitree_odometry",
                timestamp=odometry_data.timestamp,
                data=asdict(odometry_data)
            )
            
            # Process asynchronously
            asyncio.create_task(self.process_sensor_data(sensor_data))
            
        except Exception as e:
            self.logger.error(f"Error in odometry callback: {e}")
    
    def _fusion_loop(self) -> None:
        """Main sensor fusion loop."""
        self.logger.info("Sensor fusion loop started")
        
        update_interval = 1.0 / self.config.update_rate
        last_update_time = 0.0
        
        while self._running:
            try:
                if self._state != FusionState.RUNNING:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                # Control update rate
                if current_time - last_update_time < update_interval:
                    time.sleep(0.001)
                    continue
                
                # Collect synchronized sensor data
                synchronized_data = self._collect_synchronized_data(current_time)
                
                if synchronized_data:
                    # Perform sensor fusion
                    fused_state = self._fuse_sensor_data(synchronized_data, current_time)
                    
                    # Update current state
                    with self._lock:
                        self._current_state = fused_state
                        self._current_state.timestamp = current_time
                    
                    # Add to fusion buffer
                    self._fusion_buffer.append((fused_state, current_time))
                    
                    # Trigger fusion callbacks
                    for callback in self._fusion_callbacks:
                        try:
                            asyncio.create_task(callback(fused_state))
                        except Exception as e:
                            self.logger.error(f"Error in fusion callback: {e}")
                    
                    # Update statistics
                    self._update_times.append(current_time)
                    self._stats.total_updates += 1
                    self._stats.last_update = current_time
                
                last_update_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in fusion loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Sensor fusion loop stopped")
    
    def _prediction_loop(self) -> None:
        """State prediction loop."""
        self.logger.info("State prediction loop started")
        
        prediction_interval = 0.01  # 100 Hz prediction
        
        while self._running:
            try:
                if self._state != FusionState.RUNNING:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                # Predict future state
                with self._lock:
                    self._predicted_state = self._predict_state(self._current_state, prediction_interval)
                
                time.sleep(prediction_interval)
                
            except Exception as e:
                self.logger.error(f"Error in prediction loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("State prediction loop stopped")
    
    def _monitor_loop(self) -> None:
        """System monitoring loop."""
        self.logger.info("Sensor fusion monitor started")
        
        while self._running:
            try:
                # Update statistics
                self._update_statistics()
                
                # Check sensor health
                self._check_sensor_health()
                
                # Update system health
                self._update_system_health()
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in fusion monitor: {e}")
                time.sleep(1.0)
        
        self.logger.info("Sensor fusion monitor stopped")
    
    def _collect_synchronized_data(self, current_time: float) -> Dict[SensorType, List[SensorData]]:
        """Collect synchronized sensor data."""
        synchronized_data = {}
        
        for sensor_type, queue in self._sync_queues.items():
            sensor_data_list = []
            
            # Collect data within sync tolerance
            while not queue.empty():
                try:
                    data = queue.get_nowait()
                    if abs(data.timestamp - current_time) <= self._sync_tolerance:
                        sensor_data_list.append(data)
                    elif data.timestamp < current_time - self._sync_tolerance:
                        # Data too old, discard
                        continue
                    else:
                        # Data too new, put back
                        queue.put_nowait(data)
                        break
                except Empty:
                    break
            
            if sensor_data_list:
                synchronized_data[sensor_type] = sensor_data_list
        
        return synchronized_data
    
    def _fuse_sensor_data(self, synchronized_data: Dict[SensorType, List[SensorData]], timestamp: float) -> RobotState:
        """Fuse synchronized sensor data."""
        try:
            # Start with current state as base
            fused_state = RobotState(timestamp=timestamp)
            
            # Process each sensor type
            for sensor_type, data_list in synchronized_data.items():
                if sensor_type in self._processors:
                    processor = self._processors[sensor_type]
                    processed_data = processor.process(data_list)
                    
                    # Apply sensor weight
                    weight = self.config.sensor_weights.get(sensor_type, 1.0)
                    
                    # Fuse processed data into state
                    fused_state = self._apply_sensor_update(fused_state, processed_data, weight, sensor_type)
            
            # Apply Kalman filter if available
            if self._kalman_filter:
                fused_state = self._apply_kalman_filter(fused_state)
            
            # Apply smoothing if enabled
            if self.config.enable_smoothing:
                fused_state = self._apply_smoothing(fused_state)
            
            return fused_state
            
        except Exception as e:
            self.logger.error(f"Error fusing sensor data: {e}")
            return self._current_state
    
    def _apply_sensor_update(self, state: RobotState, sensor_data: Dict[str, Any], weight: float, sensor_type: SensorType) -> RobotState:
        """Apply sensor update to robot state."""
        try:
            # This is a simplified fusion approach
            # In a real implementation, you would use more sophisticated methods
            
            if sensor_type == SensorType.IMU:
                # Update orientation and acceleration from IMU
                if 'orientation' in sensor_data:
                    state.orientation = sensor_data['orientation']
                if 'linear_acceleration' in sensor_data:
                    state.linear_acceleration = sensor_data['linear_acceleration']
                if 'angular_velocity' in sensor_data:
                    state.angular_velocity = sensor_data['angular_velocity']
            
            elif sensor_type == SensorType.ODOMETRY:
                # Update position and velocity from odometry
                if 'position' in sensor_data:
                    state.position = sensor_data['position']
                if 'linear_velocity' in sensor_data:
                    state.linear_velocity = sensor_data['linear_velocity']
            
            # Apply weight to the update
            state.confidence *= weight
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error applying sensor update: {e}")
            return state
    
    def _apply_kalman_filter(self, state: RobotState) -> RobotState:
        """Apply Kalman filter to state estimate."""
        try:
            if self._kalman_filter:
                # Convert state to vector
                state_vector = np.array([
                    *state.position,
                    *state.linear_velocity,
                    *state.linear_acceleration,
                    *state.orientation[:3]  # Use only xyz of quaternion
                ])
                
                # Apply Kalman filter
                filtered_vector = self._kalman_filter.update(state_vector)
                
                # Convert back to state
                state.position = tuple(filtered_vector[0:3])
                state.linear_velocity = tuple(filtered_vector[3:6])
                state.linear_acceleration = tuple(filtered_vector[6:9])
                state.orientation = (*filtered_vector[9:12], state.orientation[3])  # Keep w component
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error applying Kalman filter: {e}")
            return state
    
    def _apply_smoothing(self, state: RobotState) -> RobotState:
        """Apply smoothing to state estimate."""
        try:
            if len(self._fusion_buffer) > 1:
                # Simple exponential smoothing
                alpha = 0.7  # Smoothing factor
                
                previous_state, _ = self._fusion_buffer[-1]
                
                # Smooth position
                state.position = tuple(
                    alpha * state.position[i] + (1 - alpha) * previous_state.position[i]
                    for i in range(3)
                )
                
                # Smooth velocity
                state.linear_velocity = tuple(
                    alpha * state.linear_velocity[i] + (1 - alpha) * previous_state.linear_velocity[i]
                    for i in range(3)
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error applying smoothing: {e}")
            return state
    
    def _predict_state(self, current_state: RobotState, dt: float) -> RobotState:
        """Predict future state."""
        try:
            predicted_state = RobotState()
            
            # Simple kinematic prediction
            predicted_state.position = tuple(
                current_state.position[i] + current_state.linear_velocity[i] * dt + 
                0.5 * current_state.linear_acceleration[i] * dt * dt
                for i in range(3)
            )
            
            predicted_state.linear_velocity = tuple(
                current_state.linear_velocity[i] + current_state.linear_acceleration[i] * dt
                for i in range(3)
            )
            
            predicted_state.linear_acceleration = current_state.linear_acceleration
            predicted_state.orientation = current_state.orientation
            predicted_state.angular_velocity = current_state.angular_velocity
            
            predicted_state.timestamp = current_state.timestamp + dt
            predicted_state.confidence = current_state.confidence * 0.95  # Decrease confidence over time
            
            return predicted_state
            
        except Exception as e:
            self.logger.error(f"Error predicting state: {e}")
            return current_state
    
    async def _process_calibration_data(self, calibration_data: Dict[str, List[SensorData]]) -> None:
        """Process sensor calibration data."""
        try:
            for sensor_id, data_list in calibration_data.items():
                if not data_list:
                    continue
                
                sensor_type = self._sensors[sensor_id]['type']
                
                if sensor_type == SensorType.IMU:
                    # Calculate IMU bias
                    acc_sum = np.array([0.0, 0.0, 0.0])
                    gyro_sum = np.array([0.0, 0.0, 0.0])
                    
                    for data in data_list:
                        imu_data = data.data
                        acc_sum += np.array(imu_data['acceleration'])
                        gyro_sum += np.array(imu_data['angular_velocity'])
                    
                    acc_bias = acc_sum / len(data_list)
                    gyro_bias = gyro_sum / len(data_list)
                    
                    # Store calibration parameters
                    self._sensors[sensor_id]['calibration'] = {
                        'acc_bias': acc_bias.tolist(),
                        'gyro_bias': gyro_bias.tolist()
                    }
                    
                    self.logger.info(f"IMU calibration completed for {sensor_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing calibration data: {e}")
    
    def _check_sensor_health(self) -> None:
        """Check sensor health status."""
        try:
            current_time = time.time()
            
            for sensor_id, sensor_info in self._sensors.items():
                last_update = sensor_info['last_update']
                
                # Check if sensor is active
                if current_time - last_update > 1.0:  # 1 second timeout
                    if self._sensor_states[sensor_id] == SensorState.ACTIVE:
                        self._sensor_states[sensor_id] = SensorState.ERROR
                        self.logger.warning(f"Sensor {sensor_id} timeout")
                else:
                    if self._sensor_states[sensor_id] == SensorState.ERROR:
                        self._sensor_states[sensor_id] = SensorState.ACTIVE
                        self.logger.info(f"Sensor {sensor_id} recovered")
        
        except Exception as e:
            self.logger.error(f"Error checking sensor health: {e}")
    
    def _update_system_health(self) -> None:
        """Update overall system health."""
        try:
            active_sensors = sum(1 for state in self._sensor_states.values() if state == SensorState.ACTIVE)
            total_sensors = len(self._sensor_states)
            
            if total_sensors > 0:
                self._stats.system_health = active_sensors / total_sensors
            else:
                self._stats.system_health = 0.0
            
            # Update current state health
            self._current_state.system_health = self._stats.system_health
        
        except Exception as e:
            self.logger.error(f"Error updating system health: {e}")
    
    def _update_statistics(self) -> None:
        """Update fusion statistics."""
        try:
            current_time = time.time()
            
            # Calculate fusion rate
            if self._update_times:
                recent_updates = [t for t in self._update_times if current_time - t < 1.0]
                self._stats.fusion_rate = len(recent_updates)
                
                # Calculate average latency
                if len(recent_updates) > 1:
                    intervals = [recent_updates[i] - recent_updates[i-1] for i in range(1, len(recent_updates))]
                    self._stats.average_latency = sum(intervals) / len(intervals)
            
            self._last_stats_update = current_time
        
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _set_state(self, new_state: FusionState) -> None:
        """Set fusion state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.logger.info(f"Fusion state changed: {old_state.value} -> {new_state.value}")