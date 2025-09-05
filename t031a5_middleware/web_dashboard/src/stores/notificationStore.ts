import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: number
  duration?: number // in milliseconds, undefined means persistent
  actions?: Array<{
    label: string
    action: () => void
    variant?: 'primary' | 'secondary'
  }>
  read: boolean
  persistent: boolean
}

export interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  maxNotifications: number
  defaultDuration: number
  soundEnabled: boolean
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => string
  removeNotification: (id: string) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearAll: () => void
  clearOld: (olderThanHours?: number) => void
  updateNotification: (id: string, updates: Partial<Notification>) => void
  
  // Convenience methods
  info: (title: string, message: string, options?: Partial<Notification>) => string
  success: (title: string, message: string, options?: Partial<Notification>) => string
  warning: (title: string, message: string, options?: Partial<Notification>) => string
  error: (title: string, message: string, options?: Partial<Notification>) => string
  
  // Settings
  setMaxNotifications: (max: number) => void
  setDefaultDuration: (duration: number) => void
  setSoundEnabled: (enabled: boolean) => void
}

const generateId = () => {
  return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const initialState = {
  notifications: [] as Notification[],
  unreadCount: 0,
  maxNotifications: 50,
  defaultDuration: 5000,
  soundEnabled: true
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      addNotification: (notificationData) => {
        const id = generateId()
        const notification: Notification = {
          id,
          timestamp: Date.now(),
          read: false,
          persistent: false,
          duration: get().defaultDuration,
          ...notificationData
        }
        
        set((state) => {
          const newNotifications = [notification, ...state.notifications]
          
          // Limit the number of notifications
          if (newNotifications.length > state.maxNotifications) {
            newNotifications.splice(state.maxNotifications)
          }
          
          return {
            ...state,
            notifications: newNotifications,
            unreadCount: state.unreadCount + 1
          }
        })
        
        // Auto-remove non-persistent notifications
        if (!notification.persistent && notification.duration) {
          setTimeout(() => {
            get().removeNotification(id)
          }, notification.duration)
        }
        
        return id
      },
      
      removeNotification: (id) => {
        set((state) => {
          const notification = state.notifications.find(n => n.id === id)
          const wasUnread = notification && !notification.read
          
          return {
            ...state,
            notifications: state.notifications.filter(n => n.id !== id),
            unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount
          }
        })
      },
      
      markAsRead: (id) => {
        set((state) => {
          const notification = state.notifications.find(n => n.id === id)
          const wasUnread = notification && !notification.read
          
          return {
            ...state,
            notifications: state.notifications.map(n => 
              n.id === id ? { ...n, read: true } : n
            ),
            unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount
          }
        })
      },
      
      markAllAsRead: () => {
        set((state) => ({
          ...state,
          notifications: state.notifications.map(n => ({ ...n, read: true })),
          unreadCount: 0
        }))
      },
      
      clearAll: () => {
        set((state) => ({
          ...state,
          notifications: [],
          unreadCount: 0
        }))
      },
      
      clearOld: (olderThanHours = 24) => {
        const cutoffTime = Date.now() - (olderThanHours * 60 * 60 * 1000)
        
        set((state) => {
          const remainingNotifications = state.notifications.filter(n => 
            n.timestamp > cutoffTime || n.persistent
          )
          
          const unreadCount = remainingNotifications.filter(n => !n.read).length
          
          return {
            ...state,
            notifications: remainingNotifications,
            unreadCount
          }
        })
      },
      
      updateNotification: (id, updates) => {
        set((state) => ({
          ...state,
          notifications: state.notifications.map(n => 
            n.id === id ? { ...n, ...updates } : n
          )
        }))
      },
      
      // Convenience methods
      info: (title, message, options = {}) => {
        return get().addNotification({
          type: 'info',
          title,
          message,
          ...options
        })
      },
      
      success: (title, message, options = {}) => {
        return get().addNotification({
          type: 'success',
          title,
          message,
          ...options
        })
      },
      
      warning: (title, message, options = {}) => {
        return get().addNotification({
          type: 'warning',
          title,
          message,
          persistent: true, // Warnings are persistent by default
          ...options
        })
      },
      
      error: (title, message, options = {}) => {
        return get().addNotification({
          type: 'error',
          title,
          message,
          persistent: true, // Errors are persistent by default
          ...options
        })
      },
      
      // Settings
      setMaxNotifications: (maxNotifications) => {
        set((state) => {
          const newNotifications = state.notifications.slice(0, maxNotifications)
          const unreadCount = newNotifications.filter(n => !n.read).length
          
          return {
            ...state,
            maxNotifications,
            notifications: newNotifications,
            unreadCount
          }
        })
      },
      
      setDefaultDuration: (defaultDuration) => {
        set((state) => ({ ...state, defaultDuration }))
      },
      
      setSoundEnabled: (soundEnabled) => {
        set((state) => ({ ...state, soundEnabled }))
      }
    }),
    {
      name: 'notification-storage',
      partialize: (state) => ({
        maxNotifications: state.maxNotifications,
        defaultDuration: state.defaultDuration,
        soundEnabled: state.soundEnabled,
        // Don't persist notifications themselves
        notifications: [],
        unreadCount: 0
      })
    }
  )
)

// Selectors for better performance
export const useNotifications = () => useNotificationStore((state) => state.notifications)
export const useUnreadCount = () => useNotificationStore((state) => state.unreadCount)
export const useNotificationSettings = () => useNotificationStore((state) => ({
  maxNotifications: state.maxNotifications,
  defaultDuration: state.defaultDuration,
  soundEnabled: state.soundEnabled
}))

// Utility hooks
export const useNotificationActions = () => {
  const store = useNotificationStore()
  return {
    info: store.info,
    success: store.success,
    warning: store.warning,
    error: store.error,
    remove: store.removeNotification,
    markAsRead: store.markAsRead,
    markAllAsRead: store.markAllAsRead,
    clearAll: store.clearAll
  }
}

export const useRecentNotifications = (limit = 5) => {
  return useNotificationStore((state) => 
    state.notifications.slice(0, limit)
  )
}

export const useNotificationsByType = (type: Notification['type']) => {
  return useNotificationStore((state) => 
    state.notifications.filter(n => n.type === type)
  )
}