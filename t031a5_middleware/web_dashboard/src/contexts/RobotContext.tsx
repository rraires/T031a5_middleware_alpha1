import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { useRobotStore } from '../stores/robotStore'
import { RobotState, RobotStatus, MotionCommand, SensorData } from '../types'

interface RobotContextType {
  robotState: RobotState
  robotStatus: RobotStatus
  sensorData: SensorData | null
  isConnected: boolean
  isMoving: boolean
  batteryLevel: number
  sendMotionCommand: (command: MotionCommand) => void
  emergencyStop: () => void
  connect: () => void
  disconnect: () => void
  updateRobotState: (state: Partial<RobotState>) => void
}

const RobotContext = createContext<RobotContextType | undefined>(undefined)

interface RobotProviderProps {
  children: ReactNode
}

export const RobotProvider: React.FC<RobotProviderProps> = ({ children }) => {
  const {
    robotState,
    robotStatus,
    sensorData,
    isConnected,
    isMoving,
    batteryLevel,
    sendMotionCommand,
    emergencyStop,
    connect,
    disconnect,
    updateRobotState,
    initializeRobot
  } = useRobotStore()

  useEffect(() => {
    // Initialize robot connection on mount
    initializeRobot()

    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [])

  const contextValue: RobotContextType = {
    robotState,
    robotStatus,
    sensorData,
    isConnected,
    isMoving,
    batteryLevel,
    sendMotionCommand,
    emergencyStop,
    connect,
    disconnect,
    updateRobotState
  }

  return (
    <RobotContext.Provider value={contextValue}>
      {children}
    </RobotContext.Provider>
  )
}

export const useRobotContext = () => {
  const context = useContext(RobotContext)
  if (context === undefined) {
    throw new Error('useRobotContext must be used within a RobotProvider')
  }
  return context
}