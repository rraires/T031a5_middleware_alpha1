// Export all services
export { apiClient, API_BASE_URL, API_TIMEOUT } from './apiClient'
export { authService } from './authService'
export { robotService } from './robotService'
export { videoService } from './videoService'

// Re-export types for convenience
export type {
  ApiResponse,
  ApiError,
  User,
  RobotState,
  MotionCommand,
  SystemMetrics,
  SensorData,
  VideoStream,
  VideoSettings
} from '../types'