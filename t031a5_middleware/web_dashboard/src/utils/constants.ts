/**
 * Application constants and configuration values
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
} as const

// WebSocket Configuration
export const WEBSOCKET_CONFIG = {
  URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  RECONNECT_INTERVAL: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
  HEARTBEAT_INTERVAL: 30000,
  CONNECTION_TIMEOUT: 10000
} as const

// Robot Configuration
export const ROBOT_CONFIG = {
  MAX_SPEED: 2.0, // m/s
  MAX_DISTANCE: 10.0, // meters
  MAX_TURN_ANGLE: 180, // degrees
  MIN_BATTERY_WARNING: 20, // percentage
  CRITICAL_BATTERY_WARNING: 10, // percentage
  STATUS_UPDATE_INTERVAL: 1000, // ms
  SENSOR_UPDATE_INTERVAL: 500, // ms
  METRICS_UPDATE_INTERVAL: 5000 // ms
} as const

// Video Configuration
export const VIDEO_CONFIG = {
  DEFAULT_RESOLUTION: {
    width: 1280,
    height: 720
  },
  SUPPORTED_RESOLUTIONS: [
    { width: 640, height: 480, label: '480p' },
    { width: 1280, height: 720, label: '720p' },
    { width: 1920, height: 1080, label: '1080p' },
    { width: 3840, height: 2160, label: '4K' }
  ],
  DEFAULT_FRAMERATE: 30,
  SUPPORTED_FRAMERATES: [15, 24, 30, 60],
  DEFAULT_BITRATE: 2000, // kbps
  QUALITY_PRESETS: {
    low: { bitrate: 500, framerate: 15 },
    medium: { bitrate: 1500, framerate: 30 },
    high: { bitrate: 3000, framerate: 30 },
    ultra: { bitrate: 6000, framerate: 60 }
  },
  MAX_RECORDING_SIZE: 1024 * 1024 * 1024, // 1GB
  SUPPORTED_FORMATS: ['mp4', 'webm', 'avi']
} as const

// Video Frame Rates (for compatibility)
export const VIDEO_FRAME_RATES = VIDEO_CONFIG.SUPPORTED_FRAMERATES

// Video Quality (for compatibility)
export const VIDEO_QUALITY = VIDEO_CONFIG.QUALITY_PRESETS
export const VIDEO_QUALITY_LEVELS = VIDEO_CONFIG.QUALITY_PRESETS

// Video Resolutions (for compatibility)
export const VIDEO_RESOLUTIONS = VIDEO_CONFIG.SUPPORTED_RESOLUTIONS.reduce((acc, res) => {
  acc[res.label.toLowerCase()] = res
  return acc
}, {} as Record<string, typeof VIDEO_CONFIG.SUPPORTED_RESOLUTIONS[0]>)

// Audio Configuration
export const AUDIO_CONFIG = {
  DEFAULT_VOLUME: 50, // percentage
  DEFAULT_SAMPLE_RATE: 44100,
  SUPPORTED_SAMPLE_RATES: [8000, 16000, 22050, 44100, 48000],
  DEFAULT_CHANNELS: 2,
  SUPPORTED_FORMATS: ['mp3', 'wav', 'ogg'],
  TTS_LANGUAGES: [
    { code: 'en-US', name: 'English (US)' },
    { code: 'en-GB', name: 'English (UK)' },
    { code: 'pt-BR', name: 'Portuguese (Brazil)' },
    { code: 'es-ES', name: 'Spanish (Spain)' },
    { code: 'fr-FR', name: 'French (France)' },
    { code: 'de-DE', name: 'German (Germany)' },
    { code: 'it-IT', name: 'Italian (Italy)' },
    { code: 'ja-JP', name: 'Japanese (Japan)' },
    { code: 'ko-KR', name: 'Korean (Korea)' },
    { code: 'zh-CN', name: 'Chinese (Simplified)' }
  ]
} as const

// Audio Sample Rates (for compatibility)
export const AUDIO_SAMPLE_RATES = AUDIO_CONFIG.SUPPORTED_SAMPLE_RATES

// Movement Speeds
export const MOVEMENT_SPEEDS = {
  SLOW: 0.5,
  NORMAL: 1.0,
  FAST: 1.5
} as const

// Robot Speed Levels (for compatibility)
export const ROBOT_SPEED_LEVELS = {
  slow: MOVEMENT_SPEEDS.SLOW,
  normal: MOVEMENT_SPEEDS.NORMAL,
  fast: MOVEMENT_SPEEDS.FAST
} as const

// TTS Languages (for compatibility)
export const TTS_LANGUAGES = AUDIO_CONFIG.TTS_LANGUAGES.reduce((acc, lang) => {
  acc[lang.code] = lang.name
  return acc
}, {} as Record<string, string>)

// LED Configuration
export const LED_CONFIG = {
  DEFAULT_BRIGHTNESS: 80, // percentage
  PATTERNS: [
    { id: 'solid', name: 'Solid', description: 'Static color' },
    { id: 'blink', name: 'Blink', description: 'Blinking pattern' },
    { id: 'fade', name: 'Fade', description: 'Fade in/out effect' },
    { id: 'rainbow', name: 'Rainbow', description: 'Color cycling' },
    { id: 'pulse', name: 'Pulse', description: 'Pulsing effect' }
  ],
  PRESET_COLORS: [
    { name: 'Red', r: 255, g: 0, b: 0 },
    { name: 'Green', r: 0, g: 255, b: 0 },
    { name: 'Blue', r: 0, g: 0, b: 255 },
    { name: 'Yellow', r: 255, g: 255, b: 0 },
    { name: 'Purple', r: 128, g: 0, b: 128 },
    { name: 'Orange', r: 255, g: 165, b: 0 },
    { name: 'Pink', r: 255, g: 192, b: 203 },
    { name: 'White', r: 255, g: 255, b: 255 }
  ]
} as const

// User Roles and Permissions
export const USER_ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
  VIEWER: 'viewer'
} as const

export const PERMISSIONS = {
  // Robot control
  ROBOT_CONTROL: 'robot:control',
  ROBOT_VIEW: 'robot:view',
  ROBOT_EMERGENCY_STOP: 'robot:emergency_stop',
  
  // Video management
  VIDEO_STREAM: 'video:stream',
  VIDEO_RECORD: 'video:record',
  VIDEO_CONFIGURE: 'video:configure',
  
  // Audio management
  AUDIO_CONTROL: 'audio:control',
  AUDIO_CONFIGURE: 'audio:configure',
  
  // LED control
  LED_CONTROL: 'led:control',
  LED_CONFIGURE: 'led:configure',
  
  // System management
  SYSTEM_VIEW: 'system:view',
  SYSTEM_CONFIGURE: 'system:configure',
  SYSTEM_LOGS: 'system:logs',
  
  // User management
  USER_MANAGE: 'user:manage',
  USER_VIEW: 'user:view'
} as const

export const ROLE_PERMISSIONS = {
  [USER_ROLES.ADMIN]: Object.values(PERMISSIONS),
  [USER_ROLES.OPERATOR]: [
    PERMISSIONS.ROBOT_CONTROL,
    PERMISSIONS.ROBOT_VIEW,
    PERMISSIONS.ROBOT_EMERGENCY_STOP,
    PERMISSIONS.VIDEO_STREAM,
    PERMISSIONS.VIDEO_RECORD,
    PERMISSIONS.AUDIO_CONTROL,
    PERMISSIONS.LED_CONTROL,
    PERMISSIONS.SYSTEM_VIEW
  ],
  [USER_ROLES.VIEWER]: [
    PERMISSIONS.ROBOT_VIEW,
    PERMISSIONS.VIDEO_STREAM,
    PERMISSIONS.SYSTEM_VIEW
  ]
} as const

// Status Constants
export const ROBOT_STATUS = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  ERROR: 'error',
  CHARGING: 'charging',
  LOW_BATTERY: 'low_battery'
} as const

export const MOTION_STATES = {
  IDLE: 'idle',
  WALKING: 'walking',
  RUNNING: 'running',
  SITTING: 'sitting',
  LYING: 'lying',
  STANDING: 'standing',
  ERROR: 'error'
} as const

export const CONNECTION_STATUS = {
  CONNECTED: 'connected',
  CONNECTING: 'connecting',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
} as const

// Motion Commands
export const MOTION_COMMANDS = {
  WALK: 'walk',
  RUN: 'run',
  TURN: 'turn',
  SIT: 'sit',
  STAND: 'stand',
  LIE_DOWN: 'lie_down',
  STOP: 'stop'
} as const

export const MOTION_DIRECTIONS = {
  FORWARD: 'forward',
  BACKWARD: 'backward',
  LEFT: 'left',
  RIGHT: 'right'
} as const

// Robot Modes
export const ROBOT_MODES = {
  MANUAL: 'manual',
  AUTO: 'auto',
  FOLLOW: 'follow',
  PATROL: 'patrol'
} as const

// Sensor Types
export const SENSOR_TYPES = {
  IMU: 'imu',
  CAMERA: 'camera',
  LIDAR: 'lidar',
  ULTRASONIC: 'ultrasonic',
  TEMPERATURE: 'temperature',
  BATTERY: 'battery',
  GPS: 'gps',
  ACCELEROMETER: 'accelerometer',
  GYROSCOPE: 'gyroscope',
  MAGNETOMETER: 'magnetometer'
} as const

// Chart Configuration
export const CHART_CONFIG = {
  DEFAULT_COLORS: [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // yellow
    '#EF4444', // red
    '#8B5CF6', // purple
    '#F97316', // orange
    '#06B6D4', // cyan
    '#84CC16'  // lime
  ],
  ANIMATION_DURATION: 300,
  GRID_COLOR: '#E5E7EB',
  TEXT_COLOR: '#6B7280',
  TOOLTIP_BACKGROUND: '#1F2937',
  TOOLTIP_TEXT_COLOR: '#F9FAFB'
} as const

// Theme Configuration
export const THEME_CONFIG = {
  MODES: {
    LIGHT: 'light',
    DARK: 'dark',
    AUTO: 'auto'
  },
  FONT_SIZES: {
    SMALL: 'small',
    MEDIUM: 'medium',
    LARGE: 'large'
  },
  BORDER_RADIUS: {
    NONE: 'none',
    SMALL: 'small',
    MEDIUM: 'medium',
    LARGE: 'large'
  }
} as const

// File Upload Configuration
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_VIDEO_TYPES: ['video/mp4', 'video/webm', 'video/avi', 'video/mov'],
  ALLOWED_AUDIO_TYPES: ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac'],
  CHUNK_SIZE: 1024 * 1024 // 1MB chunks for large file uploads
} as const

// Notification Configuration
export const NOTIFICATION_CONFIG = {
  DEFAULT_DURATION: 4000,
  SUCCESS_DURATION: 3000,
  ERROR_DURATION: 6000,
  WARNING_DURATION: 5000,
  MAX_NOTIFICATIONS: 5,
  POSITION: 'top-right'
} as const

// Dashboard Configuration
export const DASHBOARD_CONFIG = {
  REFRESH_INTERVAL: 5000, // ms
  CHART_UPDATE_INTERVAL: 1000, // ms
  MAX_DATA_POINTS: 100,
  WIDGET_GRID_COLS: 12,
  WIDGET_MIN_HEIGHT: 200,
  WIDGET_MARGIN: 16
} as const

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME_CONFIG: 'theme_config',
  DASHBOARD_LAYOUT: 'dashboard_layout',
  VIDEO_SETTINGS: 'video_settings',
  AUDIO_SETTINGS: 'audio_settings',
  ROBOT_SETTINGS: 'robot_settings'
} as const

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied. Insufficient permissions.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Internal server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  ROBOT_OFFLINE: 'Robot is offline. Please check the connection.',
  BATTERY_LOW: 'Robot battery is low. Please charge before continuing.',
  EMERGENCY_STOP: 'Emergency stop activated. Robot movement disabled.'
} as const

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Successfully logged in',
  LOGOUT_SUCCESS: 'Successfully logged out',
  PROFILE_UPDATED: 'Profile updated successfully',
  PASSWORD_CHANGED: 'Password changed successfully',
  ROBOT_COMMAND_SENT: 'Robot command sent successfully',
  VIDEO_STARTED: 'Video stream started',
  VIDEO_STOPPED: 'Video stream stopped',
  RECORDING_STARTED: 'Recording started',
  RECORDING_STOPPED: 'Recording stopped',
  SNAPSHOT_TAKEN: 'Snapshot captured',
  SETTINGS_SAVED: 'Settings saved successfully'
} as const

// Regular Expressions
export const REGEX_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  IP_ADDRESS: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  FILENAME: /^[a-zA-Z0-9._-]+$/
} as const