import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface RobotState {
  // Robot status
  isConnected: boolean
  status: 'online' | 'offline' | 'error' | 'charging' | 'low_battery'
  motionState: 'idle' | 'walking' | 'running' | 'sitting' | 'lying' | 'standing' | 'error'
  
  // Battery information
  batteryLevel: number
  batteryVoltage: number
  isCharging: boolean
  
  // Position and orientation
  position: { x: number; y: number; z: number }
  orientation: { roll: number; pitch: number; yaw: number }
  velocity: { x: number; y: number; z: number }
  
  // Sensor data
  temperature: number
  humidity: number
  pressure: number
  
  // System metrics
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkLatency: number
  
  // Control settings
  maxSpeed: number
  maxTurnRate: number
  emergencyStopEnabled: boolean
  
  // Actions
  updateRobotStatus: (status: Partial<RobotState>) => void
  updateBattery: (battery: { level: number; voltage: number; isCharging: boolean }) => void
  updatePosition: (position: { x: number; y: number; z: number }) => void
  updateOrientation: (orientation: { roll: number; pitch: number; yaw: number }) => void
  updateVelocity: (velocity: { x: number; y: number; z: number }) => void
  updateSensorData: (sensors: { temperature: number; humidity: number; pressure: number }) => void
  updateSystemMetrics: (metrics: { cpuUsage: number; memoryUsage: number; diskUsage: number; networkLatency: number }) => void
  setEmergencyStop: (enabled: boolean) => void
  setMaxSpeed: (speed: number) => void
  setMaxTurnRate: (rate: number) => void
  reset: () => void
}

const initialState = {
  isConnected: false,
  status: 'offline' as const,
  motionState: 'idle' as const,
  batteryLevel: 0,
  batteryVoltage: 0,
  isCharging: false,
  position: { x: 0, y: 0, z: 0 },
  orientation: { roll: 0, pitch: 0, yaw: 0 },
  velocity: { x: 0, y: 0, z: 0 },
  temperature: 0,
  humidity: 0,
  pressure: 0,
  cpuUsage: 0,
  memoryUsage: 0,
  diskUsage: 0,
  networkLatency: 0,
  maxSpeed: 2.0,
  maxTurnRate: 90,
  emergencyStopEnabled: false
}

export const useRobotStore = create<RobotState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      updateRobotStatus: (status) => {
        set((state) => ({ ...state, ...status }))
      },
      
      updateBattery: (battery) => {
        set((state) => ({
          ...state,
          batteryLevel: battery.level,
          batteryVoltage: battery.voltage,
          isCharging: battery.isCharging
        }))
      },
      
      updatePosition: (position) => {
        set((state) => ({ ...state, position }))
      },
      
      updateOrientation: (orientation) => {
        set((state) => ({ ...state, orientation }))
      },
      
      updateVelocity: (velocity) => {
        set((state) => ({ ...state, velocity }))
      },
      
      updateSensorData: (sensors) => {
        set((state) => ({
          ...state,
          temperature: sensors.temperature,
          humidity: sensors.humidity,
          pressure: sensors.pressure
        }))
      },
      
      updateSystemMetrics: (metrics) => {
        set((state) => ({
          ...state,
          cpuUsage: metrics.cpuUsage,
          memoryUsage: metrics.memoryUsage,
          diskUsage: metrics.diskUsage,
          networkLatency: metrics.networkLatency
        }))
      },
      
      setEmergencyStop: (enabled) => {
        set((state) => ({ ...state, emergencyStopEnabled: enabled }))
      },
      
      setMaxSpeed: (speed) => {
        set((state) => ({ ...state, maxSpeed: Math.max(0, Math.min(speed, 5.0)) }))
      },
      
      setMaxTurnRate: (rate) => {
        set((state) => ({ ...state, maxTurnRate: Math.max(0, Math.min(rate, 180)) }))
      },
      
      reset: () => {
        set(initialState)
      }
    }),
    {
      name: 'robot-storage',
      partialize: (state) => ({
        maxSpeed: state.maxSpeed,
        maxTurnRate: state.maxTurnRate,
        emergencyStopEnabled: state.emergencyStopEnabled
      })
    }
  )
)

// Selectors for better performance
export const useRobotStatus = () => useRobotStore((state) => state.status)
export const useRobotBattery = () => useRobotStore((state) => ({
  level: state.batteryLevel,
  voltage: state.batteryVoltage,
  isCharging: state.isCharging
}))
export const useRobotPosition = () => useRobotStore((state) => state.position)
export const useRobotOrientation = () => useRobotStore((state) => state.orientation)
export const useRobotVelocity = () => useRobotStore((state) => state.velocity)
export const useRobotSensors = () => useRobotStore((state) => ({
  temperature: state.temperature,
  humidity: state.humidity,
  pressure: state.pressure
}))
export const useSystemMetrics = () => useRobotStore((state) => ({
  cpuUsage: state.cpuUsage,
  memoryUsage: state.memoryUsage,
  diskUsage: state.diskUsage,
  networkLatency: state.networkLatency
}))