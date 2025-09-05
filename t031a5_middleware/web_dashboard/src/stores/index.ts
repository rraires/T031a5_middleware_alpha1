// Authentication store
export { useAuthStore } from './authStore'

// Theme store
export { useThemeStore } from './themeStore'

// Robot store
export { useRobotStore } from './robotStore'

// Video store
export { useVideoStore } from './videoStore'

// Settings store
export { useSettingsStore } from './settingsStore'

// Notification store
export { useNotificationStore } from './notificationStore'

// Re-export types for convenience
export type {
  AuthState,
  ThemeState,
  RobotState,
  VideoState,
  SettingsState,
  NotificationState
} from '../types'