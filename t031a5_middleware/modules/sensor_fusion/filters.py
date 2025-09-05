"""Sensor Fusion Filters for t031a5_middleware.

Implements various filtering algorithms for sensor data fusion including
Kalman filters, particle filters, and complementary filters.
"""

import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
from scipy.linalg import cholesky, solve_triangular
from scipy.stats import multivariate_normal


class FilterBase(ABC):
    """Base class for all filters."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialized = False
    
    @abstractmethod
    def predict(self, dt: float) -> None:
        """Predict step."""
        pass
    
    @abstractmethod
    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Update step with measurement."""
        pass
    
    @abstractmethod
    def get_state(self) -> np.ndarray:
        """Get current state estimate."""
        pass
    
    @abstractmethod
    def get_covariance(self) -> np.ndarray:
        """Get current state covariance."""
        pass


class KalmanFilter(FilterBase):
    """Extended Kalman Filter for state estimation.
    
    Implements a multi-dimensional Kalman filter for robot state estimation
    including position, velocity, acceleration, and orientation.
    """
    
    def __init__(self, 
                 state_dim: int = 12,
                 measurement_dim: int = 6,
                 process_noise: float = 0.01,
                 measurement_noise: float = 0.1,
                 initial_uncertainty: float = 1.0):
        super().__init__()
        
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim
        
        # State vector [x, y, z, vx, vy, vz, ax, ay, az, roll, pitch, yaw]
        self.x = np.zeros(state_dim)
        
        # State covariance matrix
        self.P = np.eye(state_dim) * initial_uncertainty
        
        # Process noise covariance
        self.Q = np.eye(state_dim) * process_noise
        
        # Measurement noise covariance
        self.R = np.eye(measurement_dim) * measurement_noise
        
        # State transition matrix (will be updated based on dt)
        self.F = np.eye(state_dim)
        
        # Measurement matrix
        self.H = np.zeros((measurement_dim, state_dim))
        self._setup_measurement_matrix()
        
        # Control input matrix
        self.B = np.zeros((state_dim, 3))  # 3D acceleration input
        self._setup_control_matrix()
        
        self.initialized = True
        self.logger.info(f"Kalman filter initialized: state_dim={state_dim}, measurement_dim={measurement_dim}")
    
    def _setup_measurement_matrix(self) -> None:
        """Setup measurement matrix H."""
        # Assume we can directly measure position and orientation
        self.H[0, 0] = 1.0  # x position
        self.H[1, 1] = 1.0  # y position
        self.H[2, 2] = 1.0  # z position
        self.H[3, 9] = 1.0  # roll
        self.H[4, 10] = 1.0  # pitch
        self.H[5, 11] = 1.0  # yaw
    
    def _setup_control_matrix(self) -> None:
        """Setup control input matrix B."""
        # Control input affects acceleration
        self.B[6, 0] = 1.0  # ax
        self.B[7, 1] = 1.0  # ay
        self.B[8, 2] = 1.0  # az
    
    def _update_transition_matrix(self, dt: float) -> None:
        """Update state transition matrix based on time step."""
        # Position integration: x = x + vx*dt + 0.5*ax*dt^2
        self.F[0, 3] = dt  # x += vx * dt
        self.F[1, 4] = dt  # y += vy * dt
        self.F[2, 5] = dt  # z += vz * dt
        
        self.F[0, 6] = 0.5 * dt * dt  # x += 0.5 * ax * dt^2
        self.F[1, 7] = 0.5 * dt * dt  # y += 0.5 * ay * dt^2
        self.F[2, 8] = 0.5 * dt * dt  # z += 0.5 * az * dt^2
        
        # Velocity integration: vx = vx + ax*dt
        self.F[3, 6] = dt  # vx += ax * dt
        self.F[4, 7] = dt  # vy += ay * dt
        self.F[5, 8] = dt  # vz += az * dt
        
        # Orientation integration (simplified)
        self.F[9, 9] = 1.0   # roll
        self.F[10, 10] = 1.0  # pitch
        self.F[11, 11] = 1.0  # yaw
    
    def predict(self, dt: float, control_input: Optional[np.ndarray] = None) -> None:
        """Predict step of Kalman filter."""
        try:
            if not self.initialized:
                return
            
            # Update transition matrix
            self._update_transition_matrix(dt)
            
            # Predict state
            self.x = self.F @ self.x
            
            # Add control input if provided
            if control_input is not None:
                self.x += self.B @ control_input
            
            # Predict covariance
            self.P = self.F @ self.P @ self.F.T + self.Q
            
        except Exception as e:
            self.logger.error(f"Error in Kalman predict step: {e}")
    
    def update(self, measurement: np.ndarray, measurement_covariance: Optional[np.ndarray] = None) -> np.ndarray:
        """Update step of Kalman filter."""
        try:
            if not self.initialized:
                return self.x
            
            # Use provided measurement covariance or default
            R = measurement_covariance if measurement_covariance is not None else self.R
            
            # Innovation
            y = measurement - self.H @ self.x
            
            # Innovation covariance
            S = self.H @ self.P @ self.H.T + R
            
            # Kalman gain
            try:
                K = self.P @ self.H.T @ np.linalg.inv(S)
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if matrix is singular
                K = self.P @ self.H.T @ np.linalg.pinv(S)
            
            # Update state
            self.x = self.x + K @ y
            
            # Update covariance
            I_KH = np.eye(self.state_dim) - K @ self.H
            self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T
            
            return self.x
            
        except Exception as e:
            self.logger.error(f"Error in Kalman update step: {e}")
            return self.x
    
    def get_state(self) -> np.ndarray:
        """Get current state estimate."""
        return self.x.copy()
    
    def get_covariance(self) -> np.ndarray:
        """Get current state covariance."""
        return self.P.copy()
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get current position estimate."""
        return tuple(self.x[0:3])
    
    def get_velocity(self) -> Tuple[float, float, float]:
        """Get current velocity estimate."""
        return tuple(self.x[3:6])
    
    def get_acceleration(self) -> Tuple[float, float, float]:
        """Get current acceleration estimate."""
        return tuple(self.x[6:9])
    
    def get_orientation(self) -> Tuple[float, float, float]:
        """Get current orientation estimate (roll, pitch, yaw)."""
        return tuple(self.x[9:12])
    
    def set_state(self, state: np.ndarray) -> None:
        """Set current state."""
        if len(state) == self.state_dim:
            self.x = state.copy()
        else:
            self.logger.error(f"Invalid state dimension: {len(state)}, expected {self.state_dim}")
    
    def set_covariance(self, covariance: np.ndarray) -> None:
        """Set current covariance."""
        if covariance.shape == (self.state_dim, self.state_dim):
            self.P = covariance.copy()
        else:
            self.logger.error(f"Invalid covariance shape: {covariance.shape}, expected ({self.state_dim}, {self.state_dim})")
    
    def reset(self) -> None:
        """Reset filter to initial state."""
        self.x = np.zeros(self.state_dim)
        self.P = np.eye(self.state_dim)
        self.logger.info("Kalman filter reset")


@dataclass
class Particle:
    """Particle for particle filter."""
    state: np.ndarray
    weight: float = 1.0


class ParticleFilter(FilterBase):
    """Particle Filter for non-linear state estimation.
    
    Implements a particle filter for handling non-linear dynamics
    and non-Gaussian noise distributions.
    """
    
    def __init__(self,
                 state_dim: int = 6,
                 num_particles: int = 1000,
                 process_noise: float = 0.1,
                 measurement_noise: float = 0.1):
        super().__init__()
        
        self.state_dim = state_dim
        self.num_particles = num_particles
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        
        # Initialize particles
        self.particles: List[Particle] = []
        self._initialize_particles()
        
        # Effective sample size threshold for resampling
        self.ess_threshold = num_particles / 2
        
        self.initialized = True
        self.logger.info(f"Particle filter initialized: {num_particles} particles, state_dim={state_dim}")
    
    def _initialize_particles(self) -> None:
        """Initialize particles with random states."""
        for _ in range(self.num_particles):
            state = np.random.normal(0, 1, self.state_dim)
            weight = 1.0 / self.num_particles
            self.particles.append(Particle(state, weight))
    
    def predict(self, dt: float, control_input: Optional[np.ndarray] = None) -> None:
        """Predict step - propagate particles forward."""
        try:
            if not self.initialized:
                return
            
            for particle in self.particles:
                # Apply motion model with noise
                noise = np.random.normal(0, self.process_noise, self.state_dim)
                
                # Simple motion model: position += velocity * dt
                if self.state_dim >= 6:
                    # [x, y, z, vx, vy, vz]
                    particle.state[0:3] += particle.state[3:6] * dt + noise[0:3]
                    particle.state[3:6] += noise[3:6]
                else:
                    particle.state += noise
                
                # Add control input if provided
                if control_input is not None:
                    particle.state += control_input * dt
        
        except Exception as e:
            self.logger.error(f"Error in particle filter predict step: {e}")
    
    def update(self, measurement: np.ndarray, measurement_function: Optional[callable] = None) -> np.ndarray:
        """Update step - weight particles based on measurement."""
        try:
            if not self.initialized:
                return self.get_state()
            
            # Default measurement function (identity)
            if measurement_function is None:
                measurement_function = lambda x: x[:len(measurement)]
            
            # Update particle weights
            for particle in self.particles:
                # Predict measurement from particle state
                predicted_measurement = measurement_function(particle.state)
                
                # Calculate likelihood
                diff = measurement - predicted_measurement
                likelihood = multivariate_normal.pdf(
                    diff, 
                    mean=np.zeros(len(diff)), 
                    cov=np.eye(len(diff)) * self.measurement_noise
                )
                
                # Update weight
                particle.weight *= likelihood
            
            # Normalize weights
            total_weight = sum(p.weight for p in self.particles)
            if total_weight > 0:
                for particle in self.particles:
                    particle.weight /= total_weight
            else:
                # All weights are zero, reset to uniform
                for particle in self.particles:
                    particle.weight = 1.0 / self.num_particles
            
            # Check if resampling is needed
            ess = self._effective_sample_size()
            if ess < self.ess_threshold:
                self._resample()
            
            return self.get_state()
        
        except Exception as e:
            self.logger.error(f"Error in particle filter update step: {e}")
            return self.get_state()
    
    def _effective_sample_size(self) -> float:
        """Calculate effective sample size."""
        weights = np.array([p.weight for p in self.particles])
        return 1.0 / np.sum(weights ** 2)
    
    def _resample(self) -> None:
        """Resample particles based on weights."""
        try:
            weights = np.array([p.weight for p in self.particles])
            indices = np.random.choice(
                self.num_particles, 
                size=self.num_particles, 
                p=weights
            )
            
            # Create new particle set
            new_particles = []
            for idx in indices:
                new_state = self.particles[idx].state.copy()
                new_particles.append(Particle(new_state, 1.0 / self.num_particles))
            
            self.particles = new_particles
        
        except Exception as e:
            self.logger.error(f"Error in particle resampling: {e}")
    
    def get_state(self) -> np.ndarray:
        """Get weighted mean state estimate."""
        if not self.particles:
            return np.zeros(self.state_dim)
        
        weights = np.array([p.weight for p in self.particles])
        states = np.array([p.state for p in self.particles])
        
        return np.average(states, axis=0, weights=weights)
    
    def get_covariance(self) -> np.ndarray:
        """Get state covariance estimate."""
        if not self.particles:
            return np.eye(self.state_dim)
        
        mean_state = self.get_state()
        weights = np.array([p.weight for p in self.particles])
        
        covariance = np.zeros((self.state_dim, self.state_dim))
        for particle in self.particles:
            diff = particle.state - mean_state
            covariance += particle.weight * np.outer(diff, diff)
        
        return covariance
    
    def get_particles(self) -> List[Particle]:
        """Get all particles."""
        return self.particles.copy()
    
    def reset(self) -> None:
        """Reset filter to initial state."""
        self.particles.clear()
        self._initialize_particles()
        self.logger.info("Particle filter reset")


class ComplementaryFilter(FilterBase):
    """Complementary Filter for IMU sensor fusion.
    
    Combines accelerometer and gyroscope data to estimate orientation
    using a complementary filter approach.
    """
    
    def __init__(self, alpha: float = 0.98, beta: float = 0.1):
        super().__init__()
        
        self.alpha = alpha  # Weight for gyroscope (high-pass)
        self.beta = beta    # Weight for accelerometer (low-pass)
        
        # State: [roll, pitch, yaw] in radians
        self.orientation = np.array([0.0, 0.0, 0.0])
        self.angular_velocity = np.array([0.0, 0.0, 0.0])
        
        # Bias estimation
        self.gyro_bias = np.array([0.0, 0.0, 0.0])
        self.bias_estimation_enabled = True
        
        # Covariance (simplified)
        self.covariance = np.eye(3) * 0.1
        
        self.last_time = None
        self.initialized = True
        
        self.logger.info(f"Complementary filter initialized: alpha={alpha}, beta={beta}")
    
    def predict(self, dt: float) -> None:
        """Predict step using gyroscope integration."""
        try:
            if not self.initialized:
                return
            
            # Integrate angular velocity to get orientation change
            corrected_gyro = self.angular_velocity - self.gyro_bias
            self.orientation += corrected_gyro * dt
            
            # Wrap angles to [-pi, pi]
            self.orientation = self._wrap_angles(self.orientation)
            
        except Exception as e:
            self.logger.error(f"Error in complementary filter predict step: {e}")
    
    def update(self, 
               accelerometer: np.ndarray, 
               gyroscope: np.ndarray, 
               magnetometer: Optional[np.ndarray] = None,
               dt: Optional[float] = None) -> np.ndarray:
        """Update step using accelerometer and gyroscope data."""
        try:
            if not self.initialized:
                return self.orientation
            
            # Update angular velocity
            self.angular_velocity = gyroscope
            
            # Calculate orientation from accelerometer
            acc_norm = np.linalg.norm(accelerometer)
            if acc_norm > 0:
                # Normalize accelerometer
                acc_normalized = accelerometer / acc_norm
                
                # Calculate roll and pitch from accelerometer
                acc_roll = math.atan2(acc_normalized[1], acc_normalized[2])
                acc_pitch = math.atan2(-acc_normalized[0], 
                                     math.sqrt(acc_normalized[1]**2 + acc_normalized[2]**2))
                
                acc_orientation = np.array([acc_roll, acc_pitch, self.orientation[2]])
                
                # Use magnetometer for yaw if available
                if magnetometer is not None:
                    mag_norm = np.linalg.norm(magnetometer)
                    if mag_norm > 0:
                        mag_normalized = magnetometer / mag_norm
                        
                        # Calculate yaw from magnetometer (simplified)
                        mag_yaw = math.atan2(mag_normalized[1], mag_normalized[0])
                        acc_orientation[2] = mag_yaw
                
                # Apply complementary filter
                if dt is not None:
                    # Predict with gyroscope
                    gyro_orientation = self.orientation + (gyroscope - self.gyro_bias) * dt
                    gyro_orientation = self._wrap_angles(gyro_orientation)
                    
                    # Combine predictions
                    self.orientation = (self.alpha * gyro_orientation + 
                                      (1 - self.alpha) * acc_orientation)
                else:
                    # Direct fusion without prediction
                    self.orientation = (self.alpha * self.orientation + 
                                      (1 - self.alpha) * acc_orientation)
                
                # Update bias estimation
                if self.bias_estimation_enabled and dt is not None:
                    orientation_error = acc_orientation - self.orientation
                    self.gyro_bias += self.beta * orientation_error / dt
            
            # Wrap final angles
            self.orientation = self._wrap_angles(self.orientation)
            
            return self.orientation
        
        except Exception as e:
            self.logger.error(f"Error in complementary filter update step: {e}")
            return self.orientation
    
    def _wrap_angles(self, angles: np.ndarray) -> np.ndarray:
        """Wrap angles to [-pi, pi] range."""
        return np.arctan2(np.sin(angles), np.cos(angles))
    
    def get_state(self) -> np.ndarray:
        """Get current orientation estimate."""
        return self.orientation.copy()
    
    def get_covariance(self) -> np.ndarray:
        """Get current orientation covariance."""
        return self.covariance.copy()
    
    def get_roll_pitch_yaw(self) -> Tuple[float, float, float]:
        """Get orientation as roll, pitch, yaw tuple."""
        return tuple(self.orientation)
    
    def get_quaternion(self) -> Tuple[float, float, float, float]:
        """Convert orientation to quaternion (x, y, z, w)."""
        roll, pitch, yaw = self.orientation
        
        # Convert Euler angles to quaternion
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return (x, y, z, w)
    
    def set_orientation(self, orientation: np.ndarray) -> None:
        """Set current orientation."""
        if len(orientation) == 3:
            self.orientation = self._wrap_angles(orientation.copy())
        else:
            self.logger.error(f"Invalid orientation dimension: {len(orientation)}, expected 3")
    
    def set_bias(self, bias: np.ndarray) -> None:
        """Set gyroscope bias."""
        if len(bias) == 3:
            self.gyro_bias = bias.copy()
        else:
            self.logger.error(f"Invalid bias dimension: {len(bias)}, expected 3")
    
    def enable_bias_estimation(self, enable: bool) -> None:
        """Enable or disable bias estimation."""
        self.bias_estimation_enabled = enable
        self.logger.info(f"Bias estimation {'enabled' if enable else 'disabled'}")
    
    def reset(self) -> None:
        """Reset filter to initial state."""
        self.orientation = np.array([0.0, 0.0, 0.0])
        self.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.gyro_bias = np.array([0.0, 0.0, 0.0])
        self.covariance = np.eye(3) * 0.1
        self.last_time = None
        self.logger.info("Complementary filter reset")


class AdaptiveFilter(FilterBase):
    """Adaptive Filter that switches between different filtering strategies.
    
    Automatically selects the best filtering approach based on sensor
    quality, motion dynamics, and environmental conditions.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize sub-filters
        self.kalman_filter = KalmanFilter()
        self.particle_filter = ParticleFilter()
        self.complementary_filter = ComplementaryFilter()
        
        # Current active filter
        self.active_filter = self.kalman_filter
        self.filter_weights = {
            'kalman': 1.0,
            'particle': 0.0,
            'complementary': 0.0
        }
        
        # Adaptation parameters
        self.adaptation_enabled = True
        self.performance_history = []
        self.switch_threshold = 0.1
        
        self.initialized = True
        self.logger.info("Adaptive filter initialized")
    
    def predict(self, dt: float) -> None:
        """Predict step for all filters."""
        try:
            self.kalman_filter.predict(dt)
            self.particle_filter.predict(dt)
            self.complementary_filter.predict(dt)
        except Exception as e:
            self.logger.error(f"Error in adaptive filter predict step: {e}")
    
    def update(self, measurement: np.ndarray, sensor_quality: float = 1.0) -> np.ndarray:
        """Update step with automatic filter selection."""
        try:
            # Update all filters
            kalman_result = self.kalman_filter.update(measurement)
            particle_result = self.particle_filter.update(measurement)
            
            # For complementary filter, assume measurement contains IMU data
            if len(measurement) >= 6:
                comp_result = self.complementary_filter.update(
                    measurement[0:3],  # accelerometer
                    measurement[3:6]   # gyroscope
                )
            else:
                comp_result = self.complementary_filter.get_state()
            
            # Adapt filter weights based on performance
            if self.adaptation_enabled:
                self._adapt_filter_weights(measurement, sensor_quality)
            
            # Combine results based on weights
            combined_result = (
                self.filter_weights['kalman'] * kalman_result[:len(comp_result)] +
                self.filter_weights['particle'] * particle_result[:len(comp_result)] +
                self.filter_weights['complementary'] * comp_result
            )
            
            return combined_result
        
        except Exception as e:
            self.logger.error(f"Error in adaptive filter update step: {e}")
            return self.active_filter.get_state()
    
    def _adapt_filter_weights(self, measurement: np.ndarray, sensor_quality: float) -> None:
        """Adapt filter weights based on performance."""
        try:
            # Calculate prediction errors for each filter
            kalman_error = self._calculate_prediction_error(self.kalman_filter, measurement)
            particle_error = self._calculate_prediction_error(self.particle_filter, measurement)
            comp_error = self._calculate_prediction_error(self.complementary_filter, measurement)
            
            # Calculate weights based on inverse error (lower error = higher weight)
            errors = np.array([kalman_error, particle_error, comp_error])
            errors = np.maximum(errors, 1e-6)  # Avoid division by zero
            
            weights = 1.0 / errors
            weights *= sensor_quality  # Scale by sensor quality
            weights /= np.sum(weights)  # Normalize
            
            # Update filter weights with smoothing
            alpha = 0.1  # Smoothing factor
            self.filter_weights['kalman'] = (1 - alpha) * self.filter_weights['kalman'] + alpha * weights[0]
            self.filter_weights['particle'] = (1 - alpha) * self.filter_weights['particle'] + alpha * weights[1]
            self.filter_weights['complementary'] = (1 - alpha) * self.filter_weights['complementary'] + alpha * weights[2]
            
            # Normalize weights
            total_weight = sum(self.filter_weights.values())
            for key in self.filter_weights:
                self.filter_weights[key] /= total_weight
        
        except Exception as e:
            self.logger.error(f"Error adapting filter weights: {e}")
    
    def _calculate_prediction_error(self, filter_obj: FilterBase, measurement: np.ndarray) -> float:
        """Calculate prediction error for a filter."""
        try:
            predicted_state = filter_obj.get_state()
            
            # Compare relevant parts of state with measurement
            min_len = min(len(predicted_state), len(measurement))
            error = np.linalg.norm(predicted_state[:min_len] - measurement[:min_len])
            
            return error
        
        except Exception as e:
            self.logger.error(f"Error calculating prediction error: {e}")
            return 1.0
    
    def get_state(self) -> np.ndarray:
        """Get current state estimate from active filter."""
        return self.active_filter.get_state()
    
    def get_covariance(self) -> np.ndarray:
        """Get current covariance estimate from active filter."""
        return self.active_filter.get_covariance()
    
    def get_filter_weights(self) -> Dict[str, float]:
        """Get current filter weights."""
        return self.filter_weights.copy()
    
    def set_adaptation_enabled(self, enabled: bool) -> None:
        """Enable or disable adaptive behavior."""
        self.adaptation_enabled = enabled
        self.logger.info(f"Adaptive filtering {'enabled' if enabled else 'disabled'}")
    
    def reset(self) -> None:
        """Reset all filters to initial state."""
        self.kalman_filter.reset()
        self.particle_filter.reset()
        self.complementary_filter.reset()
        
        self.filter_weights = {
            'kalman': 1.0,
            'particle': 0.0,
            'complementary': 0.0
        }
        
        self.performance_history.clear()
        self.logger.info("Adaptive filter reset