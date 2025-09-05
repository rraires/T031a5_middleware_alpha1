/**
 * Utility functions for formatting data
 */

/**
 * Format file size in bytes to human readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Format duration in seconds to human readable format
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  
  if (minutes < 60) {
    return remainingSeconds > 0 
      ? `${minutes}m ${remainingSeconds}s`
      : `${minutes}m`
  }
  
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  
  if (hours < 24) {
    return remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`
  }
  
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  
  return remainingHours > 0
    ? `${days}d ${remainingHours}h`
    : `${days}d`
}

/**
 * Format uptime in milliseconds to human readable format
 */
export const formatUptime = (uptimeMs: number): string => {
  return formatDuration(uptimeMs / 1000)
}

/**
 * Format timestamp to local date and time
 */
export const formatDateTime = (timestamp: number | string | Date): string => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

/**
 * Format timestamp to local date only
 */
export const formatDate = (timestamp: number | string | Date): string => {
  const date = new Date(timestamp)
  return date.toLocaleDateString()
}

/**
 * Format timestamp to local time only
 */
export const formatTime = (timestamp: number | string | Date): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

/**
 * Format timestamp to relative time (e.g., "2 minutes ago")
 */
export const formatRelativeTime = (timestamp: number | string | Date): string => {
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffSeconds < 60) {
    return diffSeconds <= 1 ? 'just now' : `${diffSeconds} seconds ago`
  }
  
  if (diffMinutes < 60) {
    return diffMinutes === 1 ? '1 minute ago' : `${diffMinutes} minutes ago`
  }
  
  if (diffHours < 24) {
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`
  }
  
  if (diffDays < 7) {
    return diffDays === 1 ? '1 day ago' : `${diffDays} days ago`
  }
  
  return formatDate(timestamp)
}

/**
 * Format number to percentage
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`
}

/**
 * Format number with thousand separators
 */
export const formatNumber = (value: number, decimals?: number): string => {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format currency value
 */
export const formatCurrency = (value: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency
  }).format(value)
}

/**
 * Format coordinates to string
 */
export const formatCoordinates = (x: number, y: number, z?: number): string => {
  if (z !== undefined) {
    return `(${x.toFixed(2)}, ${y.toFixed(2)}, ${z.toFixed(2)})`
  }
  return `(${x.toFixed(2)}, ${y.toFixed(2)})`
}

/**
 * Format angle in radians to degrees
 */
export const formatAngle = (radians: number, unit: 'deg' | 'rad' = 'deg'): string => {
  if (unit === 'deg') {
    const degrees = (radians * 180) / Math.PI
    return `${degrees.toFixed(1)}°`
  }
  return `${radians.toFixed(3)} rad`
}

/**
 * Format velocity vector
 */
export const formatVelocity = (vx: number, vy: number, vz?: number, unit: string = 'm/s'): string => {
  if (vz !== undefined) {
    return `(${vx.toFixed(2)}, ${vy.toFixed(2)}, ${vz.toFixed(2)}) ${unit}`
  }
  return `(${vx.toFixed(2)}, ${vy.toFixed(2)}) ${unit}`
}

/**
 * Format temperature
 */
export const formatTemperature = (celsius: number, unit: 'C' | 'F' = 'C'): string => {
  if (unit === 'F') {
    const fahrenheit = (celsius * 9/5) + 32
    return `${fahrenheit.toFixed(1)}°F`
  }
  return `${celsius.toFixed(1)}°C`
}

/**
 * Format battery level with appropriate styling
 */
export const formatBatteryLevel = (percentage: number): { text: string; color: string; icon: string } => {
  const text = `${percentage.toFixed(0)}%`
  
  if (percentage > 75) {
    return { text, color: 'text-green-600', icon: 'battery-full' }
  } else if (percentage > 50) {
    return { text, color: 'text-yellow-600', icon: 'battery-half' }
  } else if (percentage > 25) {
    return { text, color: 'text-orange-600', icon: 'battery-low' }
  } else {
    return { text, color: 'text-red-600', icon: 'battery-critical' }
  }
}

/**
 * Format status with appropriate styling
 */
export const formatStatus = (status: string): { text: string; color: string; bgColor: string } => {
  const statusLower = status.toLowerCase()
  
  switch (statusLower) {
    case 'online':
    case 'connected':
    case 'active':
    case 'running':
      return {
        text: status,
        color: 'text-green-700',
        bgColor: 'bg-green-100'
      }
    
    case 'offline':
    case 'disconnected':
    case 'inactive':
    case 'stopped':
      return {
        text: status,
        color: 'text-gray-700',
        bgColor: 'bg-gray-100'
      }
    
    case 'error':
    case 'failed':
    case 'critical':
      return {
        text: status,
        color: 'text-red-700',
        bgColor: 'bg-red-100'
      }
    
    case 'warning':
    case 'caution':
      return {
        text: status,
        color: 'text-yellow-700',
        bgColor: 'bg-yellow-100'
      }
    
    case 'charging':
    case 'loading':
    case 'processing':
      return {
        text: status,
        color: 'text-blue-700',
        bgColor: 'bg-blue-100'
      }
    
    default:
      return {
        text: status,
        color: 'text-gray-700',
        bgColor: 'bg-gray-100'
      }
  }
}

/**
 * Format robot mode with appropriate styling
 */
export const formatRobotMode = (mode: string): { text: string; color: string } => {
  const modeLower = mode.toLowerCase()
  
  switch (modeLower) {
    case 'idle':
      return { text: 'Idle', color: 'text-gray-600' }
    case 'walking':
    case 'moving':
      return { text: 'Moving', color: 'text-blue-600' }
    case 'running':
      return { text: 'Running', color: 'text-green-600' }
    case 'sitting':
      return { text: 'Sitting', color: 'text-yellow-600' }
    case 'lying':
    case 'lying_down':
      return { text: 'Lying Down', color: 'text-purple-600' }
    case 'charging':
      return { text: 'Charging', color: 'text-blue-600' }
    case 'error':
      return { text: 'Error', color: 'text-red-600' }
    default:
      return { text: mode, color: 'text-gray-600' }
  }
}

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}

/**
 * Capitalize first letter of each word
 */
export const capitalizeWords = (text: string): string => {
  return text.replace(/\b\w/g, char => char.toUpperCase())
}

/**
 * Convert camelCase to Title Case
 */
export const camelToTitle = (text: string): string => {
  return text
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

/**
 * Convert snake_case to Title Case
 */
export const snakeToTitle = (text: string): string => {
  return text
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}