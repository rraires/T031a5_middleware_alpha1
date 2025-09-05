import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface VideoState {
  // Stream settings
  isStreaming: boolean
  streamUrl: string | null
  resolution: { width: number; height: number }
  framerate: number
  bitrate: number
  quality: 'low' | 'medium' | 'high' | 'ultra'
  
  // Recording settings
  isRecording: boolean
  recordingDuration: number
  recordingSize: number
  maxRecordingSize: number
  recordingFormat: 'mp4' | 'webm' | 'avi'
  
  // Camera settings
  brightness: number
  contrast: number
  saturation: number
  exposure: number
  whiteBalance: 'auto' | 'daylight' | 'fluorescent' | 'incandescent'
  
  // Stream status
  streamHealth: 'excellent' | 'good' | 'poor' | 'disconnected'
  latency: number
  droppedFrames: number
  
  // Actions
  startStream: () => void
  stopStream: () => void
  startRecording: () => void
  stopRecording: () => void
  setResolution: (resolution: { width: number; height: number }) => void
  setFramerate: (framerate: number) => void
  setBitrate: (bitrate: number) => void
  setQuality: (quality: 'low' | 'medium' | 'high' | 'ultra') => void
  setRecordingFormat: (format: 'mp4' | 'webm' | 'avi') => void
  setBrightness: (brightness: number) => void
  setContrast: (contrast: number) => void
  setSaturation: (saturation: number) => void
  setExposure: (exposure: number) => void
  setWhiteBalance: (whiteBalance: 'auto' | 'daylight' | 'fluorescent' | 'incandescent') => void
  updateStreamStatus: (status: { health: 'excellent' | 'good' | 'poor' | 'disconnected'; latency: number; droppedFrames: number }) => void
  updateRecordingStatus: (status: { duration: number; size: number }) => void
  reset: () => void
}

const initialState = {
  isStreaming: false,
  streamUrl: null,
  resolution: { width: 1280, height: 720 },
  framerate: 30,
  bitrate: 2000,
  quality: 'medium' as const,
  isRecording: false,
  recordingDuration: 0,
  recordingSize: 0,
  maxRecordingSize: 1024 * 1024 * 1024, // 1GB
  recordingFormat: 'mp4' as const,
  brightness: 50,
  contrast: 50,
  saturation: 50,
  exposure: 0,
  whiteBalance: 'auto' as const,
  streamHealth: 'disconnected' as const,
  latency: 0,
  droppedFrames: 0
}

export const useVideoStore = create<VideoState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      startStream: () => {
        set((state) => ({ ...state, isStreaming: true }))
      },
      
      stopStream: () => {
        set((state) => ({ 
          ...state, 
          isStreaming: false, 
          streamUrl: null,
          streamHealth: 'disconnected',
          latency: 0,
          droppedFrames: 0
        }))
      },
      
      startRecording: () => {
        set((state) => ({ 
          ...state, 
          isRecording: true,
          recordingDuration: 0,
          recordingSize: 0
        }))
      },
      
      stopRecording: () => {
        set((state) => ({ 
          ...state, 
          isRecording: false
        }))
      },
      
      setResolution: (resolution) => {
        set((state) => ({ ...state, resolution }))
      },
      
      setFramerate: (framerate) => {
        set((state) => ({ ...state, framerate: Math.max(1, Math.min(framerate, 120)) }))
      },
      
      setBitrate: (bitrate) => {
        set((state) => ({ ...state, bitrate: Math.max(100, Math.min(bitrate, 10000)) }))
      },
      
      setQuality: (quality) => {
        const qualitySettings = {
          low: { bitrate: 500, framerate: 15 },
          medium: { bitrate: 1500, framerate: 30 },
          high: { bitrate: 3000, framerate: 30 },
          ultra: { bitrate: 6000, framerate: 60 }
        }
        
        const settings = qualitySettings[quality]
        set((state) => ({ 
          ...state, 
          quality,
          bitrate: settings.bitrate,
          framerate: settings.framerate
        }))
      },
      
      setRecordingFormat: (recordingFormat) => {
        set((state) => ({ ...state, recordingFormat }))
      },
      
      setBrightness: (brightness) => {
        set((state) => ({ ...state, brightness: Math.max(0, Math.min(brightness, 100)) }))
      },
      
      setContrast: (contrast) => {
        set((state) => ({ ...state, contrast: Math.max(0, Math.min(contrast, 100)) }))
      },
      
      setSaturation: (saturation) => {
        set((state) => ({ ...state, saturation: Math.max(0, Math.min(saturation, 100)) }))
      },
      
      setExposure: (exposure) => {
        set((state) => ({ ...state, exposure: Math.max(-100, Math.min(exposure, 100)) }))
      },
      
      setWhiteBalance: (whiteBalance) => {
        set((state) => ({ ...state, whiteBalance }))
      },
      
      updateStreamStatus: (status) => {
        set((state) => ({
          ...state,
          streamHealth: status.health,
          latency: status.latency,
          droppedFrames: status.droppedFrames
        }))
      },
      
      updateRecordingStatus: (status) => {
        set((state) => ({
          ...state,
          recordingDuration: status.duration,
          recordingSize: status.size
        }))
      },
      
      reset: () => {
        set(initialState)
      }
    }),
    {
      name: 'video-storage',
      partialize: (state) => ({
        resolution: state.resolution,
        framerate: state.framerate,
        bitrate: state.bitrate,
        quality: state.quality,
        recordingFormat: state.recordingFormat,
        brightness: state.brightness,
        contrast: state.contrast,
        saturation: state.saturation,
        exposure: state.exposure,
        whiteBalance: state.whiteBalance
      })
    }
  )
)

// Selectors for better performance
export const useVideoStream = () => useVideoStore((state) => ({
  isStreaming: state.isStreaming,
  streamUrl: state.streamUrl,
  health: state.streamHealth,
  latency: state.latency,
  droppedFrames: state.droppedFrames
}))

export const useVideoRecording = () => useVideoStore((state) => ({
  isRecording: state.isRecording,
  duration: state.recordingDuration,
  size: state.recordingSize,
  maxSize: state.maxRecordingSize,
  format: state.recordingFormat
}))

export const useVideoSettings = () => useVideoStore((state) => ({
  resolution: state.resolution,
  framerate: state.framerate,
  bitrate: state.bitrate,
  quality: state.quality,
  brightness: state.brightness,
  contrast: state.contrast,
  saturation: state.saturation,
  exposure: state.exposure,
  whiteBalance: state.whiteBalance
}))