/**
 * Utility functions for data validation
 */

/**
 * Email validation
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Password strength validation
 */
export const validatePassword = (password: string): {
  isValid: boolean
  errors: string[]
  strength: 'weak' | 'medium' | 'strong'
} => {
  const errors: string[] = []
  let score = 0

  // Length check
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  } else {
    score += 1
  }

  // Uppercase check
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  } else {
    score += 1
  }

  // Lowercase check
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  } else {
    score += 1
  }

  // Number check
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number')
  } else {
    score += 1
  }

  // Special character check
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character')
  } else {
    score += 1
  }

  // Determine strength
  let strength: 'weak' | 'medium' | 'strong'
  if (score < 3) {
    strength = 'weak'
  } else if (score < 5) {
    strength = 'medium'
  } else {
    strength = 'strong'
  }

  return {
    isValid: errors.length === 0,
    errors,
    strength
  }
}

/**
 * URL validation
 */
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * IP address validation
 */
export const isValidIP = (ip: string): boolean => {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

/**
 * Port number validation
 */
export const isValidPort = (port: number | string): boolean => {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535
}

/**
 * Coordinate validation
 */
export const isValidCoordinate = (value: number, min?: number, max?: number): boolean => {
  if (isNaN(value) || !isFinite(value)) {
    return false
  }
  
  if (min !== undefined && value < min) {
    return false
  }
  
  if (max !== undefined && value > max) {
    return false
  }
  
  return true
}

/**
 * Angle validation (in radians)
 */
export const isValidAngle = (angle: number): boolean => {
  return isValidCoordinate(angle, -Math.PI * 2, Math.PI * 2)
}

/**
 * Percentage validation
 */
export const isValidPercentage = (value: number): boolean => {
  return isValidCoordinate(value, 0, 100)
}

/**
 * Speed validation
 */
export const isValidSpeed = (speed: number, maxSpeed: number = 10): boolean => {
  return isValidCoordinate(speed, 0, maxSpeed)
}

/**
 * Distance validation
 */
export const isValidDistance = (distance: number, maxDistance: number = 100): boolean => {
  return isValidCoordinate(distance, 0, maxDistance)
}

/**
 * File size validation
 */
export const isValidFileSize = (size: number, maxSizeMB: number = 100): boolean => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024
  return size > 0 && size <= maxSizeBytes
}

/**
 * File type validation
 */
export const isValidFileType = (filename: string, allowedTypes: string[]): boolean => {
  const extension = filename.split('.').pop()?.toLowerCase()
  return extension ? allowedTypes.includes(extension) : false
}

/**
 * Video file validation
 */
export const isValidVideoFile = (filename: string): boolean => {
  const videoTypes = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv']
  return isValidFileType(filename, videoTypes)
}

/**
 * Image file validation
 */
export const isValidImageFile = (filename: string): boolean => {
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  return isValidFileType(filename, imageTypes)
}

/**
 * Audio file validation
 */
export const isValidAudioFile = (filename: string): boolean => {
  const audioTypes = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a']
  return isValidFileType(filename, audioTypes)
}

/**
 * JSON validation
 */
export const isValidJSON = (str: string): boolean => {
  try {
    JSON.parse(str)
    return true
  } catch {
    return false
  }
}

/**
 * Robot command validation
 */
export const validateRobotCommand = (command: any): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // Check required fields
  if (!command.type) {
    errors.push('Command type is required')
  }

  if (!command.parameters) {
    errors.push('Command parameters are required')
  }

  // Validate specific command types
  if (command.type === 'walk') {
    if (!command.parameters.direction) {
      errors.push('Walk direction is required')
    }
    
    if (command.parameters.distance !== undefined && !isValidDistance(command.parameters.distance)) {
      errors.push('Invalid walk distance')
    }
    
    if (command.parameters.speed !== undefined && !isValidSpeed(command.parameters.speed)) {
      errors.push('Invalid walk speed')
    }
  }

  if (command.type === 'turn') {
    if (!command.parameters.direction) {
      errors.push('Turn direction is required')
    }
    
    if (command.parameters.angle !== undefined && !isValidAngle(command.parameters.angle * Math.PI / 180)) {
      errors.push('Invalid turn angle')
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Video configuration validation
 */
export const validateVideoConfig = (config: any): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // Resolution validation
  if (config.resolution) {
    if (!config.resolution.width || !config.resolution.height) {
      errors.push('Resolution width and height are required')
    } else {
      if (config.resolution.width < 320 || config.resolution.width > 4096) {
        errors.push('Resolution width must be between 320 and 4096')
      }
      if (config.resolution.height < 240 || config.resolution.height > 2160) {
        errors.push('Resolution height must be between 240 and 2160')
      }
    }
  }

  // Frame rate validation
  if (config.framerate !== undefined) {
    if (config.framerate < 1 || config.framerate > 60) {
      errors.push('Frame rate must be between 1 and 60 fps')
    }
  }

  // Bitrate validation
  if (config.bitrate !== undefined) {
    if (config.bitrate < 100 || config.bitrate > 50000) {
      errors.push('Bitrate must be between 100 and 50000 kbps')
    }
  }

  // Quality validation
  if (config.quality !== undefined) {
    if (!['low', 'medium', 'high', 'ultra'].includes(config.quality)) {
      errors.push('Quality must be one of: low, medium, high, ultra')
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Audio configuration validation
 */
export const validateAudioConfig = (config: any): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // Volume validation
  if (config.volume !== undefined && !isValidPercentage(config.volume)) {
    errors.push('Volume must be between 0 and 100')
  }

  // Sample rate validation
  if (config.sampleRate !== undefined) {
    const validRates = [8000, 16000, 22050, 44100, 48000]
    if (!validRates.includes(config.sampleRate)) {
      errors.push('Sample rate must be one of: 8000, 16000, 22050, 44100, 48000')
    }
  }

  // Channels validation
  if (config.channels !== undefined) {
    if (config.channels < 1 || config.channels > 8) {
      errors.push('Channels must be between 1 and 8')
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * LED configuration validation
 */
export const validateLEDConfig = (config: any): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // Color validation
  if (config.color) {
    if (config.color.r !== undefined && !isValidCoordinate(config.color.r, 0, 255)) {
      errors.push('Red color value must be between 0 and 255')
    }
    if (config.color.g !== undefined && !isValidCoordinate(config.color.g, 0, 255)) {
      errors.push('Green color value must be between 0 and 255')
    }
    if (config.color.b !== undefined && !isValidCoordinate(config.color.b, 0, 255)) {
      errors.push('Blue color value must be between 0 and 255')
    }
  }

  // Brightness validation
  if (config.brightness !== undefined && !isValidPercentage(config.brightness)) {
    errors.push('Brightness must be between 0 and 100')
  }

  // Pattern validation
  if (config.pattern && !['solid', 'blink', 'fade', 'rainbow', 'pulse'].includes(config.pattern)) {
    errors.push('Pattern must be one of: solid, blink, fade, rainbow, pulse')
  }

  // Speed validation (for patterns)
  if (config.speed !== undefined && !isValidCoordinate(config.speed, 0.1, 10)) {
    errors.push('Pattern speed must be between 0.1 and 10')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Form validation helper
 */
export const validateForm = (data: Record<string, any>, rules: Record<string, any>): {
  isValid: boolean
  errors: Record<string, string[]>
} => {
  const errors: Record<string, string[]> = {}

  Object.keys(rules).forEach(field => {
    const value = data[field]
    const rule = rules[field]
    const fieldErrors: string[] = []

    // Required validation
    if (rule.required && (value === undefined || value === null || value === '')) {
      fieldErrors.push(`${field} is required`)
    }

    // Skip other validations if field is empty and not required
    if (!rule.required && (value === undefined || value === null || value === '')) {
      return
    }

    // Type validation
    if (rule.type) {
      switch (rule.type) {
        case 'email':
          if (!isValidEmail(value)) {
            fieldErrors.push('Invalid email format')
          }
          break
        case 'url':
          if (!isValidUrl(value)) {
            fieldErrors.push('Invalid URL format')
          }
          break
        case 'number':
          if (isNaN(Number(value))) {
            fieldErrors.push('Must be a valid number')
          }
          break
      }
    }

    // Length validation
    if (rule.minLength && value.length < rule.minLength) {
      fieldErrors.push(`Must be at least ${rule.minLength} characters`)
    }
    if (rule.maxLength && value.length > rule.maxLength) {
      fieldErrors.push(`Must be no more than ${rule.maxLength} characters`)
    }

    // Range validation
    if (rule.min !== undefined && Number(value) < rule.min) {
      fieldErrors.push(`Must be at least ${rule.min}`)
    }
    if (rule.max !== undefined && Number(value) > rule.max) {
      fieldErrors.push(`Must be no more than ${rule.max}`)
    }

    // Custom validation
    if (rule.validator && typeof rule.validator === 'function') {
      const customResult = rule.validator(value)
      if (customResult !== true) {
        fieldErrors.push(customResult || 'Invalid value')
      }
    }

    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors
    }
  })

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}