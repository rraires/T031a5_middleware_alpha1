// Context providers
export { 
  AuthProvider, 
  ThemeProvider, 
  WebSocketProvider, 
  RobotProvider 
} from '../contexts'

// Authentication hooks
export { 
  useAuth, 
  usePermission, 
  useRole, 
  useAdminOnly, 
  useOperatorAccess 
} from './useAuth'

// Robot management hooks
export { 
  useRobot, 
  useSensorData, 
  useBattery, 
  useMovement 
} from './useRobot'

// Video management hooks
export { 
  useVideo, 
  useVideoStream, 
  useVideoRecording 
} from './useVideo'

// WebSocket hooks
export { 
  useWebSocket, 
  useWebSocketSubscription, 
  useRobotStatusUpdates, 
  useSensorDataUpdates, 
  useSystemMetricsUpdates, 
  useWebSocketMessage, 
  useConnectionStatus 
} from './useWebSocket'

// Re-export common types for convenience
export type {
  User,
  UserRole,
  Permission,
  RobotState,
  RobotStatus,
  MotionCommand,
  SensorData,
  SystemMetrics,
  VideoStream,
  VideoConfig,
  VideoRecording,
  WebSocketMessage,
  MessageType
} from '../types'