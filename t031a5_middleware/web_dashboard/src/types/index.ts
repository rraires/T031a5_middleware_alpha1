// Base types
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// User and Authentication types
export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  permissions: Permission[]
  is_active: boolean
  last_login?: string
  created_at: string
}

export enum UserRole {
  ADMIN = 'admin',
  OPERATOR = 'operator',
  VIEWER = 'viewer'
}

export enum Permission {
  // System permissions
  SYSTEM_READ = 'system:read',
  SYSTEM_WRITE = 'system:write',
  SYSTEM_ADMIN = 'system:admin',
  
  // Robot control permissions
  ROBOT_READ = 'robot:read',
  ROBOT_CONTROL = 'robot:control',
  ROBOT_CONFIG = 'robot:config',
  
  // Video permissions
  VIDEO_VIEW = 'video:view',
  VIDEO_RECORD = 'video:record',
  VIDEO_CONFIG = 'video:config',
  
  // Audio permissions
  AUDIO_LISTEN = 'audio:listen',
  AUDIO_SPEAK = 'audio:speak',
  AUDIO_CONFIG = 'audio:config',
  
  // LED permissions
  LED_VIEW = 'led:view',
  LED_CONTROL = 'led:control',
  
  // Sensor permissions
  SENSOR_READ = 'sensor:read',
  SENSOR_CONFIG = 'sensor:config'
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Robot types
export interface RobotStatus {
  id: string
  name: string
  state: RobotState
  battery_level: number
  temperature: number
  uptime: number
  last_seen: string
  position: Position3D
  orientation: Orientation3D
  velocity: Velocity3D
  is_charging: boolean
  error_code?: string
  error_message?: string
}

export enum RobotState {
  IDLE = 'idle',
  ACTIVE = 'active',
  MOVING = 'moving',
  CHARGING = 'charging',
  ERROR = 'error',
  OFFLINE = 'offline'
}

export interface Position3D {
  x: number
  y: number
  z: number
}

export interface Orientation3D {
  roll: number
  pitch: number
  yaw: number
}

export interface Velocity3D {
  linear: Position3D
  angular: Orientation3D
}

// Motion control types
export interface MotionCommand {
  type: MotionType
  parameters: Record<string, any>
  duration?: number
  priority: CommandPriority
}

export enum MotionType {
  WALK = 'walk',
  RUN = 'run',
  TURN = 'turn',
  STOP = 'stop',
  STAND = 'stand',
  SIT = 'sit',
  LIE_DOWN = 'lie_down',
  CUSTOM = 'custom'
}

export enum CommandPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  EMERGENCY = 'emergency'
}

// Sensor types
export interface SensorData {
  timestamp: string
  sensor_type: SensorType
  values: Record<string, number>
  unit: string
  quality: DataQuality
}

export enum SensorType {
  IMU = 'imu',
  LIDAR = 'lidar',
  CAMERA = 'camera',
  ULTRASONIC = 'ultrasonic',
  TEMPERATURE = 'temperature',
  PRESSURE = 'pressure',
  GPS = 'gps',
  ENCODER = 'encoder',
  FORCE = 'force',
  TOUCH = 'touch'
}

export enum DataQuality {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  FAIR = 'fair',
  POOR = 'poor',
  INVALID = 'invalid'
}

// Video types
export interface VideoStream {
  id: string
  name: string
  url: string
  resolution: VideoResolution
  fps: number
  codec: VideoCodec
  is_active: boolean
  quality: StreamQuality
  latency: number
}

export interface VideoResolution {
  width: number
  height: number
}

export enum VideoCodec {
  H264 = 'h264',
  H265 = 'h265',
  VP8 = 'vp8',
  VP9 = 'vp9',
  AV1 = 'av1'
}

export enum StreamQuality {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  ULTRA = 'ultra'
}

// Audio types
export interface AudioConfig {
  input_device: string
  output_device: string
  sample_rate: number
  channels: number
  bit_depth: number
  volume: number
  muted: boolean
  noise_reduction: boolean
  echo_cancellation: boolean
}

export interface AudioCommand {
  type: AudioCommandType
  text?: string
  volume?: number
  language?: string
  voice?: string
}

export enum AudioCommandType {
  SPEAK = 'speak',
  LISTEN = 'listen',
  STOP = 'stop',
  SET_VOLUME = 'set_volume',
  MUTE = 'mute',
  UNMUTE = 'unmute'
}

// LED types
export interface LEDConfig {
  led_id: string
  color: RGBColor
  brightness: number
  pattern: LEDPattern
  duration?: number
  repeat?: number
}

export interface RGBColor {
  r: number
  g: number
  b: number
}

export enum LEDPattern {
  SOLID = 'solid',
  BLINK = 'blink',
  FADE = 'fade',
  RAINBOW = 'rainbow',
  PULSE = 'pulse',
  WAVE = 'wave',
  CUSTOM = 'custom'
}

// System monitoring types
export interface SystemMetrics {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_usage: NetworkUsage
  temperature: number
  processes: ProcessInfo[]
}

export interface NetworkUsage {
  bytes_sent: number
  bytes_received: number
  packets_sent: number
  packets_received: number
}

export interface ProcessInfo {
  pid: number
  name: string
  cpu_percent: number
  memory_percent: number
  status: ProcessStatus
}

export enum ProcessStatus {
  RUNNING = 'running',
  SLEEPING = 'sleeping',
  STOPPED = 'stopped',
  ZOMBIE = 'zombie'
}

// WebSocket types
export interface WebSocketMessage {
  type: MessageType
  data: any
  timestamp: string
  id?: string
}

export enum MessageType {
  // Connection
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  PING = 'ping',
  PONG = 'pong',
  
  // Robot status
  ROBOT_STATUS = 'robot_status',
  ROBOT_COMMAND = 'robot_command',
  
  // Sensor data
  SENSOR_DATA = 'sensor_data',
  
  // Video streaming
  VIDEO_FRAME = 'video_frame',
  VIDEO_STATUS = 'video_status',
  
  // Audio
  AUDIO_DATA = 'audio_data',
  AUDIO_COMMAND = 'audio_command',
  
  // LED
  LED_STATUS = 'led_status',
  LED_COMMAND = 'led_command',
  
  // System
  SYSTEM_METRICS = 'system_metrics',
  SYSTEM_ALERT = 'system_alert',
  
  // Errors
  ERROR = 'error',
  WARNING = 'warning'
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
  message?: string
  timestamp: string
  request_id: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

// Chart and visualization types
export interface ChartDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface ChartConfig {
  type: ChartType
  title: string
  x_axis: AxisConfig
  y_axis: AxisConfig
  series: SeriesConfig[]
  colors?: string[]
  animation?: boolean
}

export enum ChartType {
  LINE = 'line',
  BAR = 'bar',
  AREA = 'area',
  PIE = 'pie',
  SCATTER = 'scatter',
  GAUGE = 'gauge'
}

export interface AxisConfig {
  label: string
  min?: number
  max?: number
  unit?: string
  format?: string
}

export interface SeriesConfig {
  name: string
  data: ChartDataPoint[]
  color?: string
  type?: ChartType
}

// Theme types
export interface ThemeConfig {
  mode: ThemeMode
  primary_color: string
  secondary_color: string
  accent_color: string
  font_family: string
  font_size: FontSize
  border_radius: BorderRadius
  animations: boolean
}

export enum ThemeMode {
  LIGHT = 'light',
  DARK = 'dark',
  AUTO = 'auto'
}

export enum FontSize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large'
}

export enum BorderRadius {
  NONE = 'none',
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large'
}

// Settings types
export interface DashboardSettings {
  theme: ThemeConfig
  notifications: NotificationSettings
  dashboard: DashboardConfig
  robot: RobotSettings
  video: VideoSettings
  audio: AudioSettings
}

export interface NotificationSettings {
  enabled: boolean
  sound: boolean
  desktop: boolean
  email: boolean
  types: NotificationType[]
}

export enum NotificationType {
  ROBOT_STATUS = 'robot_status',
  SYSTEM_ALERT = 'system_alert',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface DashboardConfig {
  auto_refresh: boolean
  refresh_interval: number
  show_grid: boolean
  compact_mode: boolean
  widgets: WidgetConfig[]
}

export interface WidgetConfig {
  id: string
  type: WidgetType
  position: WidgetPosition
  size: WidgetSize
  config: Record<string, any>
  visible: boolean
}

export enum WidgetType {
  ROBOT_STATUS = 'robot_status',
  SENSOR_CHART = 'sensor_chart',
  VIDEO_STREAM = 'video_stream',
  SYSTEM_METRICS = 'system_metrics',
  QUICK_CONTROLS = 'quick_controls',
  ALERTS = 'alerts'
}

export interface WidgetPosition {
  x: number
  y: number
}

export interface WidgetSize {
  width: number
  height: number
}

export interface RobotSettings {
  default_speed: number
  safety_limits: SafetyLimits
  auto_standby: boolean
  standby_timeout: number
}

export interface SafetyLimits {
  max_speed: number
  max_acceleration: number
  min_battery_level: number
  max_temperature: number
}

export interface VideoSettings {
  default_resolution: VideoResolution
  default_fps: number
  default_quality: StreamQuality
  auto_record: boolean
  storage_path: string
}

export interface AudioSettings {
  default_volume: number
  voice: string
  language: string
  speech_rate: number
  auto_listen: boolean
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

export type Timestamp = string

export type ID = string

export type Color = string

export type Percentage = number // 0-100

export type Milliseconds = number

export type Seconds = number