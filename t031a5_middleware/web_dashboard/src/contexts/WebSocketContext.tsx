import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { useWebSocketStore } from '../stores/webSocketStore'
import { WebSocketMessage, MessageType } from '../types'

interface WebSocketContextType {
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastMessage: WebSocketMessage | null
  sendMessage: (type: MessageType, payload: any) => void
  connect: () => void
  disconnect: () => void
  subscribe: (type: MessageType, callback: (data: any) => void) => () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: ReactNode
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    subscribe
  } = useWebSocketStore()

  useEffect(() => {
    // Auto-connect on mount
    connect()

    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [])

  const contextValue: WebSocketContextType = {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    subscribe
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}