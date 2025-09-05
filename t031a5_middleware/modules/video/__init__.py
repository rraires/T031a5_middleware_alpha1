"""Video module for t031a5_middleware.

This module provides video capture, streaming, and processing capabilities
for the Unitree G1 robot, including integration with the Unitree SDK.
"""

from .manager import VideoManager
from .capture import VideoCapture
from .streaming import VideoStreamer
from .processing import VideoProcessor

__all__ = [
    'VideoManager',
    'Video