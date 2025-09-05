import { create } from 'zustand'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage, MessageType, RobotStatus, SensorData, SystemMetrics } from '../types'
import toast from 'react-hot-toast'

interface WebSocketState {
  socket: Socket | null
  isConnected: boolean
  isConnecting: boolean
  connectionError: string | null
  lastMessage: WebSocketMessage | null
  robotStatus: RobotStatus | null
  sensorData: Record<string, SensorData[]>
  systemMetrics: SystemMetrics | null
  messageHistory: WebSocketMessage[]
}

interface WebSocketStore extends WebSocketState {
  // Connection management
  connect: () => void
  disconnect: () => void
  reconnect: () => void
  
  // Message handling
  sendMessage: (message: WebSocketMessage) => void
  subscribeToTopic: (topic: string) => void
  unsubscribeFromTopic: (topic: string) => void
  
  // Data management
  clearHistory: () => void
  clearSensorData: () => void
  
  // Event handlers
  onRobotStatus: (callback: (status: RobotStatus) => void) => () => void
  onSensorData: (callback: (data: SensorData) => void) => () => void
  onSystemMetrics: (callback: (metrics: SystemMetrics) => void) => () => void
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const MAX_MESSAGE_HISTORY = 1000
const MAX_SENSOR_DATA_POINTS = 100
const RECONNECT_INTERVAL = 5000

export const useWebSocketStore = create<WebSocketStore>((set, get) => ({
  // Initial state
  socket: null,
  isConnected: false,
  isConnecting: false,
  connectionError: null,
  lastMessage: null,
  robotStatus: null,
  sensorData: {},
  systemMetrics: null,
  messageHistory: [],

  // Connection management
  connect: () => {
    const { socket, isConnected, isConnecting } = get()
    
    if (isConnected || isConnecting || socket) {
      return
    }
    
    set({ isConnecting: true, connectionError: null })
    
    try {
      const newSocket = io(WS_URL, {
        transports: ['websocket'],
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: RECONNECT_INTERVAL,
        auth: {
          token: localStorage.getItem('auth_token')
        }
      })
      
      // Connection events
      newSocket.on('connect', () => {
        console.log('WebSocket connected')
        set({
          socket: newSocket,
          isConnected: true,
          isConnecting: false,
          connectionError: null
        })
        toast.success('Connected to robot')
      })
      
      newSocket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason)
        set({
          isConnected: false,
          connectionError: reason
        })
        
        if (reason === 'io server disconnect') {
          // Server disconnected, try to reconnect
          setTimeout(() => {
            get().reconnect()
          }, RECONNECT_INTERVAL)
        }
      })
      
      newSocket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        set({
          isConnecting: false,
          connectionError: error.message
        })
        toast.error('Failed to connect to robot')
      })
      
      // Message handling
      newSocket.on('message', (message: WebSocketMessage) => {
        const { messageHistory } = get()
        
        // Add to message history
        const newHistory = [...messageHistory, message].slice(-MAX_MESSAGE_HISTORY)
        
        set({
          lastMessage: message,
          messageHistory: newHistory
        })
        
        // Handle specific message types
        switch (message.type) {
          case MessageType.ROBOT_STATUS:
            set({ robotStatus: message.data })
            break
            
          case MessageType.SENSOR_DATA:
            const sensorData = message.data as SensorData
            const { sensorData: currentSensorData } = get()
            const sensorType = sensorData.sensor_type
            
            const updatedSensorData = {
              ...currentSensorData,
              [sensorType]: [
                ...(currentSensorData[sensorType] || []),
                sensorData
              ].slice(-MAX_SENSOR_DATA_POINTS)
            }
            
            set({ sensorData: updatedSensorData })
            break
            
          case MessageType.SYSTEM_METRICS:
            set({ systemMetrics: message.data })
            break
            
          case MessageType.ERROR:
            toast.error(message.data.message || 'Robot error occurred')
            break
            
          case MessageType.WARNING:
            toast.error(message.data.message || 'Robot warning', {
              icon: '⚠️'
            })
            break
            
          case MessageType.SYSTEM_ALERT:
            toast.error(message.data.message || 'System alert', {
              duration: 6000
            })
            break
        }
      })
      
      // Robot-specific events
      newSocket.on('robot_status', (status: RobotStatus) => {
        set({ robotStatus: status })
      })
      
      newSocket.on('sensor_data', (data: SensorData) => {
        const { sensorData: currentSensorData } = get()
        const sensorType = data.sensor_type
        
        const updatedSensorData = {
          ...currentSensorData,
          [sensorType]: [
            ...(currentSensorData[sensorType] || []),
            data
          ].slice(-MAX_SENSOR_DATA_POINTS)
        }
        
        set({ sensorData: updatedSensorData })
      })
      
      newSocket.on('system_metrics', (metrics: SystemMetrics) => {
        set({ systemMetrics: metrics })
      })
      
      set({ socket: newSocket })
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      set({
        isConnecting: false,
        connectionError: 'Failed to create connection'
      })
      toast.error('Failed to connect to robot')
    }
  },
  
  disconnect: () => {
    const { socket } = get()
    
    if (socket) {
      socket.disconnect()
      set({
        socket: null,
        isConnected: false,
        isConnecting: false,
        connectionError: null
      })
    }
  },
  
  reconnect: () => {
    const { disconnect, connect } = get()
    disconnect()
    setTimeout(connect, 1000)
  },
  
  // Message handling
  sendMessage: (message: WebSocketMessage) => {
    const { socket, isConnected } = get()
    
    if (!socket || !isConnected) {
      toast.error('Not connected to robot')
      return
    }
    
    try {
      socket.emit('message', message)
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error('Failed to send command')
    }
  },
  
  subscribeToTopic: (topic: string) => {
    const { socket, isConnected } = get()
    
    if (!socket || !isConnected) {
      return
    }
    
    socket.emit('subscribe', { topic })
  },
  
  unsubscribeFromTopic: (topic: string) => {
    const { socket, isConnected } = get()
    
    if (!socket || !isConnected) {
      return
    }
    
    socket.emit('unsubscribe', { topic })
  },
  
  // Data management
  clearHistory: () => {
    set({ messageHistory: [] })
  },
  
  clearSensorData: () => {
    set({ sensorData: {} })
  },
  
  // Event handlers
  onRobotStatus: (callback: (status: RobotStatus) => void) => {
    const { socket } = get()
    
    if (!socket) {
      return () => {}
    }
    
    socket.on('robot_status', callback)
    
    return () => {
      socket.off('robot_status', callback)
    }
  },
  
  onSensorData: (callback: (data: SensorData) => void) => {
    const { socket } = get()
    
    if (!socket) {
      return () => {}
    }
    
    socket.on('sensor_data', callback)
    
    return () => {
      socket.off('sensor_data', callback)
    }
  },
  
  onSystemMetrics: (callback: (metrics: SystemMetrics) => void) => {
    const { socket } = get()
    
    if (!socket) {
      return () => {}
    }
    
    socket.on('system_metrics', callback)
    
    return () => {
      socket.off('system_metrics', callback)
    }
  }
}))

// Export selectors for better performance
export const selectIsConnected = () => useWebSocketStore((state) => state.isConnected)
export const selectRobotStatus = () => useWebSocketStore((state) => state.robotStatus)
export const selectSensorData = () => useWebSocketStore((state) => state.sensorData)
export const selectSystemMetrics = () => useWebSocketStore((state) => state.systemMetrics)
export const selectConnectionError = () => useWebSocketStore((state) => state.connectionError)