import { useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useWebSocketStore } from '../stores/websocketStore'
import { robotService } from '../services/robotService'
import { RobotState, MotionCommand, SystemMetrics, SensorData } from '../types'
import toast from 'react-hot-toast'

/**
 * Hook for robot status and control
 */
export const useRobot = () => {
  const queryClient = useQueryClient()
  const { robotStatus, sensorData, systemMetrics } = useWebSocketStore()

  // Robot status query
  const statusQuery = useQuery({
    queryKey: ['robot', 'status'],
    queryFn: async () => {
      const response = await robotService.getStatus()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get robot status')
      }
      return response.data!
    },
    refetchInterval: robotStatus ? undefined : 5000, // Poll if no WebSocket data
    staleTime: 2000,
    retry: 3
  })

  // System metrics query
  const metricsQuery = useQuery({
    queryKey: ['robot', 'metrics'],
    queryFn: async () => {
      const response = await robotService.getSystemMetrics()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get system metrics')
      }
      return response.data!
    },
    refetchInterval: systemMetrics ? undefined : 10000, // Poll if no WebSocket data
    staleTime: 5000,
    retry: 3
  })

  // Sensor data query
  const sensorsQuery = useQuery({
    queryKey: ['robot', 'sensors'],
    queryFn: async () => {
      const response = await robotService.getSensorData()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get sensor data')
      }
      return response.data!
    },
    refetchInterval: sensorData.length > 0 ? undefined : 3000, // Poll if no WebSocket data
    staleTime: 1000,
    retry: 3
  })

  // Motion command mutation
  const motionMutation = useMutation({
    mutationFn: async (command: MotionCommand) => {
      const response = await robotService.sendMotionCommand(command)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to send motion command')
      }
      return response.data!
    },
    onSuccess: (data) => {
      toast.success(`Motion command ${data.status}`)
      // Invalidate status to get updated state
      queryClient.invalidateQueries({ queryKey: ['robot', 'status'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Emergency stop mutation
  const emergencyStopMutation = useMutation({
    mutationFn: async () => {
      const response = await robotService.emergencyStop()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to execute emergency stop')
      }
      return response.data!
    },
    onSuccess: () => {
      toast.success('Emergency stop executed!')
      queryClient.invalidateQueries({ queryKey: ['robot', 'status'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Calibration mutation
  const calibrationMutation = useMutation({
    mutationFn: async () => {
      const response = await robotService.startCalibration()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to start calibration')
      }
      return response.data!
    },
    onSuccess: (data) => {
      toast.success('Calibration started')
      // Start polling calibration status
      queryClient.invalidateQueries({ queryKey: ['robot', 'calibration'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Power state mutation
  const powerMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await robotService.setPowerState(enabled)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to set power state')
      }
    },
    onSuccess: (_, enabled) => {
      toast.success(`Robot ${enabled ? 'powered on' : 'powered off'}`)
      queryClient.invalidateQueries({ queryKey: ['robot', 'status'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Reset position mutation
  const resetPositionMutation = useMutation({
    mutationFn: async () => {
      const response = await robotService.resetPosition()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to reset position')
      }
      return response.data!
    },
    onSuccess: () => {
      toast.success('Position reset')
      queryClient.invalidateQueries({ queryKey: ['robot', 'status'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Helper functions
  const sendMotionCommand = useCallback((command: MotionCommand) => {
    motionMutation.mutate(command)
  }, [motionMutation])

  const emergencyStop = useCallback(() => {
    emergencyStopMutation.mutate()
  }, [emergencyStopMutation])

  const startCalibration = useCallback(() => {
    calibrationMutation.mutate()
  }, [calibrationMutation])

  const setPowerState = useCallback((enabled: boolean) => {
    powerMutation.mutate(enabled)
  }, [powerMutation])

  const resetPosition = useCallback(() => {
    resetPositionMutation.mutate()
  }, [resetPositionMutation])

  // Movement helpers
  const moveForward = useCallback((distance: number = 1.0, speed: number = 0.5) => {
    sendMotionCommand({
      type: 'walk',
      parameters: {
        direction: 'forward',
        distance,
        speed
      },
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const moveBackward = useCallback((distance: number = 1.0, speed: number = 0.5) => {
    sendMotionCommand({
      type: 'walk',
      parameters: {
        direction: 'backward',
        distance,
        speed
      },
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const turnLeft = useCallback((angle: number = 90, speed: number = 0.5) => {
    sendMotionCommand({
      type: 'turn',
      parameters: {
        direction: 'left',
        angle,
        speed
      },
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const turnRight = useCallback((angle: number = 90, speed: number = 0.5) => {
    sendMotionCommand({
      type: 'turn',
      parameters: {
        direction: 'right',
        angle,
        speed
      },
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const sit = useCallback(() => {
    sendMotionCommand({
      type: 'sit',
      parameters: {},
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const stand = useCallback(() => {
    sendMotionCommand({
      type: 'stand',
      parameters: {},
      priority: 'normal'
    })
  }, [sendMotionCommand])

  const layDown = useCallback(() => {
    sendMotionCommand({
      type: 'lie_down',
      parameters: {},
      priority: 'normal'
    })
  }, [sendMotionCommand])

  // Status helpers
  const currentStatus = robotStatus || statusQuery.data?.status
  const currentMetrics = systemMetrics || metricsQuery.data?.metrics
  const currentSensors = sensorData.length > 0 ? sensorData : sensorsQuery.data?.sensors || []

  const isOnline = useCallback(() => {
    return currentStatus ? robotService.isRobotOnline(currentStatus) : false
  }, [currentStatus])

  const isMoving = useCallback(() => {
    return currentStatus ? robotService.isRobotMoving(currentStatus) : false
  }, [currentStatus])

  const hasErrors = useCallback(() => {
    return currentStatus ? robotService.hasErrors(currentStatus) : false
  }, [currentStatus])

  const getBatteryLevel = useCallback(() => {
    return currentStatus ? robotService.getBatteryPercentage(currentStatus) : 0
  }, [currentStatus])

  const getUptime = useCallback(() => {
    return currentStatus ? robotService.getUptime(currentStatus) : 0
  }, [currentStatus])

  const getStatusColor = useCallback(() => {
    return currentStatus ? robotService.getStatusColor(currentStatus) : 'gray'
  }, [currentStatus])

  const getStatusText = useCallback(() => {
    return currentStatus ? robotService.getStatusText(currentStatus) : 'Unknown'
  }, [currentStatus])

  const getFormattedUptime = useCallback(() => {
    const uptime = getUptime()
    return robotService.formatUptime(uptime)
  }, [getUptime])

  return {
    // Data (prefer WebSocket data over API data)
    status: currentStatus,
    metrics: currentMetrics,
    sensors: currentSensors,
    
    // Loading states
    isLoading: statusQuery.isLoading || metricsQuery.isLoading || sensorsQuery.isLoading,
    isStatusLoading: statusQuery.isLoading,
    isMetricsLoading: metricsQuery.isLoading,
    isSensorsLoading: sensorsQuery.isLoading,
    
    // Error states
    statusError: statusQuery.error,
    metricsError: metricsQuery.error,
    sensorsError: sensorsQuery.error,
    
    // Actions
    sendMotionCommand,
    emergencyStop,
    startCalibration,
    setPowerState,
    resetPosition,
    
    // Movement helpers
    moveForward,
    moveBackward,
    turnLeft,
    turnRight,
    sit,
    stand,
    layDown,
    
    // Action states
    isSendingCommand: motionMutation.isPending,
    isExecutingEmergencyStop: emergencyStopMutation.isPending,
    isStartingCalibration: calibrationMutation.isPending,
    isSettingPower: powerMutation.isPending,
    isResettingPosition: resetPositionMutation.isPending,
    
    // Status helpers
    isOnline,
    isMoving,
    hasErrors,
    getBatteryLevel,
    getUptime,
    getStatusColor,
    getStatusText,
    getFormattedUptime,
    
    // Refresh functions
    refreshStatus: statusQuery.refetch,
    refreshMetrics: metricsQuery.refetch,
    refreshSensors: sensorsQuery.refetch
  }
}

/**
 * Hook for specific sensor data
 */
export const useSensorData = (sensorType?: string) => {
  const { sensors } = useRobot()
  
  const filteredSensors = sensorType 
    ? sensors.filter(sensor => sensor.type === sensorType)
    : sensors
    
  return {
    sensors: filteredSensors,
    latestReading: filteredSensors[0] || null,
    hasData: filteredSensors.length > 0
  }
}

/**
 * Hook for battery monitoring
 */
export const useBattery = () => {
  const { status, getBatteryLevel } = useRobot()
  
  const batteryLevel = getBatteryLevel()
  const isLowBattery = batteryLevel < 20
  const isCriticalBattery = batteryLevel < 10
  const isCharging = status?.charging_state === 'charging'
  
  // Show warning for low battery
  useEffect(() => {
    if (isCriticalBattery && !isCharging) {
      toast.error('Critical battery level! Please charge the robot.', {
        duration: 10000,
        id: 'critical-battery'
      })
    } else if (isLowBattery && !isCharging) {
      toast.warning('Low battery level. Consider charging soon.', {
        duration: 5000,
        id: 'low-battery'
      })
    }
  }, [isCriticalBattery, isLowBattery, isCharging])
  
  return {
    batteryLevel,
    isLowBattery,
    isCriticalBattery,
    isCharging,
    chargingState: status?.charging_state || 'unknown'
  }
}

/**
 * Hook for robot movement state
 */
export const useMovement = () => {
  const { status, isMoving, sendMotionCommand } = useRobot()
  
  const canMove = status?.motion_state !== 'error' && status?.connection_status === 'connected'
  const currentPosition = status?.position
  const currentOrientation = status?.orientation
  const currentVelocity = status?.velocity
  
  return {
    isMoving: isMoving(),
    canMove,
    currentPosition,
    currentOrientation,
    currentVelocity,
    motionState: status?.motion_state || 'unknown',
    sendCommand: sendMotionCommand
  }
}