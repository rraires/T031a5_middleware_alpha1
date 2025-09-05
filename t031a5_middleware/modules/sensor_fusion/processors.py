"""Sensor Processors for t031a5_middleware.

Implements specialized processors for different sensor types including
IMU, Lidar, Vision, and Odometry data processing.
"""

import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time
import math
from scipy.spatial.transform import Rotation
from scipy.signal import butter, filtfilt
import cv2


@dataclass
class ProcessedSensorData:
    """Processed sensor data container."""
    timestamp: float
    sensor_type: str
    data: np.ndarray
    quality: float
    confidence: float
    metadata: Dict[str, Any]


class SensorProcessor(ABC):
    """Base class for sensor processors."""
    
    def __init__(self, sensor_type: str):
        self.sensor_type = sensor_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{sensor_type}")
        self.initialized = False
        self.calibration_data = {}
        self.processing_stats = {
            'processed_count': 0,
            'error_count': 0,
            'average_processing_time': 0.0,
            'last_processing_time': 0.0
        }
    
    @abstractmethod
    def process(self, raw_data: Any, timestamp: float) -> Optional[ProcessedSensorData]:
        """Process raw sensor data."""
        pass
    
    @abstractmethod
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate sensor processor."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            'processed_count': 0,
            'error_count': 0,
            'average_processing_time': 0.0,
            'last_processing_time': 0.0
        }
    
    def _update_stats(self, processing_time: float, success: bool) -> None:
        """Update processing statistics."""
        self.processing_stats['last_processing_time'] = processing_time
        
        if success:
            self.processing_stats['processed_count'] += 1
            # Update average processing time
            count = self.processing_stats['processed_count']
            avg = self.processing_stats['average_processing_time']
            self.processing_stats['average_processing_time'] = (
                (avg * (count - 1) + processing_time) / count
            )
        else:
            self.processing_stats['error_count'] += 1


class IMUProcessor(SensorProcessor):
    """IMU sensor data processor.
    
    Processes accelerometer, gyroscope, and magnetometer data
    with calibration, filtering, and orientation estimation.
    """
    
    def __init__(self):
        super().__init__("imu")
        
        # Calibration parameters
        self.accel_bias = np.zeros(3)
        self.accel_scale = np.ones(3)
        self.gyro_bias = np.zeros(3)
        self.gyro_scale = np.ones(3)
        self.mag_bias = np.zeros(3)
        self.mag_scale = np.ones(3)
        
        # Filter parameters
        self.filter_order = 4
        self.cutoff_freq = 50.0  # Hz
        self.sample_rate = 200.0  # Hz
        
        # Create low-pass filter
        nyquist = self.sample_rate / 2
        normal_cutoff = self.cutoff_freq / nyquist
        self.filter_b, self.filter_a = butter(self.filter_order, normal_cutoff, btype='low')
        
        # Data buffers for filtering
        self.accel_buffer = []
        self.gyro_buffer = []
        self.mag_buffer = []
        self.buffer_size = 10
        
        # Orientation estimation
        self.orientation = np.array([0.0, 0.0, 0.0])  # roll, pitch, yaw
        self.angular_velocity = np.array([0.0, 0.0, 0.0])
        
        # Quality assessment
        self.gravity_magnitude = 9.81
        self.gravity_tolerance = 0.5
        
        self.initialized = True
        self.logger.info("IMU processor initialized")
    
    def process(self, raw_data: Dict[str, np.ndarray], timestamp: float) -> Optional[ProcessedSensorData]:
        """Process IMU data.
        
        Args:
            raw_data: Dictionary with 'accelerometer', 'gyroscope', 'magnetometer' keys
            timestamp: Data timestamp
        
        Returns:
            Processed IMU data or None if processing failed
        """
        start_time = time.time()
        
        try:
            if not self.initialized:
                return None
            
            # Extract sensor data
            accel = raw_data.get('accelerometer', np.zeros(3))
            gyro = raw_data.get('gyroscope', np.zeros(3))
            mag = raw_data.get('magnetometer', np.zeros(3))
            
            # Apply calibration
            accel_cal = self._calibrate_accelerometer(accel)
            gyro_cal = self._calibrate_gyroscope(gyro)
            mag_cal = self._calibrate_magnetometer(mag)
            
            # Apply filtering
            accel_filtered = self._apply_filter(accel_cal, self.accel_buffer)
            gyro_filtered = self._apply_filter(gyro_cal, self.gyro_buffer)
            mag_filtered = self._apply_filter(mag_cal, self.mag_buffer)
            
            # Update orientation estimate
            self._update_orientation(accel_filtered, gyro_filtered, mag_filtered, timestamp)
            
            # Assess data quality
            quality = self._assess_quality(accel_filtered, gyro_filtered, mag_filtered)
            
            # Calculate confidence
            confidence = self._calculate_confidence(accel_filtered, gyro_filtered)
            
            # Combine processed data
            processed_data = np.concatenate([
                accel_filtered,
                gyro_filtered,
                mag_filtered,
                self.orientation,
                self.angular_velocity
            ])
            
            # Create metadata
            metadata = {
                'accelerometer_raw': accel,
                'gyroscope_raw': gyro,
                'magnetometer_raw': mag,
                'orientation_euler': self.orientation,
                'angular_velocity': self.angular_velocity,
                'gravity_magnitude': np.linalg.norm(accel_filtered)
            }
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return ProcessedSensorData(
                timestamp=timestamp,
                sensor_type=self.sensor_type,
                data=processed_data,
                quality=quality,
                confidence=confidence,
                metadata=metadata
            )
        
        except Exception as e:
            self.logger.error(f"Error processing IMU data: {e}")
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            return None
    
    def _calibrate_accelerometer(self, accel: np.ndarray) -> np.ndarray:
        """Apply accelerometer calibration."""
        return (accel - self.accel_bias) * self.accel_scale
    
    def _calibrate_gyroscope(self, gyro: np.ndarray) -> np.ndarray:
        """Apply gyroscope calibration."""
        return (gyro - self.gyro_bias) * self.gyro_scale
    
    def _calibrate_magnetometer(self, mag: np.ndarray) -> np.ndarray:
        """Apply magnetometer calibration."""
        return (mag - self.mag_bias) * self.mag_scale
    
    def _apply_filter(self, data: np.ndarray, buffer: List[np.ndarray]) -> np.ndarray:
        """Apply low-pass filter to sensor data."""
        # Add to buffer
        buffer.append(data.copy())
        if len(buffer) > self.buffer_size:
            buffer.pop(0)
        
        # Apply filter if enough data
        if len(buffer) >= self.filter_order + 1:
            buffer_array = np.array(buffer)
            filtered = np.zeros_like(data)
            
            for i in range(3):  # x, y, z components
                filtered[i] = filtfilt(self.filter_b, self.filter_a, buffer_array[:, i])[-1]
            
            return filtered
        else:
            return data
    
    def _update_orientation(self, accel: np.ndarray, gyro: np.ndarray, 
                          mag: np.ndarray, timestamp: float) -> None:
        """Update orientation estimate using sensor fusion."""
        try:
            # Store angular velocity
            self.angular_velocity = gyro.copy()
            
            # Calculate orientation from accelerometer
            accel_norm = np.linalg.norm(accel)
            if accel_norm > 0:
                accel_normalized = accel / accel_norm
                
                # Calculate roll and pitch
                roll = math.atan2(accel_normalized[1], accel_normalized[2])
                pitch = math.atan2(-accel_normalized[0], 
                                 math.sqrt(accel_normalized[1]**2 + accel_normalized[2]**2))
                
                # Calculate yaw from magnetometer if available
                mag_norm = np.linalg.norm(mag)
                if mag_norm > 0:
                    mag_normalized = mag / mag_norm
                    
                    # Tilt compensation for magnetometer
                    mag_x = (mag_normalized[0] * math.cos(pitch) + 
                            mag_normalized[2] * math.sin(pitch))
                    mag_y = (mag_normalized[0] * math.sin(roll) * math.sin(pitch) + 
                            mag_normalized[1] * math.cos(roll) - 
                            mag_normalized[2] * math.sin(roll) * math.cos(pitch))
                    
                    yaw = math.atan2(-mag_y, mag_x)
                else:
                    yaw = self.orientation[2]  # Keep previous yaw
                
                # Update orientation with complementary filter
                alpha = 0.98  # Weight for gyroscope integration
                
                if hasattr(self, 'last_timestamp'):
                    dt = timestamp - self.last_timestamp
                    if dt > 0 and dt < 1.0:  # Reasonable time step
                        # Integrate gyroscope
                        gyro_orientation = self.orientation + gyro * dt
                        
                        # Combine with accelerometer/magnetometer
                        accel_mag_orientation = np.array([roll, pitch, yaw])
                        
                        self.orientation = (alpha * gyro_orientation + 
                                          (1 - alpha) * accel_mag_orientation)
                    else:
                        self.orientation = np.array([roll, pitch, yaw])
                else:
                    self.orientation = np.array([roll, pitch, yaw])
                
                self.last_timestamp = timestamp
                
                # Wrap angles to [-pi, pi]
                self.orientation = np.arctan2(np.sin(self.orientation), np.cos(self.orientation))
        
        except Exception as e:
            self.logger.error(f"Error updating orientation: {e}")
    
    def _assess_quality(self, accel: np.ndarray, gyro: np.ndarray, mag: np.ndarray) -> float:
        """Assess IMU data quality."""
        try:
            quality = 1.0
            
            # Check accelerometer magnitude (should be close to gravity)
            accel_magnitude = np.linalg.norm(accel)
            gravity_error = abs(accel_magnitude - self.gravity_magnitude)
            if gravity_error > self.gravity_tolerance:
                quality *= max(0.1, 1.0 - gravity_error / self.gravity_magnitude)
            
            # Check for excessive angular velocity
            gyro_magnitude = np.linalg.norm(gyro)
            if gyro_magnitude > 10.0:  # rad/s
                quality *= max(0.1, 1.0 - (gyro_magnitude - 10.0) / 10.0)
            
            # Check magnetometer magnitude consistency
            mag_magnitude = np.linalg.norm(mag)
            if mag_magnitude > 0:
                # Typical Earth's magnetic field: 25-65 µT
                expected_mag = 50.0  # µT
                mag_error = abs(mag_magnitude - expected_mag) / expected_mag
                if mag_error > 0.5:
                    quality *= max(0.5, 1.0 - mag_error)
            
            return max(0.0, min(1.0, quality))
        
        except Exception as e:
            self.logger.error(f"Error assessing IMU quality: {e}")
            return 0.5
    
    def _calculate_confidence(self, accel: np.ndarray, gyro: np.ndarray) -> float:
        """Calculate confidence in IMU measurements."""
        try:
            # Base confidence on data consistency and noise levels
            confidence = 1.0
            
            # Check accelerometer noise
            if hasattr(self, 'accel_buffer') and len(self.accel_buffer) > 1:
                accel_variance = np.var(self.accel_buffer, axis=0)
                accel_noise = np.mean(accel_variance)
                if accel_noise > 0.1:
                    confidence *= max(0.3, 1.0 - accel_noise)
            
            # Check gyroscope stability
            if hasattr(self, 'gyro_buffer') and len(self.gyro_buffer) > 1:
                gyro_variance = np.var(self.gyro_buffer, axis=0)
                gyro_noise = np.mean(gyro_variance)
                if gyro_noise > 0.05:
                    confidence *= max(0.3, 1.0 - gyro_noise * 10)
            
            return max(0.0, min(1.0, confidence))
        
        except Exception as e:
            self.logger.error(f"Error calculating IMU confidence: {e}")
            return 0.5
    
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate IMU processor."""
        try:
            if 'accelerometer' in calibration_data:
                accel_cal = calibration_data['accelerometer']
                self.accel_bias = np.array(accel_cal.get('bias', [0, 0, 0]))
                self.accel_scale = np.array(accel_cal.get('scale', [1, 1, 1]))
            
            if 'gyroscope' in calibration_data:
                gyro_cal = calibration_data['gyroscope']
                self.gyro_bias = np.array(gyro_cal.get('bias', [0, 0, 0]))
                self.gyro_scale = np.array(gyro_cal.get('scale', [1, 1, 1]))
            
            if 'magnetometer' in calibration_data:
                mag_cal = calibration_data['magnetometer']
                self.mag_bias = np.array(mag_cal.get('bias', [0, 0, 0]))
                self.mag_scale = np.array(mag_cal.get('scale', [1, 1, 1]))
            
            self.calibration_data = calibration_data
            self.logger.info("IMU calibration updated")
            return True
        
        except Exception as e:
            self.logger.error(f"Error calibrating IMU: {e}")
            return False


class LidarProcessor(SensorProcessor):
    """Lidar sensor data processor.
    
    Processes point cloud data with filtering, ground detection,
    and obstacle identification.
    """
    
    def __init__(self):
        super().__init__("lidar")
        
        # Processing parameters
        self.max_range = 30.0  # meters
        self.min_range = 0.1   # meters
        self.ground_threshold = 0.1  # meters
        self.cluster_tolerance = 0.5  # meters
        self.min_cluster_size = 10
        self.max_cluster_size = 10000
        
        # Filtering parameters
        self.voxel_size = 0.05  # meters
        self.statistical_neighbors = 20
        self.statistical_std_ratio = 2.0
        
        # Ground plane parameters
        self.ground_plane_normal = np.array([0, 0, 1])
        self.ground_plane_distance = 0.0
        
        self.initialized = True
        self.logger.info("Lidar processor initialized")
    
    def process(self, raw_data: np.ndarray, timestamp: float) -> Optional[ProcessedSensorData]:
        """Process Lidar point cloud data.
        
        Args:
            raw_data: Point cloud as Nx3 or Nx4 array (x, y, z, [intensity])
            timestamp: Data timestamp
        
        Returns:
            Processed Lidar data or None if processing failed
        """
        start_time = time.time()
        
        try:
            if not self.initialized or raw_data is None or len(raw_data) == 0:
                return None
            
            # Ensure we have at least x, y, z coordinates
            if raw_data.shape[1] < 3:
                self.logger.error(f"Invalid point cloud shape: {raw_data.shape}")
                return None
            
            points = raw_data[:, :3]  # x, y, z
            intensities = raw_data[:, 3] if raw_data.shape[1] > 3 else None
            
            # Range filtering
            points_filtered = self._range_filter(points)
            
            # Voxel downsampling
            points_downsampled = self._voxel_downsample(points_filtered)
            
            # Statistical outlier removal
            points_clean = self._statistical_outlier_removal(points_downsampled)
            
            # Ground plane detection and removal
            ground_points, obstacle_points = self._ground_segmentation(points_clean)
            
            # Obstacle clustering
            clusters = self._cluster_obstacles(obstacle_points)
            
            # Calculate quality metrics
            quality = self._assess_quality(points_clean, ground_points, obstacle_points)
            
            # Calculate confidence
            confidence = self._calculate_confidence(points_clean)
            
            # Prepare processed data
            processed_data = {
                'points': points_clean,
                'ground_points': ground_points,
                'obstacle_points': obstacle_points,
                'clusters': clusters,
                'point_count': len(points_clean)
            }
            
            # Create metadata
            metadata = {
                'original_point_count': len(points),
                'filtered_point_count': len(points_clean),
                'ground_point_count': len(ground_points),
                'obstacle_point_count': len(obstacle_points),
                'cluster_count': len(clusters),
                'max_range': self.max_range,
                'min_range': self.min_range,
                'voxel_size': self.voxel_size
            }
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return ProcessedSensorData(
                timestamp=timestamp,
                sensor_type=self.sensor_type,
                data=processed_data,
                quality=quality,
                confidence=confidence,
                metadata=metadata
            )
        
        except Exception as e:
            self.logger.error(f"Error processing Lidar data: {e}")
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            return None
    
    def _range_filter(self, points: np.ndarray) -> np.ndarray:
        """Filter points by range."""
        distances = np.linalg.norm(points, axis=1)
        mask = (distances >= self.min_range) & (distances <= self.max_range)
        return points[mask]
    
    def _voxel_downsample(self, points: np.ndarray) -> np.ndarray:
        """Downsample point cloud using voxel grid."""
        if len(points) == 0:
            return points
        
        # Simple voxel downsampling
        voxel_coords = np.floor(points / self.voxel_size).astype(int)
        
        # Find unique voxels
        unique_voxels, indices = np.unique(voxel_coords, axis=0, return_inverse=True)
        
        # Average points in each voxel
        downsampled_points = []
        for i in range(len(unique_voxels)):
            voxel_mask = indices == i
            voxel_points = points[voxel_mask]
            centroid = np.mean(voxel_points, axis=0)
            downsampled_points.append(centroid)
        
        return np.array(downsampled_points)
    
    def _statistical_outlier_removal(self, points: np.ndarray) -> np.ndarray:
        """Remove statistical outliers."""
        if len(points) < self.statistical_neighbors:
            return points
        
        # Calculate distances to k nearest neighbors
        from scipy.spatial.distance import cdist
        
        distances = cdist(points, points)
        
        # For each point, find mean distance to k nearest neighbors
        mean_distances = []
        for i in range(len(points)):
            # Sort distances and take k nearest (excluding self)
            sorted_distances = np.sort(distances[i])[1:self.statistical_neighbors+1]
            mean_distances.append(np.mean(sorted_distances))
        
        mean_distances = np.array(mean_distances)
        
        # Calculate threshold
        global_mean = np.mean(mean_distances)
        global_std = np.std(mean_distances)
        threshold = global_mean + self.statistical_std_ratio * global_std
        
        # Filter outliers
        mask = mean_distances < threshold
        return points[mask]
    
    def _ground_segmentation(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Segment ground plane from point cloud."""
        if len(points) == 0:
            return np.array([]), np.array([])
        
        # Simple ground segmentation based on z-coordinate
        z_coords = points[:, 2]
        ground_mask = np.abs(z_coords - np.min(z_coords)) < self.ground_threshold
        
        ground_points = points[ground_mask]
        obstacle_points = points[~ground_mask]
        
        return ground_points, obstacle_points
    
    def _cluster_obstacles(self, points: np.ndarray) -> List[np.ndarray]:
        """Cluster obstacle points."""
        if len(points) == 0:
            return []
        
        # Simple clustering based on spatial proximity
        from scipy.spatial.distance import pdist, squareform
        from scipy.cluster.hierarchy import fcluster, linkage
        
        try:
            # Calculate pairwise distances
            if len(points) > 1000:  # Subsample for large point clouds
                indices = np.random.choice(len(points), 1000, replace=False)
                sample_points = points[indices]
            else:
                sample_points = points
                indices = np.arange(len(points))
            
            if len(sample_points) < 2:
                return [points]
            
            # Hierarchical clustering
            distances = pdist(sample_points)
            linkage_matrix = linkage(distances, method='ward')
            cluster_labels = fcluster(linkage_matrix, self.cluster_tolerance, criterion='distance')
            
            # Group points by cluster
            clusters = []
            for cluster_id in np.unique(cluster_labels):
                cluster_mask = cluster_labels == cluster_id
                cluster_indices = indices[cluster_mask]
                cluster_points = points[cluster_indices]
                
                if self.min_cluster_size <= len(cluster_points) <= self.max_cluster_size:
                    clusters.append(cluster_points)
            
            return clusters
        
        except Exception as e:
            self.logger.error(f"Error clustering obstacles: {e}")
            return [points]
    
    def _assess_quality(self, points: np.ndarray, ground_points: np.ndarray, 
                      obstacle_points: np.ndarray) -> float:
        """Assess Lidar data quality."""
        try:
            if len(points) == 0:
                return 0.0
            
            quality = 1.0
            
            # Point density quality
            expected_points = 10000  # Expected number of points
            density_ratio = len(points) / expected_points
            if density_ratio < 0.5:
                quality *= density_ratio * 2
            elif density_ratio > 2.0:
                quality *= max(0.5, 2.0 / density_ratio)
            
            # Ground detection quality
            if len(points) > 0:
                ground_ratio = len(ground_points) / len(points)
                if ground_ratio < 0.1 or ground_ratio > 0.8:
                    quality *= 0.8
            
            # Range distribution quality
            if len(points) > 0:
                distances = np.linalg.norm(points, axis=1)
                range_std = np.std(distances)
                if range_std < 1.0:  # Too uniform
                    quality *= 0.9
            
            return max(0.0, min(1.0, quality))
        
        except Exception as e:
            self.logger.error(f"Error assessing Lidar quality: {e}")
            return 0.5
    
    def _calculate_confidence(self, points: np.ndarray) -> float:
        """Calculate confidence in Lidar measurements."""
        try:
            if len(points) == 0:
                return 0.0
            
            # Base confidence on point cloud characteristics
            confidence = 1.0
            
            # Point count confidence
            min_points = 1000
            if len(points) < min_points:
                confidence *= len(points) / min_points
            
            # Spatial distribution confidence
            if len(points) > 10:
                # Check if points are well distributed
                centroid = np.mean(points, axis=0)
                distances_to_centroid = np.linalg.norm(points - centroid, axis=1)
                distribution_std = np.std(distances_to_centroid)
                
                if distribution_std < 0.5:  # Too clustered
                    confidence *= 0.8
                elif distribution_std > 10.0:  # Too spread out
                    confidence *= 0.8
            
            return max(0.0, min(1.0, confidence))
        
        except Exception as e:
            self.logger.error(f"Error calculating Lidar confidence: {e}")
            return 0.5
    
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate Lidar processor."""
        try:
            if 'max_range' in calibration_data:
                self.max_range = calibration_data['max_range']
            
            if 'min_range' in calibration_data:
                self.min_range = calibration_data['min_range']
            
            if 'ground_threshold' in calibration_data:
                self.ground_threshold = calibration_data['ground_threshold']
            
            if 'voxel_size' in calibration_data:
                self.voxel_size = calibration_data['voxel_size']
            
            self.calibration_data = calibration_data
            self.logger.info("Lidar calibration updated")
            return True
        
        except Exception as e:
            self.logger.error(f"Error calibrating Lidar: {e}")
            return False


class VisionProcessor(SensorProcessor):
    """Vision sensor data processor.
    
    Processes camera images with feature detection, tracking,
    and visual odometry estimation.
    """
    
    def __init__(self):
        super().__init__("vision")
        
        # Feature detection parameters
        self.feature_detector = cv2.ORB_create(nfeatures=1000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Tracking parameters
        self.max_features = 1000
        self.quality_level = 0.01
        self.min_distance = 10
        self.track_length = 10
        
        # Visual odometry
        self.prev_frame = None
        self.prev_keypoints = None
        self.prev_descriptors = None
        self.trajectory = []
        
        # Camera parameters (should be calibrated)
        self.camera_matrix = np.eye(3)
        self.dist_coeffs = np.zeros(5)
        
        self.initialized = True
        self.logger.info("Vision processor initialized")
    
    def process(self, raw_data: np.ndarray, timestamp: float) -> Optional[ProcessedSensorData]:
        """Process camera image data.
        
        Args:
            raw_data: Image as numpy array (H, W, C) or (H, W)
            timestamp: Data timestamp
        
        Returns:
            Processed vision data or None if processing failed
        """
        start_time = time.time()
        
        try:
            if not self.initialized or raw_data is None:
                return None
            
            # Convert to grayscale if needed
            if len(raw_data.shape) == 3:
                gray = cv2.cvtColor(raw_data, cv2.COLOR_BGR2GRAY)
            else:
                gray = raw_data
            
            # Detect features
            keypoints, descriptors = self.feature_detector.detectAndCompute(gray, None)
            
            # Track features and estimate motion
            motion_estimate = self._estimate_motion(gray, keypoints, descriptors)
            
            # Calculate quality metrics
            quality = self._assess_quality(gray, keypoints)
            
            # Calculate confidence
            confidence = self._calculate_confidence(keypoints, motion_estimate)
            
            # Prepare processed data
            processed_data = {
                'image': gray,
                'keypoints': keypoints,
                'descriptors': descriptors,
                'motion_estimate': motion_estimate,
                'feature_count': len(keypoints)
            }
            
            # Create metadata
            metadata = {
                'image_shape': gray.shape,
                'feature_count': len(keypoints),
                'motion_estimate': motion_estimate,
                'trajectory_length': len(self.trajectory)
            }
            
            # Update previous frame data
            self.prev_frame = gray.copy()
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return ProcessedSensorData(
                timestamp=timestamp,
                sensor_type=self.sensor_type,
                data=processed_data,
                quality=quality,
                confidence=confidence,
                metadata=metadata
            )
        
        except Exception as e:
            self.logger.error(f"Error processing vision data: {e}")
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            return None
    
    def _estimate_motion(self, frame: np.ndarray, keypoints: List, 
                        descriptors: np.ndarray) -> Dict[str, Any]:
        """Estimate camera motion using visual odometry."""
        motion_estimate = {
            'translation': np.zeros(3),
            'rotation': np.zeros(3),
            'scale': 1.0,
            'matches': 0
        }
        
        try:
            if (self.prev_frame is None or self.prev_keypoints is None or 
                self.prev_descriptors is None or descriptors is None):
                return motion_estimate
            
            # Match features between frames
            matches = self.matcher.match(self.prev_descriptors, descriptors)
            matches = sorted(matches, key=lambda x: x.distance)
            
            if len(matches) < 10:
                return motion_estimate
            
            # Extract matched points
            prev_pts = np.float32([self.prev_keypoints[m.queryIdx].pt for m in matches])
            curr_pts = np.float32([keypoints[m.trainIdx].pt for m in matches])
            
            # Estimate fundamental matrix
            F, mask = cv2.findFundamentalMat(prev_pts, curr_pts, cv2.FM_RANSAC)
            
            if F is not None and mask is not None:
                # Filter matches using fundamental matrix
                good_matches = mask.ravel() == 1
                prev_pts_filtered = prev_pts[good_matches]
                curr_pts_filtered = curr_pts[good_matches]
                
                if len(prev_pts_filtered) > 8:
                    # Estimate essential matrix
                    E, _ = cv2.findEssentialMat(prev_pts_filtered, curr_pts_filtered, 
                                              self.camera_matrix)
                    
                    if E is not None:
                        # Recover pose
                        _, R, t, _ = cv2.recoverPose(E, prev_pts_filtered, curr_pts_filtered, 
                                                   self.camera_matrix)
                        
                        # Convert rotation matrix to Euler angles
                        rotation = Rotation.from_matrix(R).as_euler('xyz')
                        
                        motion_estimate = {
                            'translation': t.flatten(),
                            'rotation': rotation,
                            'scale': np.linalg.norm(t),
                            'matches': len(prev_pts_filtered)
                        }
                        
                        # Add to trajectory
                        self.trajectory.append({
                            'translation': t.flatten(),
                            'rotation': rotation,
                            'timestamp': time.time()
                        })
                        
                        # Limit trajectory length
                        if len(self.trajectory) > 1000:
                            self.trajectory.pop(0)
            
            return motion_estimate
        
        except Exception as e:
            self.logger.error(f"Error estimating motion: {e}")
            return motion_estimate
    
    def _assess_quality(self, image: np.ndarray, keypoints: List) -> float:
        """Assess vision data quality."""
        try:
            quality = 1.0
            
            # Image quality assessment
            # Check brightness
            mean_brightness = np.mean(image)
            if mean_brightness < 50 or mean_brightness > 200:
                quality *= max(0.3, 1.0 - abs(mean_brightness - 127.5) / 127.5)
            
            # Check contrast
            contrast = np.std(image)
            if contrast < 20:
                quality *= max(0.5, contrast / 20)
            
            # Feature quality
            if len(keypoints) < 100:
                quality *= len(keypoints) / 100
            elif len(keypoints) > 2000:
                quality *= max(0.8, 2000 / len(keypoints))
            
            # Check feature distribution
            if len(keypoints) > 10:
                points = np.array([kp.pt for kp in keypoints])
                height, width = image.shape
                
                # Check if features are well distributed
                x_std = np.std(points[:, 0]) / width
                y_std = np.std(points[:, 1]) / height
                
                if x_std < 0.1 or y_std < 0.1:
                    quality *= 0.8  # Features too clustered
            
            return max(0.0, min(1.0, quality))
        
        except Exception as e:
            self.logger.error(f"Error assessing vision quality: {e}")
            return 0.5
    
    def _calculate_confidence(self, keypoints: List, motion_estimate: Dict[str, Any]) -> float:
        """Calculate confidence in vision measurements."""
        try:
            confidence = 1.0
            
            # Feature-based confidence
            if len(keypoints) < 50:
                confidence *= len(keypoints) / 50
            
            # Motion estimation confidence
            if motion_estimate['matches'] < 10:
                confidence *= motion_estimate['matches'] / 10
            
            # Scale consistency check
            if motion_estimate['scale'] > 10.0:  # Unrealistic motion
                confidence *= 0.3
            
            return max(0.0, min(1.0, confidence))
        
        except Exception as e:
            self.logger.error(f"Error calculating vision confidence: {e}")
            return 0.5
    
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate vision processor."""
        try:
            if 'camera_matrix' in calibration_data:
                self.camera_matrix = np.array(calibration_data['camera_matrix'])
            
            if 'dist_coeffs' in calibration_data:
                self.dist_coeffs = np.array(calibration_data['dist_coeffs'])
            
            if 'max_features' in calibration_data:
                self.max_features = calibration_data['max_features']
                self.feature_detector = cv2.ORB_create(nfeatures=self.max_features)
            
            self.calibration_data = calibration_data
            self.logger.info("Vision calibration updated")
            return True
        
        except Exception as e:
            self.logger.error(f"Error calibrating vision: {e}")
            return False


class OdometryProcessor(SensorProcessor):
    """Odometry sensor data processor.
    
    Processes wheel encoder and motor data to estimate robot motion.
    """
    
    def __init__(self):
        super().__init__("odometry")
        
        # Robot parameters
        self.wheel_radius = 0.1  # meters
        self.wheel_base = 0.5    # meters
        self.encoder_resolution = 1024  # ticks per revolution
        
        # State tracking
        self.position = np.array([0.0, 0.0, 0.0])  # x, y, theta
        self.velocity = np.array([0.0, 0.0, 0.0])  # vx, vy, omega
        
        # Previous encoder values
        self.prev_left_encoder = 0
        self.prev_right_encoder = 0
        self.prev_timestamp = None
        
        # Calibration parameters
        self.left_wheel_factor = 1.0
        self.right_wheel_factor = 1.0
        
        self.initialized = True
        self.logger.info("Odometry processor initialized")
    
    def process(self, raw_data: Dict[str, Any], timestamp: float) -> Optional[ProcessedSensorData]:
        """Process odometry data.
        
        Args:
            raw_data: Dictionary with encoder and motor data
            timestamp: Data timestamp
        
        Returns:
            Processed odometry data or None if processing failed
        """
        start_time = time.time()
        
        try:
            if not self.initialized:
                return None
            
            # Extract encoder data
            left_encoder = raw_data.get('left_encoder', 0)
            right_encoder = raw_data.get('right_encoder', 0)
            
            # Calculate motion if we have previous data
            if self.prev_timestamp is not None:
                dt = timestamp - self.prev_timestamp
                
                if dt > 0 and dt < 1.0:  # Reasonable time step
                    # Calculate encoder differences
                    left_diff = left_encoder - self.prev_left_encoder
                    right_diff = right_encoder - self.prev_right_encoder
                    
                    # Convert to distances
                    left_distance = self._encoder_to_distance(left_diff) * self.left_wheel_factor
                    right_distance = self._encoder_to_distance(right_diff) * self.right_wheel_factor
                    
                    # Calculate robot motion
                    linear_distance = (left_distance + right_distance) / 2.0
                    angular_distance = (right_distance - left_distance) / self.wheel_base
                    
                    # Update velocity
                    linear_velocity = linear_distance / dt
                    angular_velocity = angular_distance / dt
                    
                    # Update position
                    self.position[0] += linear_distance * math.cos(self.position[2])
                    self.position[1] += linear_distance * math.sin(self.position[2])
                    self.position[2] += angular_distance
                    
                    # Wrap angle
                    self.position[2] = math.atan2(math.sin(self.position[2]), math.cos(self.position[2]))
                    
                    # Update velocity
                    self.velocity[0] = linear_velocity * math.cos(self.position[2])
                    self.velocity[1] = linear_velocity * math.sin(self.position[2])
                    self.velocity[2] = angular_velocity
            
            # Update previous values
            self.prev_left_encoder = left_encoder
            self.prev_right_encoder = right_encoder
            self.prev_timestamp = timestamp
            
            # Calculate quality and confidence
            quality = self._assess_quality(raw_data)
            confidence = self._calculate_confidence(raw_data)
            
            # Prepare processed data
            processed_data = np.concatenate([self.position, self.velocity])
            
            # Create metadata
            metadata = {
                'position': self.position.copy(),
                'velocity': self.velocity.copy(),
                'left_encoder': left_encoder,
                'right_encoder': right_encoder,
                'wheel_radius': self.wheel_radius,
                'wheel_base': self.wheel_base
            }
            
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            return ProcessedSensorData(
                timestamp=timestamp,
                sensor_type=self.sensor_type,
                data=processed_data,
                quality=quality,
                confidence=confidence,
                metadata=metadata
            )
        
        except Exception as e:
            self.logger.error(f"Error processing odometry data: {e}")
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            return None
    
    def _encoder_to_distance(self, encoder_ticks: int) -> float:
        """Convert encoder ticks to distance."""
        revolutions = encoder_ticks / self.encoder_resolution
        distance = revolutions * 2 * math.pi * self.wheel_radius
        return distance
    
    def _assess_quality(self, raw_data: Dict[str, Any]) -> float:
        """Assess odometry data quality."""
        try:
            quality = 1.0
            
            # Check for reasonable encoder values
            left_encoder = raw_data.get('left_encoder', 0)
            right_encoder = raw_data.get('right_encoder', 0)
            
            # Check for encoder overflow/underflow
            max_encoder_value = 2**31 - 1
            if abs(left_encoder) > max_encoder_value or abs(right_encoder) > max_encoder_value:
                quality *= 0.1
            
            # Check for motor current/voltage if available
            if 'motor_current' in raw_data:
                motor_current = raw_data['motor_current']
                if isinstance(motor_current, (list, np.ndarray)):
                    max_current = max(abs(c) for c in motor_current)
                    if max_current > 10.0:  # Excessive current
                        quality *= 0.8
            
            return max(0.0, min(1.0, quality))
        
        except Exception as e:
            self.logger.error(f"Error assessing odometry quality: {e}")
            return 0.5
    
    def _calculate_confidence(self, raw_data: Dict[str, Any]) -> float:
        """Calculate confidence in odometry measurements."""
        try:
            confidence = 1.0
            
            # Check velocity consistency
            velocity_magnitude = np.linalg.norm(self.velocity[:2])
            if velocity_magnitude > 5.0:  # Unrealistic velocity
                confidence *= max(0.3, 5.0 / velocity_magnitude)
            
            # Check angular velocity
            if abs(self.velocity[2]) > 3.0:  # Unrealistic angular velocity
                confidence *= max(0.5, 3.0 / abs(self.velocity[2]))
            
            return max(0.0, min(1.0, confidence))
        
        except Exception as e:
            self.logger.error(f"Error calculating odometry confidence: {e}")
            return 0.5
    
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """Calibrate odometry processor."""
        try:
            if 'wheel_radius' in calibration_data:
                self.wheel_radius = calibration_data['wheel_radius']
            
            if 'wheel_base' in calibration_data:
                self.wheel_base = calibration_data['wheel_base']
            
            if 'encoder_resolution' in calibration_data:
                self.encoder_resolution = calibration_data['encoder_resolution']
            
            if 'left_wheel_factor' in calibration_data:
                self.left_wheel_factor = calibration_data['left_wheel_factor']
            
            if 'right_wheel_factor' in calibration_data:
                self.right_wheel_factor = calibration_data['right_wheel_factor']
            
            self.calibration_data = calibration_data
            self.logger.info("Odometry calibration updated")
            return True
        
        except Exception as e:
            self.logger.error(f"Error calibrating odometry: {e}")
            return False
    
    def reset_position(self, position: Optional[np.ndarray] = None) -> None:
        """Reset odometry position."""
        if position is not None and len(position) == 3:
            self.position = position.copy()
        else:
            self.position = np.array([0.0, 0.0, 0.0])
        
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.logger.info(f"Odometry position reset to {self.position}")
    
    def get_pose(self) -> Tuple[float, float, float]:
        """Get current pose (x, y, theta)."""
        return tuple(self.position)
    
    def get_velocity(self) -> Tuple[float, float, float]:
        """Get current velocity (vx, vy, omega)."""
        return tuple(self.velocity)