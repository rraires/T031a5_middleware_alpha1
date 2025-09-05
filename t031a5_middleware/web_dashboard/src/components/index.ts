/**
 * Components exports
 */

// Layout components
export { Header } from './Header'
export { Sidebar } from './Sidebar'
export { Layout, LoadingSpinner, ErrorBoundary, ProtectedRoute } from './Layout'

// UI components
export * from './ui'

// Re-export common types for convenience
export type {
  User,
  UserRole,
  Permission,
  RobotStatus,
  RobotCommand,
  SensorData,
  VideoStream,
  AudioConfig,
  LEDConfig,
  SystemMetrics,
  ApiResponse,
  WebSocketMessage
} from '../types'