import { ApiResponse, RobotState, MotionCommand, SystemMetrics, SensorData } from '../types'
import { apiClient } from './apiClient'

interface RobotStatusResponse {
  status: RobotState
  last_updated: string
}

interface SystemMetricsResponse {
  metrics: SystemMetrics
  timestamp: string
}

interface SensorDataResponse {
  sensors: SensorData[]
  timestamp: string
}

interface MotionCommandResponse {
  command_id: string
  status: 'accepted' | 'rejected' | 'executing' | 'completed' | 'failed'
  message?: string
}

interface EmergencyStopResponse {
  stopped: boolean
  timestamp: string
}

interface CalibrationResponse {
  calibration_id: string
  status: 'started' | 'in_progress' | 'completed' | 'failed'
  progress?: number
  message?: string
}

class RobotService {
  private readonly baseUrl = '/api/robot'

  /**
   * Get current robot status
   */
  async getStatus(): Promise<ApiResponse<RobotStatusResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<RobotStatusResponse>>(
        `${this.baseUrl}/status`
      )
      return response.data
    } catch (error: any) {
      console.error('Get robot status error:', error)
      return {
        success: false,
        error: {
          code: 'GET_STATUS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get robot status'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get system metrics
   */
  async getSystemMetrics(): Promise<ApiResponse<SystemMetricsResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<SystemMetricsResponse>>(
        `${this.baseUrl}/metrics`
      )
      return response.data
    } catch (error: any) {
      console.error('Get system metrics error:', error)
      return {
        success: false,
        error: {
          code: 'GET_METRICS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get system metrics'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get sensor data
   */
  async getSensorData(sensorTypes?: string[]): Promise<ApiResponse<SensorDataResponse>> {
    try {
      const params = sensorTypes ? { types: sensorTypes.join(',') } : {}
      const response = await apiClient.get<ApiResponse<SensorDataResponse>>(
        `${this.baseUrl}/sensors`,
        { params }
      )
      return response.data
    } catch (error: any) {
      console.error('Get sensor data error:', error)
      return {
        success: false,
        error: {
          code: 'GET_SENSORS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get sensor data'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Send motion command to robot
   */
  async sendMotionCommand(command: MotionCommand): Promise<ApiResponse<MotionCommandResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<MotionCommandResponse>>(
        `${this.baseUrl}/motion`,
        command
      )
      return response.data
    } catch (error: any) {
      console.error('Send motion command error:', error)
      return {
        success: false,
        error: {
          code: 'MOTION_COMMAND_FAILED',
          message: error.response?.data?.error?.message || 'Failed to send motion command'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Emergency stop robot
   */
  async emergencyStop(): Promise<ApiResponse<EmergencyStopResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<EmergencyStopResponse>>(
        `${this.baseUrl}/emergency-stop`
      )
      return response.data
    } catch (error: any) {
      console.error('Emergency stop error:', error)
      return {
        success: false,
        error: {
          code: 'EMERGENCY_STOP_FAILED',
          message: error.response?.data?.error?.message || 'Failed to execute emergency stop'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Start robot calibration
   */
  async startCalibration(): Promise<ApiResponse<CalibrationResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<CalibrationResponse>>(
        `${this.baseUrl}/calibration/start`
      )
      return response.data
    } catch (error: any) {
      console.error('Start calibration error:', error)
      return {
        success: false,
        error: {
          code: 'CALIBRATION_START_FAILED',
          message: error.response?.data?.error?.message || 'Failed to start calibration'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get calibration status
   */
  async getCalibrationStatus(calibrationId: string): Promise<ApiResponse<CalibrationResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<CalibrationResponse>>(
        `${this.baseUrl}/calibration/${calibrationId}`
      )
      return response.data
    } catch (error: any) {
      console.error('Get calibration status error:', error)
      return {
        success: false,
        error: {
          code: 'GET_CALIBRATION_STATUS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get calibration status'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Cancel calibration
   */
  async cancelCalibration(calibrationId: string): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `${this.baseUrl}/calibration/${calibrationId}/cancel`
      )
      return response.data
    } catch (error: any) {
      console.error('Cancel calibration error:', error)
      return {
        success: false,
        error: {
          code: 'CANCEL_CALIBRATION_FAILED',
          message: error.response?.data?.error?.message || 'Failed to cancel calibration'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Set robot power state
   */
  async setPowerState(enabled: boolean): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `${this.baseUrl}/power`,
        { enabled }
      )
      return response.data
    } catch (error: any) {
      console.error('Set power state error:', error)
      return {
        success: false,
        error: {
          code: 'SET_POWER_FAILED',
          message: error.response?.data?.error?.message || 'Failed to set power state'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Reset robot to default position
   */
  async resetPosition(): Promise<ApiResponse<MotionCommandResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<MotionCommandResponse>>(
        `${this.baseUrl}/reset-position`
      )
      return response.data
    } catch (error: any) {
      console.error('Reset position error:', error)
      return {
        success: false,
        error: {
          code: 'RESET_POSITION_FAILED',
          message: error.response?.data?.error?.message || 'Failed to reset position'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get robot configuration
   */
  async getConfiguration(): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get<ApiResponse<any>>(
        `${this.baseUrl}/config`
      )
      return response.data
    } catch (error: any) {
      console.error('Get configuration error:', error)
      return {
        success: false,
        error: {
          code: 'GET_CONFIG_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get configuration'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Update robot configuration
   */
  async updateConfiguration(config: any): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.put<ApiResponse<void>>(
        `${this.baseUrl}/config`,
        config
      )
      return response.data
    } catch (error: any) {
      console.error('Update configuration error:', error)
      return {
        success: false,
        error: {
          code: 'UPDATE_CONFIG_FAILED',
          message: error.response?.data?.error?.message || 'Failed to update configuration'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get robot logs
   */
  async getLogs(
    level?: string,
    limit?: number,
    offset?: number
  ): Promise<ApiResponse<any>> {
    try {
      const params: any = {}
      if (level) params.level = level
      if (limit) params.limit = limit
      if (offset) params.offset = offset
      
      const response = await apiClient.get<ApiResponse<any>>(
        `${this.baseUrl}/logs`,
        { params }
      )
      return response.data
    } catch (error: any) {
      console.error('Get logs error:', error)
      return {
        success: false,
        error: {
          code: 'GET_LOGS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get logs'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Clear robot logs
   */
  async clearLogs(): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `${this.baseUrl}/logs`
      )
      return response.data
    } catch (error: any) {
      console.error('Clear logs error:', error)
      return {
        success: false,
        error: {
          code: 'CLEAR_LOGS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to clear logs'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get robot health status
   */
  async getHealthStatus(): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get<ApiResponse<any>>(
        `${this.baseUrl}/health`
      )
      return response.data
    } catch (error: any) {
      console.error('Get health status error:', error)
      return {
        success: false,
        error: {
          code: 'GET_HEALTH_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get health status'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Utility methods
   */
  
  /**
   * Check if robot is online
   */
  isRobotOnline(status: RobotState): boolean {
    return status.connection_status === 'connected'
  }

  /**
   * Check if robot is moving
   */
  isRobotMoving(status: RobotState): boolean {
    return status.motion_state === 'moving'
  }

  /**
   * Check if robot has errors
   */
  hasErrors(status: RobotState): boolean {
    return status.error_state !== 'none' || status.errors.length > 0
  }

  /**
   * Get battery percentage
   */
  getBatteryPercentage(status: RobotState): number {
    return status.battery_level
  }

  /**
   * Get robot uptime in seconds
   */
  getUptime(status: RobotState): number {
    return status.uptime
  }

  /**
   * Format uptime as human readable string
   */
  formatUptime(uptimeSeconds: number): string {
    const hours = Math.floor(uptimeSeconds / 3600)
    const minutes = Math.floor((uptimeSeconds % 3600) / 60)
    const seconds = uptimeSeconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  }

  /**
   * Get status color for UI
   */
  getStatusColor(status: RobotState): string {
    if (!this.isRobotOnline(status)) return 'red'
    if (this.hasErrors(status)) return 'red'
    if (this.isRobotMoving(status)) return 'blue'
    return 'green'
  }

  /**
   * Get status text for UI
   */
  getStatusText(status: RobotState): string {
    if (!this.isRobotOnline(status)) return 'Offline'
    if (this.hasErrors(status)) return 'Error'
    if (this.isRobotMoving(status)) return 'Moving'
    return 'Online'
  }
}

export const robotService = new RobotService()