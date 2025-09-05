import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { videoService } from '../services/videoService'
import { VideoStream, VideoConfig, VideoRecording } from '../types'
import toast from 'react-hot-toast'

/**
 * Hook for video streaming and management
 */
export const useVideo = () => {
  const queryClient = useQueryClient()
  const [activeStreams, setActiveStreams] = useState<Map<string, MediaStream>>(new Map())
  const [streamElements, setStreamElements] = useState<Map<string, HTMLVideoElement>>(new Map())
  const videoRefs = useRef<Map<string, HTMLVideoElement>>(new Map())

  // Available streams query
  const streamsQuery = useQuery({
    queryKey: ['video', 'streams'],
    queryFn: async () => {
      const response = await videoService.getAvailableStreams()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get available streams')
      }
      return response.data!
    },
    staleTime: 30000,
    retry: 3
  })

  // Video config query
  const configQuery = useQuery({
    queryKey: ['video', 'config'],
    queryFn: async () => {
      const response = await videoService.getVideoConfig()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get video config')
      }
      return response.data!
    },
    staleTime: 60000,
    retry: 3
  })

  // Recordings query
  const recordingsQuery = useQuery({
    queryKey: ['video', 'recordings'],
    queryFn: async () => {
      const response = await videoService.getRecordings()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get recordings')
      }
      return response.data!
    },
    staleTime: 10000,
    retry: 3
  })

  // Start stream mutation
  const startStreamMutation = useMutation({
    mutationFn: async ({ streamId, config }: { streamId: string; config?: Partial<VideoConfig> }) => {
      const response = await videoService.startStream(streamId, config)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to start stream')
      }
      return response.data!
    },
    onSuccess: (data, variables) => {
      toast.success(`Stream ${variables.streamId} started`)
      queryClient.invalidateQueries({ queryKey: ['video', 'streams'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Stop stream mutation
  const stopStreamMutation = useMutation({
    mutationFn: async (streamId: string) => {
      const response = await videoService.stopStream(streamId)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to stop stream')
      }
      return response.data!
    },
    onSuccess: (data, streamId) => {
      toast.success(`Stream ${streamId} stopped`)
      // Clean up local stream
      const stream = activeStreams.get(streamId)
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
        setActiveStreams(prev => {
          const newMap = new Map(prev)
          newMap.delete(streamId)
          return newMap
        })
      }
      queryClient.invalidateQueries({ queryKey: ['video', 'streams'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Start recording mutation
  const startRecordingMutation = useMutation({
    mutationFn: async ({ streamId, filename }: { streamId: string; filename?: string }) => {
      const response = await videoService.startRecording(streamId, filename)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to start recording')
      }
      return response.data!
    },
    onSuccess: (data, variables) => {
      toast.success(`Recording started for stream ${variables.streamId}`)
      queryClient.invalidateQueries({ queryKey: ['video', 'recordings'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Stop recording mutation
  const stopRecordingMutation = useMutation({
    mutationFn: async (streamId: string) => {
      const response = await videoService.stopRecording(streamId)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to stop recording')
      }
      return response.data!
    },
    onSuccess: (data, streamId) => {
      toast.success(`Recording stopped for stream ${streamId}`)
      queryClient.invalidateQueries({ queryKey: ['video', 'recordings'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Take snapshot mutation
  const snapshotMutation = useMutation({
    mutationFn: async ({ streamId, filename }: { streamId: string; filename?: string }) => {
      const response = await videoService.takeSnapshot(streamId, filename)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to take snapshot')
      }
      return response.data!
    },
    onSuccess: (data, variables) => {
      toast.success(`Snapshot taken for stream ${variables.streamId}`)
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Update config mutation
  const updateConfigMutation = useMutation({
    mutationFn: async (config: Partial<VideoConfig>) => {
      const response = await videoService.updateVideoConfig(config)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to update video config')
      }
      return response.data!
    },
    onSuccess: () => {
      toast.success('Video configuration updated')
      queryClient.invalidateQueries({ queryKey: ['video', 'config'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Delete recording mutation
  const deleteRecordingMutation = useMutation({
    mutationFn: async (recordingId: string) => {
      const response = await videoService.deleteRecording(recordingId)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to delete recording')
      }
    },
    onSuccess: (_, recordingId) => {
      toast.success('Recording deleted')
      queryClient.invalidateQueries({ queryKey: ['video', 'recordings'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // WebRTC connection helper
  const connectWebRTC = useCallback(async (streamId: string, videoElement: HTMLVideoElement) => {
    try {
      const stream = await videoService.connectWebRTCStream(streamId)
      if (stream) {
        videoElement.srcObject = stream
        setActiveStreams(prev => new Map(prev).set(streamId, stream))
        setStreamElements(prev => new Map(prev).set(streamId, videoElement))
        videoRefs.current.set(streamId, videoElement)
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to connect WebRTC stream:', error)
      toast.error('Failed to connect video stream')
      return false
    }
  }, [])

  // HTTP stream connection helper
  const connectHTTPStream = useCallback(async (streamId: string, videoElement: HTMLVideoElement) => {
    try {
      const success = await videoService.connectHTTPStream(streamId, videoElement)
      if (success) {
        setStreamElements(prev => new Map(prev).set(streamId, videoElement))
        videoRefs.current.set(streamId, videoElement)
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to connect HTTP stream:', error)
      toast.error('Failed to connect video stream')
      return false
    }
  }, [])

  // Disconnect stream helper
  const disconnectStream = useCallback((streamId: string) => {
    const stream = activeStreams.get(streamId)
    const element = streamElements.get(streamId)
    
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setActiveStreams(prev => {
        const newMap = new Map(prev)
        newMap.delete(streamId)
        return newMap
      })
    }
    
    if (element) {
      element.srcObject = null
      setStreamElements(prev => {
        const newMap = new Map(prev)
        newMap.delete(streamId)
        return newMap
      })
    }
    
    videoRefs.current.delete(streamId)
    videoService.disconnectStream(streamId)
  }, [activeStreams, streamElements])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      activeStreams.forEach((stream, streamId) => {
        disconnectStream(streamId)
      })
      videoService.cleanup()
    }
  }, [])

  // Helper functions
  const startStream = useCallback((streamId: string, config?: Partial<VideoConfig>) => {
    startStreamMutation.mutate({ streamId, config })
  }, [startStreamMutation])

  const stopStream = useCallback((streamId: string) => {
    stopStreamMutation.mutate(streamId)
  }, [stopStreamMutation])

  const startRecording = useCallback((streamId: string, filename?: string) => {
    startRecordingMutation.mutate({ streamId, filename })
  }, [startRecordingMutation])

  const stopRecording = useCallback((streamId: string) => {
    stopRecordingMutation.mutate(streamId)
  }, [stopRecordingMutation])

  const takeSnapshot = useCallback((streamId: string, filename?: string) => {
    snapshotMutation.mutate({ streamId, filename })
  }, [snapshotMutation])

  const updateConfig = useCallback((config: Partial<VideoConfig>) => {
    updateConfigMutation.mutate(config)
  }, [updateConfigMutation])

  const deleteRecording = useCallback((recordingId: string) => {
    deleteRecordingMutation.mutate(recordingId)
  }, [deleteRecordingMutation])

  const downloadRecording = useCallback(async (recordingId: string, filename?: string) => {
    try {
      await videoService.downloadRecording(recordingId, filename)
      toast.success('Recording download started')
    } catch (error) {
      toast.error('Failed to download recording')
    }
  }, [])

  // Status helpers
  const isStreamActive = useCallback((streamId: string) => {
    return videoService.isStreamActive(streamId)
  }, [])

  const getActiveStreamCount = useCallback(() => {
    return videoService.getActiveStreamCount()
  }, [])

  const getStreamElement = useCallback((streamId: string) => {
    return videoService.getStreamElement(streamId)
  }, [])

  return {
    // Data
    streams: streamsQuery.data || [],
    config: configQuery.data,
    recordings: recordingsQuery.data || [],
    activeStreams,
    streamElements,
    
    // Loading states
    isLoading: streamsQuery.isLoading || configQuery.isLoading || recordingsQuery.isLoading,
    isStreamsLoading: streamsQuery.isLoading,
    isConfigLoading: configQuery.isLoading,
    isRecordingsLoading: recordingsQuery.isLoading,
    
    // Error states
    streamsError: streamsQuery.error,
    configError: configQuery.error,
    recordingsError: recordingsQuery.error,
    
    // Actions
    startStream,
    stopStream,
    startRecording,
    stopRecording,
    takeSnapshot,
    updateConfig,
    deleteRecording,
    downloadRecording,
    
    // Connection helpers
    connectWebRTC,
    connectHTTPStream,
    disconnectStream,
    
    // Action states
    isStartingStream: startStreamMutation.isPending,
    isStoppingStream: stopStreamMutation.isPending,
    isStartingRecording: startRecordingMutation.isPending,
    isStoppingRecording: stopRecordingMutation.isPending,
    isTakingSnapshot: snapshotMutation.isPending,
    isUpdatingConfig: updateConfigMutation.isPending,
    isDeletingRecording: deleteRecordingMutation.isPending,
    
    // Status helpers
    isStreamActive,
    getActiveStreamCount,
    getStreamElement,
    
    // Refresh functions
    refreshStreams: streamsQuery.refetch,
    refreshConfig: configQuery.refetch,
    refreshRecordings: recordingsQuery.refetch
  }
}

/**
 * Hook for a specific video stream
 */
export const useVideoStream = (streamId: string) => {
  const { 
    streams, 
    activeStreams, 
    startStream, 
    stopStream, 
    connectWebRTC, 
    connectHTTPStream, 
    disconnectStream,
    isStreamActive
  } = useVideo()
  
  const stream = streams.find(s => s.id === streamId)
  const mediaStream = activeStreams.get(streamId)
  const isActive = isStreamActive(streamId)
  
  const connect = useCallback(async (videoElement: HTMLVideoElement, useWebRTC: boolean = true) => {
    if (useWebRTC) {
      return await connectWebRTC(streamId, videoElement)
    } else {
      return await connectHTTPStream(streamId, videoElement)
    }
  }, [streamId, connectWebRTC, connectHTTPStream])
  
  const disconnect = useCallback(() => {
    disconnectStream(streamId)
  }, [streamId, disconnectStream])
  
  const start = useCallback((config?: Partial<VideoConfig>) => {
    startStream(streamId, config)
  }, [streamId, startStream])
  
  const stop = useCallback(() => {
    stopStream(streamId)
  }, [streamId, stopStream])
  
  return {
    stream,
    mediaStream,
    isActive,
    connect,
    disconnect,
    start,
    stop
  }
}

/**
 * Hook for video recording management
 */
export const useVideoRecording = () => {
  const { 
    recordings, 
    startRecording, 
    stopRecording, 
    deleteRecording, 
    downloadRecording,
    isStartingRecording,
    isStoppingRecording,
    isDeletingRecording,
    refreshRecordings
  } = useVideo()
  
  const activeRecordings = recordings.filter(r => r.status === 'recording')
  const completedRecordings = recordings.filter(r => r.status === 'completed')
  
  const getTotalSize = useCallback(() => {
    return recordings.reduce((total, recording) => total + (recording.file_size || 0), 0)
  }, [recordings])
  
  const getTotalDuration = useCallback(() => {
    return recordings.reduce((total, recording) => total + (recording.duration || 0), 0)
  }, [recordings])
  
  const getFormattedSize = useCallback((bytes: number) => {
    return videoService.formatFileSize(bytes)
  }, [])
  
  const getFormattedDuration = useCallback((seconds: number) => {
    return videoService.formatDuration(seconds)
  }, [])
  
  return {
    recordings,
    activeRecordings,
    completedRecordings,
    startRecording,
    stopRecording,
    deleteRecording,
    downloadRecording,
    isStartingRecording,
    isStoppingRecording,
    isDeletingRecording,
    refreshRecordings,
    getTotalSize,
    getTotalDuration,
    getFormattedSize,
    getFormattedDuration
  }
}