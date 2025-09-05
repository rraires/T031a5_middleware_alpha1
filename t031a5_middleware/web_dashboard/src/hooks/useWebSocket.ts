import { useEffect, useCallback, useRef } from 'react'
import { useWebSocketStore } from '../stores/websocketStore'
import { WebSocketMessage, MessageType } from '../types'
import toast from 'react-hot-toast'

/**
 * Hook for WebSocket connection management
 */
export const useWebSocket = () => {
  const {
    socket,
    isConnected,
    isConnecting,
    error,
    lastMessage,
    robotStatus,
    sensorData,
    systemMetrics,
    connect,
    disconnect,
    reconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    clearError,
    clearSensorData,
    clearSystemMetrics
  } = useWebSocketStore()

  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>()
  const connectionAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  // Auto-connect on mount
  useEffect(() => {
    if (!isConnected && !isConnecting && !error) {
      connect()
    }
  }, [])

  // Handle connection errors with auto-reconnect
  useEffect(() => {
    if (error && !isConnecting) {
      console.error('WebSocket error:', error)
      
      if (connectionAttemptsRef.current < maxReconnectAttempts) {
        connectionAttemptsRef.current++
        
        toast.error(`Connection lost. Reconnecting... (${connectionAttemptsRef.current}/${maxReconnectAttempts})`, {
          id: 'websocket-reconnect'
        })
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnect()
        }, reconnectDelay * connectionAttemptsRef.current)
      } else {
        toast.error('Failed to connect to robot. Please check your connection.', {
          duration: 10000,
          id: 'websocket-failed'
        })
      }
    }
  }, [error, isConnecting, reconnect])

  // Reset connection attempts on successful connection
  useEffect(() => {
    if (isConnected) {
      connectionAttemptsRef.current = 0
      toast.dismiss('websocket-reconnect')
      toast.dismiss('websocket-failed')
      toast.success('Connected to robot', {
        duration: 3000,
        id: 'websocket-connected'
      })
    }
  }, [isConnected])

  // Setup heartbeat when connected
  useEffect(() => {
    if (isConnected && socket) {
      // Send ping every 30 seconds
      heartbeatIntervalRef.current = setInterval(() => {
        sendMessage({
          type: 'ping',
          data: { timestamp: Date.now() }
        })
      }, 30000)

      return () => {
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
        }
      }
    }
  }, [isConnected, socket, sendMessage])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current)
      }
    }
  }, [])

  // Helper functions
  const sendRobotCommand = useCallback((command: any) => {
    sendMessage({
      type: 'robot_command',
      data: command
    })
  }, [sendMessage])

  const sendVideoCommand = useCallback((command: any) => {
    sendMessage({
      type: 'video_command',
      data: command
    })
  }, [sendMessage])

  const sendAudioCommand = useCallback((command: any) => {
    sendMessage({
      type: 'audio_command',
      data: command
    })
  }, [sendMessage])

  const sendLEDCommand = useCallback((command: any) => {
    sendMessage({
      type: 'led_command',
      data: command
    })
  }, [sendMessage])

  const requestRobotStatus = useCallback(() => {
    sendMessage({
      type: 'get_robot_status',
      data: {}
    })
  }, [sendMessage])

  const requestSensorData = useCallback(() => {
    sendMessage({
      type: 'get_sensor_data',
      data: {}
    })
  }, [sendMessage])

  const requestSystemMetrics = useCallback(() => {
    sendMessage({
      type: 'get_system_metrics',
      data: {}
    })
  }, [sendMessage])

  const subscribeToTopic = useCallback((topic: string) => {
    subscribe(topic)
    sendMessage({
      type: 'subscribe',
      data: { topic }
    })
  }, [subscribe, sendMessage])

  const unsubscribeFromTopic = useCallback((topic: string) => {
    unsubscribe(topic)
    sendMessage({
      type: 'unsubscribe',
      data: { topic }
    })
  }, [unsubscribe, sendMessage])

  const forceReconnect = useCallback(() => {
    connectionAttemptsRef.current = 0
    clearError()
    reconnect()
  }, [clearError, reconnect])

  return {
    // Connection state
    isConnected,
    isConnecting,
    error,
    connectionAttempts: connectionAttemptsRef.current,
    maxReconnectAttempts,
    
    // Data
    lastMessage,
    robotStatus,
    sensorData,
    systemMetrics,
    
    // Actions
    connect,
    disconnect,
    reconnect: forceReconnect,
    sendMessage,
    
    // Command helpers
    sendRobotCommand,
    sendVideoCommand,
    sendAudioCommand,
    sendLEDCommand,
    
    // Data request helpers
    requestRobotStatus,
    requestSensorData,
    requestSystemMetrics,
    
    // Subscription helpers
    subscribeToTopic,
    unsubscribeFromTopic,
    
    // Utility
    clearError,
    clearSensorData,
    clearSystemMetrics
  }
}

/**
 * Hook for subscribing to specific WebSocket topics
 */
export const useWebSocketSubscription = (topics: string[]) => {
  const { subscribeToTopic, unsubscribeFromTopic, isConnected } = useWebSocket()
  
  useEffect(() => {
    if (isConnected) {
      topics.forEach(topic => {
        subscribeToTopic(topic)
      })
      
      return () => {
        topics.forEach(topic => {
          unsubscribeFromTopic(topic)
        })
      }
    }
  }, [topics, isConnected, subscribeToTopic, unsubscribeFromTopic])
}

/**
 * Hook for real-time robot status updates
 */
export const useRobotStatusUpdates = () => {
  const { robotStatus, requestRobotStatus, isConnected } = useWebSocket()
  
  // Subscribe to robot status updates
  useWebSocketSubscription(['robot_status'])
  
  // Request initial status when connected
  useEffect(() => {
    if (isConnected) {
      requestRobotStatus()
    }
  }, [isConnected, requestRobotStatus])
  
  return {
    robotStatus,
    requestUpdate: requestRobotStatus
  }
}

/**
 * Hook for real-time sensor data updates
 */
export const useSensorDataUpdates = (sensorTypes?: string[]) => {
  const { sensorData, requestSensorData, isConnected } = useWebSocket()
  
  // Subscribe to sensor data updates
  useWebSocketSubscription(['sensor_data'])
  
  // Request initial data when connected
  useEffect(() => {
    if (isConnected) {
      requestSensorData()
    }
  }, [isConnected, requestSensorData])
  
  // Filter sensor data by types if specified
  const filteredSensorData = sensorTypes 
    ? sensorData.filter(sensor => sensorTypes.includes(sensor.type))
    : sensorData
  
  return {
    sensorData: filteredSensorData,
    allSensorData: sensorData,
    requestUpdate: requestSensorData
  }
}

/**
 * Hook for real-time system metrics updates
 */
export const useSystemMetricsUpdates = () => {
  const { systemMetrics, requestSystemMetrics, isConnected } = useWebSocket()
  
  // Subscribe to system metrics updates
  useWebSocketSubscription(['system_metrics'])
  
  // Request initial metrics when connected
  useEffect(() => {
    if (isConnected) {
      requestSystemMetrics()
    }
  }, [isConnected, requestSystemMetrics])
  
  return {
    systemMetrics,
    requestUpdate: requestSystemMetrics
  }
}

/**
 * Hook for WebSocket message handling with type safety
 */
export const useWebSocketMessage = <T = any>(messageType: MessageType, handler: (data: T) => void) => {
  const { lastMessage } = useWebSocket()
  
  useEffect(() => {
    if (lastMessage && lastMessage.type === messageType) {
      handler(lastMessage.data as T)
    }
  }, [lastMessage, messageType, handler])
}

/**
 * Hook for connection status monitoring
 */
export const useConnectionStatus = () => {
  const { isConnected, isConnecting, error, connectionAttempts, maxReconnectAttempts } = useWebSocket()
  
  const connectionStatus = isConnected 
    ? 'connected' 
    : isConnecting 
      ? 'connecting' 
      : error 
        ? 'error' 
        : 'disconnected'
  
  const connectionHealth = isConnected 
    ? 'good'
    : connectionAttempts > 0 && connectionAttempts < maxReconnectAttempts
      ? 'warning'
      : 'critical'
  
  return {
    status: connectionStatus,
    health: connectionHealth,
    isConnected,
    isConnecting,
    error,
    connectionAttempts,
    maxReconnectAttempts
  }
}