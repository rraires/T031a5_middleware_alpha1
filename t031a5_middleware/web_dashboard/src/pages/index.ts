// Export all pages
export { Dashboard } from './Dashboard'
export { Control } from './Control'
export { Video } from './Video'
export { default as Sensors } from './Sensors'
export { Settings } from './Settings'

// Re-export common types for convenience
export type {
  User,
  Robot,
  SensorData,
  VideoConfig,
  AudioConfig,
  LEDConfig
} from '../types'