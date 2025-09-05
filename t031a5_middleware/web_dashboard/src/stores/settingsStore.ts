import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface SettingsState {
  // General settings
  language: 'en' | 'pt' | 'es' | 'fr' | 'de' | 'zh'
  timezone: string
  dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD'
  timeFormat: '12h' | '24h'
  
  // Dashboard settings
  autoRefresh: boolean
  refreshInterval: number // in seconds
  showNotifications: boolean
  soundEnabled: boolean
  vibrationEnabled: boolean
  
  // Display settings
  compactMode: boolean
  showAdvancedControls: boolean
  showDebugInfo: boolean
  gridSize: 'small' | 'medium' | 'large'
  
  // Connection settings
  autoReconnect: boolean
  reconnectInterval: number // in seconds
  maxReconnectAttempts: number
  connectionTimeout: number // in seconds
  
  // Performance settings
  enableAnimations: boolean
  reducedMotion: boolean
  lowPowerMode: boolean
  maxFPS: number
  
  // Privacy settings
  analyticsEnabled: boolean
  crashReportingEnabled: boolean
  telemetryEnabled: boolean
  
  // Experimental features
  experimentalFeatures: {
    voiceControl: boolean
    gestureControl: boolean
    aiAssistant: boolean
    advancedMetrics: boolean
  }
  
  // Actions
  setLanguage: (language: 'en' | 'pt' | 'es' | 'fr' | 'de' | 'zh') => void
  setTimezone: (timezone: string) => void
  setDateFormat: (format: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD') => void
  setTimeFormat: (format: '12h' | '24h') => void
  setAutoRefresh: (enabled: boolean) => void
  setRefreshInterval: (interval: number) => void
  setNotifications: (enabled: boolean) => void
  setSoundEnabled: (enabled: boolean) => void
  setVibrationEnabled: (enabled: boolean) => void
  setCompactMode: (enabled: boolean) => void
  setShowAdvancedControls: (enabled: boolean) => void
  setShowDebugInfo: (enabled: boolean) => void
  setGridSize: (size: 'small' | 'medium' | 'large') => void
  setAutoReconnect: (enabled: boolean) => void
  setReconnectInterval: (interval: number) => void
  setMaxReconnectAttempts: (attempts: number) => void
  setConnectionTimeout: (timeout: number) => void
  setEnableAnimations: (enabled: boolean) => void
  setReducedMotion: (enabled: boolean) => void
  setLowPowerMode: (enabled: boolean) => void
  setMaxFPS: (fps: number) => void
  setAnalyticsEnabled: (enabled: boolean) => void
  setCrashReportingEnabled: (enabled: boolean) => void
  setTelemetryEnabled: (enabled: boolean) => void
  setExperimentalFeature: (feature: keyof SettingsState['experimentalFeatures'], enabled: boolean) => void
  resetToDefaults: () => void
  exportSettings: () => string
  importSettings: (settings: string) => boolean
}

const initialState = {
  language: 'en' as const,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  dateFormat: 'DD/MM/YYYY' as const,
  timeFormat: '24h' as const,
  autoRefresh: true,
  refreshInterval: 5,
  showNotifications: true,
  soundEnabled: true,
  vibrationEnabled: true,
  compactMode: false,
  showAdvancedControls: false,
  showDebugInfo: false,
  gridSize: 'medium' as const,
  autoReconnect: true,
  reconnectInterval: 5,
  maxReconnectAttempts: 10,
  connectionTimeout: 30,
  enableAnimations: true,
  reducedMotion: false,
  lowPowerMode: false,
  maxFPS: 60,
  analyticsEnabled: true,
  crashReportingEnabled: true,
  telemetryEnabled: true,
  experimentalFeatures: {
    voiceControl: false,
    gestureControl: false,
    aiAssistant: false,
    advancedMetrics: false
  }
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setLanguage: (language) => {
        set((state) => ({ ...state, language }))
      },
      
      setTimezone: (timezone) => {
        set((state) => ({ ...state, timezone }))
      },
      
      setDateFormat: (dateFormat) => {
        set((state) => ({ ...state, dateFormat }))
      },
      
      setTimeFormat: (timeFormat) => {
        set((state) => ({ ...state, timeFormat }))
      },
      
      setAutoRefresh: (autoRefresh) => {
        set((state) => ({ ...state, autoRefresh }))
      },
      
      setRefreshInterval: (refreshInterval) => {
        set((state) => ({ 
          ...state, 
          refreshInterval: Math.max(1, Math.min(refreshInterval, 300)) 
        }))
      },
      
      setNotifications: (showNotifications) => {
        set((state) => ({ ...state, showNotifications }))
      },
      
      setSoundEnabled: (soundEnabled) => {
        set((state) => ({ ...state, soundEnabled }))
      },
      
      setVibrationEnabled: (vibrationEnabled) => {
        set((state) => ({ ...state, vibrationEnabled }))
      },
      
      setCompactMode: (compactMode) => {
        set((state) => ({ ...state, compactMode }))
      },
      
      setShowAdvancedControls: (showAdvancedControls) => {
        set((state) => ({ ...state, showAdvancedControls }))
      },
      
      setShowDebugInfo: (showDebugInfo) => {
        set((state) => ({ ...state, showDebugInfo }))
      },
      
      setGridSize: (gridSize) => {
        set((state) => ({ ...state, gridSize }))
      },
      
      setAutoReconnect: (autoReconnect) => {
        set((state) => ({ ...state, autoReconnect }))
      },
      
      setReconnectInterval: (reconnectInterval) => {
        set((state) => ({ 
          ...state, 
          reconnectInterval: Math.max(1, Math.min(reconnectInterval, 60)) 
        }))
      },
      
      setMaxReconnectAttempts: (maxReconnectAttempts) => {
        set((state) => ({ 
          ...state, 
          maxReconnectAttempts: Math.max(1, Math.min(maxReconnectAttempts, 100)) 
        }))
      },
      
      setConnectionTimeout: (connectionTimeout) => {
        set((state) => ({ 
          ...state, 
          connectionTimeout: Math.max(5, Math.min(connectionTimeout, 300)) 
        }))
      },
      
      setEnableAnimations: (enableAnimations) => {
        set((state) => ({ ...state, enableAnimations }))
      },
      
      setReducedMotion: (reducedMotion) => {
        set((state) => ({ ...state, reducedMotion }))
      },
      
      setLowPowerMode: (lowPowerMode) => {
        set((state) => ({ ...state, lowPowerMode }))
      },
      
      setMaxFPS: (maxFPS) => {
        set((state) => ({ 
          ...state, 
          maxFPS: Math.max(15, Math.min(maxFPS, 120)) 
        }))
      },
      
      setAnalyticsEnabled: (analyticsEnabled) => {
        set((state) => ({ ...state, analyticsEnabled }))
      },
      
      setCrashReportingEnabled: (crashReportingEnabled) => {
        set((state) => ({ ...state, crashReportingEnabled }))
      },
      
      setTelemetryEnabled: (telemetryEnabled) => {
        set((state) => ({ ...state, telemetryEnabled }))
      },
      
      setExperimentalFeature: (feature, enabled) => {
        set((state) => ({
          ...state,
          experimentalFeatures: {
            ...state.experimentalFeatures,
            [feature]: enabled
          }
        }))
      },
      
      resetToDefaults: () => {
        set(initialState)
      },
      
      exportSettings: () => {
        const state = get()
        const exportData = {
          ...state,
          exportedAt: new Date().toISOString(),
          version: '1.0.0'
        }
        return JSON.stringify(exportData, null, 2)
      },
      
      importSettings: (settingsJson) => {
        try {
          const importedSettings = JSON.parse(settingsJson)
          
          // Validate imported settings
          if (typeof importedSettings !== 'object' || !importedSettings) {
            return false
          }
          
          // Apply only valid settings
          const validSettings = Object.keys(initialState).reduce((acc, key) => {
            if (key in importedSettings && typeof importedSettings[key] === typeof initialState[key as keyof typeof initialState]) {
              acc[key as keyof typeof initialState] = importedSettings[key]
            }
            return acc
          }, {} as Partial<typeof initialState>)
          
          set((state) => ({ ...state, ...validSettings }))
          return true
        } catch (error) {
          console.error('Failed to import settings:', error)
          return false
        }
      }
    }),
    {
      name: 'settings-storage'
    }
  )
)

// Selectors for better performance
export const useLanguageSettings = () => useSettingsStore((state) => ({
  language: state.language,
  timezone: state.timezone,
  dateFormat: state.dateFormat,
  timeFormat: state.timeFormat
}))

export const useDisplaySettings = () => useSettingsStore((state) => ({
  compactMode: state.compactMode,
  showAdvancedControls: state.showAdvancedControls,
  showDebugInfo: state.showDebugInfo,
  gridSize: state.gridSize,
  enableAnimations: state.enableAnimations,
  reducedMotion: state.reducedMotion
}))

export const useConnectionSettings = () => useSettingsStore((state) => ({
  autoReconnect: state.autoReconnect,
  reconnectInterval: state.reconnectInterval,
  maxReconnectAttempts: state.maxReconnectAttempts,
  connectionTimeout: state.connectionTimeout
}))

export const useNotificationSettings = () => useSettingsStore((state) => ({
  showNotifications: state.showNotifications,
  soundEnabled: state.soundEnabled,
  vibrationEnabled: state.vibrationEnabled
}))

export const useExperimentalFeatures = () => useSettingsStore((state) => state.experimentalFeatures)