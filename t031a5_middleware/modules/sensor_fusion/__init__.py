"""Sensor Fusion module for t031a5_middleware.

This module provides sensor data aggregation, fusion, and processing capabilities
for the Unitree G1 robot, integrating multiple sensor inputs including IMU,
lidar, cameras, and other sensors for enhanced perception and navigation.
"""

from .manager import (
    SensorFusion,
    SensorType,
    SensorState,
    SensorData,
    FusionConfig,
    FusionStats
)

from .filters import (
    KalmanFilter,
    ParticleFilter,
    ComplementaryFilter,
    FilterType
)

from .processors import (
    IMUProcessor,
    LidarProcessor,
    VisionProcessor,
    OdometryProcessor
)

__all__ = [
    # Main classes
    'SensorFusion',
    'SensorType',
    'SensorState',
    'SensorData',
    'FusionConfig',
    'FusionStats',
    
    # Filters
    'KalmanFilter',
    'ParticleFilter',
    'ComplementaryFilter',
    'FilterType',
    
    # Processors
    'IMUProcessor',
    'LidarProcessor',
    'VisionProcessor',
    'OdometryProcessor'
]

__version__ = '1.0.0'
__author__ = 't031a5_middleware'
__description__ = 'Sensor fusion and data processing for Unitree G1 robot'