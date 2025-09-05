"""Video Processing module for t031a5_middleware.

Handles real-time video processing including object detection, face recognition,
motion detection, and other computer vision tasks.
"""

import cv2
import numpy as np
import asyncio
import threading
import logging
import time
import json
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty
import mediapipe as mp


class ProcessingMode(Enum):
    """Video processing modes."""
    DISABLED = "disabled"
    OBJECT_DETECTION = "object_detection"
    FACE_DETECTION = "face_detection"
    FACE_RECOGNITION = "face_recognition"
    MOTION_DETECTION = "motion_detection"
    POSE_ESTIMATION = "pose_estimation"
    HAND_TRACKING = "hand_tracking"
    FULL_ANALYSIS = "full_analysis"


class ProcessingState(Enum):
    """Processing states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class DetectionResult:
    """Detection result data."""
    type: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    label: str
    timestamp: float
    additional_data: Dict[str, Any] = None


@dataclass
class FaceResult:
    """Face detection/recognition result."""
    bbox: Tuple[int, int, int, int]
    confidence: float
    landmarks: List[Tuple[int, int]]
    identity: Optional[str] = None
    identity_confidence: float = 0.0
    age: Optional[int] = None
    gender: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class MotionResult:
    """Motion detection result."""
    motion_detected: bool
    motion_areas: List[Tuple[int, int, int, int]]
    motion_intensity: float
    direction: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class PoseResult:
    """Pose estimation result."""
    keypoints: List[Tuple[int, int, float]]  # x, y, confidence
    pose_confidence: float
    pose_type: str  # standing, sitting, lying, etc.
    timestamp: float = 0.0


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    mode: ProcessingMode = ProcessingMode.OBJECT_DETECTION
    target_fps: int = 10
    max_detections: int = 10
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    enable_tracking: bool = True
    save_results: bool = False
    draw_annotations: bool = True
    annotation_color: Tuple[int, int, int] = (0, 255, 0)
    annotation_thickness: int = 2


@dataclass
class ProcessingStats:
    """Processing statistics."""
    frames_processed: int = 0
    processing_fps: float = 0.0
    average_processing_time: float = 0.0
    total_detections: int = 0
    faces_detected: int = 0
    objects_detected: int = 0
    motion_events: int = 0
    errors: int = 0


class VideoProcessor:
    """Video processing manager.
    
    Handles real-time video processing including object detection, face recognition,
    motion detection, and pose estimation using OpenCV and MediaPipe.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.logger = logging.getLogger(__name__)
        
        # State management
        self._state = ProcessingState.STOPPED
        self._lock = threading.RLock()
        self._running = False
        
        # Processing components
        self._face_detector = None
        self._face_recognizer = None
        self._object_detector = None
        self._pose_estimator = None
        self._hand_tracker = None
        
        # MediaPipe components
        self._mp_face_detection = mp.solutions.face_detection
        self._mp_face_mesh = mp.solutions.face_mesh
        self._mp_pose = mp.solutions.pose
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        
        # Frame management
        self._input_queue: Queue = Queue(maxsize=10)
        self._output_queue: Queue = Queue(maxsize=10)
        self._latest_results: Dict[str, Any] = {}
        
        # Motion detection
        self._background_subtractor = None
        self._previous_frame = None
        self._motion_threshold = 1000
        
        # Object detection (using OpenCV DNN)
        self._net = None
        self._output_layers = None
        self._class_names = []
        
        # Threading
        self._processing_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._stats = ProcessingStats()
        self._processing_times: List[float] = []
        self._last_stats_update = time.time()
        
        # Callbacks
        self._detection_callbacks: List[Callable] = []
        self._face_callbacks: List[Callable] = []
        self._motion_callbacks: List[Callable] = []
        self._pose_callbacks: List[Callable] = []
        
        # Known faces database (for recognition)
        self._known_faces: Dict[str, np.ndarray] = {}
        
        self.logger.info("VideoProcessor initialized")
    
    async def initialize(self) -> bool:
        """Initialize video processor."""
        try:
            with self._lock:
                if self._state != ProcessingState.STOPPED:
                    self.logger.warning("VideoProcessor already initialized")
                    return True
                
                self._set_state(ProcessingState.STARTING)
                
                # Initialize processing components based on mode
                await self._initialize_components()
                
                self._set_state(ProcessingState.RUNNING)
                self.logger.info("VideoProcessor initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize VideoProcessor: {e}")
            self._set_state(ProcessingState.ERROR)
            return False
    
    async def start(self) -> bool:
        """Start video processing."""
        try:
            with self._lock:
                if self._state == ProcessingState.RUNNING:
                    self.logger.warning("VideoProcessor already running")
                    return True
                
                if self._state != ProcessingState.RUNNING:
                    if not await self.initialize():
                        return False
                
                self._running = True
                
                # Start processing thread
                self._processing_thread = threading.Thread(
                    target=self._processing_loop,
                    name="VideoProcessor-Main",
                    daemon=True
                )
                self._processing_thread.start()
                
                # Start monitor thread
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    name="VideoProcessor-Monitor",
                    daemon=True
                )
                self._monitor_thread.start()
                
                self.logger.info("VideoProcessor started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start VideoProcessor: {e}")
            self._set_state(ProcessingState.ERROR)
            return False
    
    async def stop(self) -> bool:
        """Stop video processing."""
        try:
            with self._lock:
                if self._state == ProcessingState.STOPPED:
                    return True
                
                self._running = False
                
                # Wait for threads to finish
                if self._processing_thread and self._processing_thread.is_alive():
                    self._processing_thread.join(timeout=2.0)
                
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=1.0)
                
                # Clear queues
                while not self._input_queue.empty():
                    try:
                        self._input_queue.get_nowait()
                    except Empty:
                        break
                
                while not self._output_queue.empty():
                    try:
                        self._output_queue.get_nowait()
                    except Empty:
                        break
                
                # Clean up components
                await self._cleanup_components()
                
                self._set_state(ProcessingState.STOPPED)
                self.logger.info("VideoProcessor stopped successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop VideoProcessor: {e}")
            return False
    
    async def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process a single frame."""
        try:
            if self._state != ProcessingState.RUNNING:
                return frame
            
            current_time = time.time()
            
            # Add frame to input queue
            try:
                self._input_queue.put_nowait((frame.copy(), current_time))
            except:
                # Queue full, drop oldest frame
                try:
                    self._input_queue.get_nowait()
                    self._input_queue.put_nowait((frame.copy(), current_time))
                except:
                    pass
            
            # Get processed frame from output queue
            try:
                processed_frame, _ = self._output_queue.get_nowait()
                return processed_frame
            except Empty:
                return frame
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return frame
    
    def add_detection_callback(self, callback: Callable) -> None:
        """Add detection callback."""
        self._detection_callbacks.append(callback)
    
    def add_face_callback(self, callback: Callable) -> None:
        """Add face detection callback."""
        self._face_callbacks.append(callback)
    
    def add_motion_callback(self, callback: Callable) -> None:
        """Add motion detection callback."""
        self._motion_callbacks.append(callback)
    
    def add_pose_callback(self, callback: Callable) -> None:
        """Add pose estimation callback."""
        self._pose_callbacks.append(callback)
    
    async def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """Add known face for recognition."""
        try:
            # Extract face encoding
            face_encoding = await self._extract_face_encoding(face_image)
            if face_encoding is not None:
                self._known_faces[name] = face_encoding
                self.logger.info(f"Added known face: {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding known face {name}: {e}")
            return False
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get latest processing results."""
        return self._latest_results.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        self._update_statistics()
        return asdict(self._stats)
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update processing configuration."""
        try:
            with self._lock:
                # Update config values
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                # Reinitialize components if mode changed
                if 'mode' in config:
                    await self._initialize_components()
                
                self.logger.info("Processing configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update processing configuration: {e}")
            return False
    
    async def _initialize_components(self) -> None:
        """Initialize processing components based on mode."""
        try:
            mode = self.config.mode
            
            if mode in [ProcessingMode.FACE_DETECTION, ProcessingMode.FACE_RECOGNITION, ProcessingMode.FULL_ANALYSIS]:
                self._face_detector = self._mp_face_detection.FaceDetection(
                    model_selection=0,
                    min_detection_confidence=self.config.confidence_threshold
                )
                
                if mode == ProcessingMode.FACE_RECOGNITION:
                    # Initialize face recognition components
                    pass  # Would need face_recognition library or custom implementation
            
            if mode in [ProcessingMode.OBJECT_DETECTION, ProcessingMode.FULL_ANALYSIS]:
                # Initialize YOLO or other object detection model
                await self._initialize_object_detection()
            
            if mode in [ProcessingMode.MOTION_DETECTION, ProcessingMode.FULL_ANALYSIS]:
                self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
                    detectShadows=True
                )
            
            if mode in [ProcessingMode.POSE_ESTIMATION, ProcessingMode.FULL_ANALYSIS]:
                self._pose_estimator = self._mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=self.config.confidence_threshold,
                    min_tracking_confidence=0.5
                )
            
            if mode in [ProcessingMode.HAND_TRACKING, ProcessingMode.FULL_ANALYSIS]:
                self._hand_tracker = self._mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    model_complexity=0,
                    min_detection_confidence=self.config.confidence_threshold,
                    min_tracking_confidence=0.5
                )
            
            self.logger.info(f"Initialized components for mode: {mode.value}")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    async def _initialize_object_detection(self) -> None:
        """Initialize object detection model."""
        try:
            # This would typically load a pre-trained model like YOLO
            # For now, we'll use OpenCV's DNN module with a placeholder
            
            # Example COCO class names
            self._class_names = [
                'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
                'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
                'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
                'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
                'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
                'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
                'toothbrush'
            ]
            
            # Note: In a real implementation, you would load actual model weights
            # self._net = cv2.dnn.readNet('yolo.weights', 'yolo.cfg')
            # self._output_layers = self._net.getUnconnectedOutLayersNames()
            
            self.logger.info("Object detection model initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing object detection: {e}")
    
    async def _cleanup_components(self) -> None:
        """Clean up processing components."""
        try:
            if self._face_detector:
                self._face_detector.close()
                self._face_detector = None
            
            if self._pose_estimator:
                self._pose_estimator.close()
                self._pose_estimator = None
            
            if self._hand_tracker:
                self._hand_tracker.close()
                self._hand_tracker = None
            
            self._background_subtractor = None
            self._net = None
            self._previous_frame = None
            
            self.logger.info("Processing components cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up components: {e}")
    
    def _processing_loop(self) -> None:
        """Main processing loop."""
        self.logger.info("Video processing loop started")
        
        frame_time = 1.0 / self.config.target_fps
        last_process_time = 0.0
        
        while self._running:
            try:
                if self._state != ProcessingState.RUNNING:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                # Control processing rate
                if current_time - last_process_time < frame_time:
                    time.sleep(0.01)
                    continue
                
                # Get frame from input queue
                try:
                    frame, timestamp = self._input_queue.get(timeout=0.1)
                except Empty:
                    continue
                
                # Process frame
                start_time = time.time()
                processed_frame, results = await self._process_frame_internal(frame, timestamp)
                processing_time = time.time() - start_time
                
                # Update statistics
                self._processing_times.append(processing_time)
                self._stats.frames_processed += 1
                
                # Store latest results
                self._latest_results.update(results)
                
                # Add processed frame to output queue
                try:
                    self._output_queue.put_nowait((processed_frame, timestamp))
                except:
                    # Queue full, drop oldest frame
                    try:
                        self._output_queue.get_nowait()
                        self._output_queue.put_nowait((processed_frame, timestamp))
                    except:
                        pass
                
                # Trigger callbacks
                await self._trigger_callbacks(results)
                
                last_process_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self._stats.errors += 1
                time.sleep(0.1)
        
        self.logger.info("Video processing loop stopped")
    
    def _monitor_loop(self) -> None:
        """Statistics monitoring loop."""
        self.logger.info("Video processing monitor started")
        
        while self._running:
            try:
                # Update statistics
                self._update_statistics()
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in processing monitor: {e}")
                time.sleep(1.0)
        
        self.logger.info("Video processing monitor stopped")
    
    async def _process_frame_internal(self, frame: np.ndarray, timestamp: float) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Internal frame processing."""
        results = {}
        processed_frame = frame.copy()
        
        try:
            mode = self.config.mode
            
            if mode == ProcessingMode.DISABLED:
                return processed_frame, results
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Face detection
            if mode in [ProcessingMode.FACE_DETECTION, ProcessingMode.FACE_RECOGNITION, ProcessingMode.FULL_ANALYSIS]:
                face_results = await self._detect_faces(rgb_frame, timestamp)
                results['faces'] = face_results
                
                if self.config.draw_annotations:
                    processed_frame = self._draw_face_annotations(processed_frame, face_results)
            
            # Object detection
            if mode in [ProcessingMode.OBJECT_DETECTION, ProcessingMode.FULL_ANALYSIS]:
                object_results = await self._detect_objects(frame, timestamp)
                results['objects'] = object_results
                
                if self.config.draw_annotations:
                    processed_frame = self._draw_object_annotations(processed_frame, object_results)
            
            # Motion detection
            if mode in [ProcessingMode.MOTION_DETECTION, ProcessingMode.FULL_ANALYSIS]:
                motion_results = await self._detect_motion(frame, timestamp)
                results['motion'] = motion_results
                
                if self.config.draw_annotations:
                    processed_frame = self._draw_motion_annotations(processed_frame, motion_results)
            
            # Pose estimation
            if mode in [ProcessingMode.POSE_ESTIMATION, ProcessingMode.FULL_ANALYSIS]:
                pose_results = await self._estimate_pose(rgb_frame, timestamp)
                results['pose'] = pose_results
                
                if self.config.draw_annotations:
                    processed_frame = self._draw_pose_annotations(processed_frame, pose_results)
            
            # Hand tracking
            if mode in [ProcessingMode.HAND_TRACKING, ProcessingMode.FULL_ANALYSIS]:
                hand_results = await self._track_hands(rgb_frame, timestamp)
                results['hands'] = hand_results
                
                if self.config.draw_annotations:
                    processed_frame = self._draw_hand_annotations(processed_frame, hand_results)
            
            return processed_frame, results
            
        except Exception as e:
            self.logger.error(f"Error in internal frame processing: {e}")
            return processed_frame, results
    
    async def _detect_faces(self, rgb_frame: np.ndarray, timestamp: float) -> List[FaceResult]:
        """Detect faces in frame."""
        try:
            if not self._face_detector:
                return []
            
            results = self._face_detector.process(rgb_frame)
            face_results = []
            
            if results.detections:
                h, w = rgb_frame.shape[:2]
                
                for detection in results.detections:
                    bbox_rel = detection.location_data.relative_bounding_box
                    bbox = (
                        int(bbox_rel.xmin * w),
                        int(bbox_rel.ymin * h),
                        int(bbox_rel.width * w),
                        int(bbox_rel.height * h)
                    )
                    
                    confidence = detection.score[0]
                    
                    # Extract landmarks
                    landmarks = []
                    if detection.location_data.relative_keypoints:
                        for keypoint in detection.location_data.relative_keypoints:
                            landmarks.append((
                                int(keypoint.x * w),
                                int(keypoint.y * h)
                            ))
                    
                    face_result = FaceResult(
                        bbox=bbox,
                        confidence=confidence,
                        landmarks=landmarks,
                        timestamp=timestamp
                    )
                    
                    face_results.append(face_result)
                    self._stats.faces_detected += 1
            
            return face_results
            
        except Exception as e:
            self.logger.error(f"Error in face detection: {e}")
            return []
    
    async def _detect_objects(self, frame: np.ndarray, timestamp: float) -> List[DetectionResult]:
        """Detect objects in frame."""
        try:
            # Placeholder for object detection
            # In a real implementation, this would use YOLO or similar
            
            # Simple contour-based detection as placeholder
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            object_results = []
            for i, contour in enumerate(contours[:self.config.max_detections]):
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    detection = DetectionResult(
                        type="object",
                        confidence=0.7,  # Placeholder confidence
                        bbox=(x, y, w, h),
                        label="unknown_object",
                        timestamp=timestamp
                    )
                    
                    object_results.append(detection)
                    self._stats.objects_detected += 1
            
            return object_results
            
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return []
    
    async def _detect_motion(self, frame: np.ndarray, timestamp: float) -> MotionResult:
        """Detect motion in frame."""
        try:
            if not self._background_subtractor:
                return MotionResult(
                    motion_detected=False,
                    motion_areas=[],
                    motion_intensity=0.0,
                    timestamp=timestamp
                )
            
            # Apply background subtraction
            fg_mask = self._background_subtractor.apply(frame)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_areas = []
            total_motion_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self._motion_threshold:
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_areas.append((x, y, w, h))
                    total_motion_area += area
            
            motion_detected = len(motion_areas) > 0
            motion_intensity = min(total_motion_area / (frame.shape[0] * frame.shape[1]), 1.0)
            
            if motion_detected:
                self._stats.motion_events += 1
            
            return MotionResult(
                motion_detected=motion_detected,
                motion_areas=motion_areas,
                motion_intensity=motion_intensity,
                timestamp=timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Error in motion detection: {e}")
            return MotionResult(
                motion_detected=False,
                motion_areas=[],
                motion_intensity=0.0,
                timestamp=timestamp
            )
    
    async def _estimate_pose(self, rgb_frame: np.ndarray, timestamp: float) -> Optional[PoseResult]:
        """Estimate pose in frame."""
        try:
            if not self._pose_estimator:
                return None
            
            results = self._pose_estimator.process(rgb_frame)
            
            if results.pose_landmarks:
                h, w = rgb_frame.shape[:2]
                
                keypoints = []
                for landmark in results.pose_landmarks.landmark:
                    keypoints.append((
                        int(landmark.x * w),
                        int(landmark.y * h),
                        landmark.visibility
                    ))
                
                # Simple pose classification based on keypoints
                pose_type = self._classify_pose(keypoints)
                
                return PoseResult(
                    keypoints=keypoints,
                    pose_confidence=0.8,  # Placeholder
                    pose_type=pose_type,
                    timestamp=timestamp
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in pose estimation: {e}")
            return None
    
    async def _track_hands(self, rgb_frame: np.ndarray, timestamp: float) -> List[Dict[str, Any]]:
        """Track hands in frame."""
        try:
            if not self._hand_tracker:
                return []
            
            results = self._hand_tracker.process(rgb_frame)
            hand_results = []
            
            if results.multi_hand_landmarks:
                h, w = rgb_frame.shape[:2]
                
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = []
                    for landmark in hand_landmarks.landmark:
                        landmarks.append((
                            int(landmark.x * w),
                            int(landmark.y * h),
                            landmark.z
                        ))
                    
                    hand_results.append({
                        'landmarks': landmarks,
                        'timestamp': timestamp
                    })
            
            return hand_results
            
        except Exception as e:
            self.logger.error(f"Error in hand tracking: {e}")
            return []
    
    def _classify_pose(self, keypoints: List[Tuple[int, int, float]]) -> str:
        """Simple pose classification."""
        try:
            # This is a very basic pose classifier
            # In a real implementation, you would use more sophisticated methods
            
            if len(keypoints) < 33:  # MediaPipe pose has 33 landmarks
                return "unknown"
            
            # Get key landmarks
            nose = keypoints[0]
            left_shoulder = keypoints[11]
            right_shoulder = keypoints[12]
            left_hip = keypoints[23]
            right_hip = keypoints[24]
            
            # Simple standing/sitting classification based on hip-shoulder distance
            shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
            hip_y = (left_hip[1] + right_hip[1]) / 2
            
            if hip_y - shoulder_y > 100:  # Arbitrary threshold
                return "standing"
            else:
                return "sitting"
            
        except Exception as e:
            self.logger.error(f"Error classifying pose: {e}")
            return "unknown"
    
    def _draw_face_annotations(self, frame: np.ndarray, face_results: List[FaceResult]) -> np.ndarray:
        """Draw face detection annotations."""
        for face in face_results:
            x, y, w, h = face.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.config.annotation_color, self.config.annotation_thickness)
            
            # Draw confidence
            label = f"Face: {face.confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.config.annotation_color, 1)
            
            # Draw landmarks
            for landmark in face.landmarks:
                cv2.circle(frame, landmark, 2, (0, 255, 255), -1)
        
        return frame
    
    def _draw_object_annotations(self, frame: np.ndarray, object_results: List[DetectionResult]) -> np.ndarray:
        """Draw object detection annotations."""
        for obj in object_results:
            x, y, w, h = obj.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), self.config.annotation_thickness)
            
            # Draw label
            label = f"{obj.label}: {obj.confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        return frame
    
    def _draw_motion_annotations(self, frame: np.ndarray, motion_result: MotionResult) -> np.ndarray:
        """Draw motion detection annotations."""
        if motion_result.motion_detected:
            for x, y, w, h in motion_result.motion_areas:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            # Draw motion intensity
            intensity_text = f"Motion: {motion_result.motion_intensity:.2f}"
            cv2.putText(frame, intensity_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def _draw_pose_annotations(self, frame: np.ndarray, pose_result: Optional[PoseResult]) -> np.ndarray:
        """Draw pose estimation annotations."""
        if pose_result:
            # Draw pose type
            cv2.putText(frame, f"Pose: {pose_result.pose_type}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Draw keypoints
            for x, y, confidence in pose_result.keypoints:
                if confidence > 0.5:
                    cv2.circle(frame, (x, y), 3, (255, 255, 0), -1)
        
        return frame
    
    def _draw_hand_annotations(self, frame: np.ndarray, hand_results: List[Dict[str, Any]]) -> np.ndarray:
        """Draw hand tracking annotations."""
        for hand in hand_results:
            landmarks = hand['landmarks']
            
            # Draw hand landmarks
            for x, y, z in landmarks:
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        
        return frame
    
    async def _extract_face_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face encoding for recognition."""
        try:
            # Placeholder for face encoding extraction
            # In a real implementation, you would use face_recognition library or similar
            
            # Simple feature extraction using histogram
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (64, 64))
            hist = cv2.calcHist([resized], [0], None, [256], [0, 256])
            
            return hist.flatten()
            
        except Exception as e:
            self.logger.error(f"Error extracting face encoding: {e}")
            return None
    
    async def _trigger_callbacks(self, results: Dict[str, Any]) -> None:
        """Trigger appropriate callbacks based on results."""
        try:
            # Face detection callbacks
            if 'faces' in results and results['faces']:
                for callback in self._face_callbacks:
                    try:
                        await callback(results['faces'])
                    except Exception as e:
                        self.logger.error(f"Error in face callback: {e}")
            
            # Object detection callbacks
            if 'objects' in results and results['objects']:
                for callback in self._detection_callbacks:
                    try:
                        await callback(results['objects'])
                    except Exception as e:
                        self.logger.error(f"Error in detection callback: {e}")
            
            # Motion detection callbacks
            if 'motion' in results and results['motion'].motion_detected:
                for callback in self._motion_callbacks:
                    try:
                        await callback(results['motion'])
                    except Exception as e:
                        self.logger.error(f"Error in motion callback: {e}")
            
            # Pose estimation callbacks
            if 'pose' in results and results['pose']:
                for callback in self._pose_callbacks:
                    try:
                        await callback(results['pose'])
                    except Exception as e:
                        self.logger.error(f"Error in pose callback: {e}")
        
        except Exception as e:
            self.logger.error(f"Error triggering callbacks: {e}")
    
    def _update_statistics(self) -> None:
        """Update processing statistics."""
        current_time = time.time()
        
        # Calculate processing FPS
        if self._processing_times:
            recent_times = [t for t in self._processing_times if current_time - t < 1.0]
            self._stats.processing_fps = len(recent_times)
            
            # Calculate average processing time
            if recent_times:
                self._stats.average_processing_time = sum(recent_times) / len(recent_times)
            
            # Keep only recent processing times
            self._processing_times = recent_times
        
        self._last_stats_update = current_time
    
    def _set_state(self, new_state: ProcessingState) -> None:
        """Set processing state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.logger.info(f"Processing state changed: {old_state.value} -> {new_state.value}")