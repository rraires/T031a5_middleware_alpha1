import { ApiResponse, VideoStream, VideoSettings } from '../types'
import { apiClient } from './apiClient'

interface VideoStreamResponse {
  streams: VideoStream[]
  active_streams: number
  total_streams: number
}

interface StreamControlResponse {
  stream_id: string
  status: 'started' | 'stopped' | 'paused' | 'error'
  message?: string
}

interface RecordingResponse {
  recording_id: string
  status: 'started' | 'stopped' | 'paused' | 'error'
  filename?: string
  duration?: number
  file_size?: number
}

interface SnapshotResponse {
  snapshot_id: string
  filename: string
  url: string
  timestamp: string
}

interface VideoSettingsResponse {
  settings: VideoSettings
  applied: boolean
}

class VideoService {
  private readonly baseUrl = '/api/video'
  private activeStreams: Map<string, MediaStream> = new Map()
  private streamElements: Map<string, HTMLVideoElement> = new Map()

  /**
   * Get available video streams
   */
  async getStreams(): Promise<ApiResponse<VideoStreamResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<VideoStreamResponse>>(
        `${this.baseUrl}/streams`
      )
      return response.data
    } catch (error: any) {
      console.error('Get video streams error:', error)
      return {
        success: false,
        error: {
          code: 'GET_STREAMS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get video streams'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Start video stream
   */
  async startStream(streamId: string): Promise<ApiResponse<StreamControlResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<StreamControlResponse>>(
        `${this.baseUrl}/streams/${streamId}/start`
      )
      return response.data
    } catch (error: any) {
      console.error('Start stream error:', error)
      return {
        success: false,
        error: {
          code: 'START_STREAM_FAILED',
          message: error.response?.data?.error?.message || 'Failed to start stream'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Stop video stream
   */
  async stopStream(streamId: string): Promise<ApiResponse<StreamControlResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<StreamControlResponse>>(
        `${this.baseUrl}/streams/${streamId}/stop`
      )
      
      // Clean up local stream resources
      this.cleanupStream(streamId)
      
      return response.data
    } catch (error: any) {
      console.error('Stop stream error:', error)
      return {
        success: false,
        error: {
          code: 'STOP_STREAM_FAILED',
          message: error.response?.data?.error?.message || 'Failed to stop stream'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Pause video stream
   */
  async pauseStream(streamId: string): Promise<ApiResponse<StreamControlResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<StreamControlResponse>>(
        `${this.baseUrl}/streams/${streamId}/pause`
      )
      return response.data
    } catch (error: any) {
      console.error('Pause stream error:', error)
      return {
        success: false,
        error: {
          code: 'PAUSE_STREAM_FAILED',
          message: error.response?.data?.error?.message || 'Failed to pause stream'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Resume video stream
   */
  async resumeStream(streamId: string): Promise<ApiResponse<StreamControlResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<StreamControlResponse>>(
        `${this.baseUrl}/streams/${streamId}/resume`
      )
      return response.data
    } catch (error: any) {
      console.error('Resume stream error:', error)
      return {
        success: false,
        error: {
          code: 'RESUME_STREAM_FAILED',
          message: error.response?.data?.error?.message || 'Failed to resume stream'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Start recording
   */
  async startRecording(
    streamId: string,
    filename?: string
  ): Promise<ApiResponse<RecordingResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<RecordingResponse>>(
        `${this.baseUrl}/streams/${streamId}/record/start`,
        { filename }
      )
      return response.data
    } catch (error: any) {
      console.error('Start recording error:', error)
      return {
        success: false,
        error: {
          code: 'START_RECORDING_FAILED',
          message: error.response?.data?.error?.message || 'Failed to start recording'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Stop recording
   */
  async stopRecording(recordingId: string): Promise<ApiResponse<RecordingResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<RecordingResponse>>(
        `${this.baseUrl}/recordings/${recordingId}/stop`
      )
      return response.data
    } catch (error: any) {
      console.error('Stop recording error:', error)
      return {
        success: false,
        error: {
          code: 'STOP_RECORDING_FAILED',
          message: error.response?.data?.error?.message || 'Failed to stop recording'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Take snapshot
   */
  async takeSnapshot(
    streamId: string,
    filename?: string
  ): Promise<ApiResponse<SnapshotResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<SnapshotResponse>>(
        `${this.baseUrl}/streams/${streamId}/snapshot`,
        { filename }
      )
      return response.data
    } catch (error: any) {
      console.error('Take snapshot error:', error)
      return {
        success: false,
        error: {
          code: 'SNAPSHOT_FAILED',
          message: error.response?.data?.error?.message || 'Failed to take snapshot'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get video settings
   */
  async getSettings(): Promise<ApiResponse<VideoSettingsResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<VideoSettingsResponse>>(
        `${this.baseUrl}/settings`
      )
      return response.data
    } catch (error: any) {
      console.error('Get video settings error:', error)
      return {
        success: false,
        error: {
          code: 'GET_SETTINGS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get video settings'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Update video settings
   */
  async updateSettings(settings: Partial<VideoSettings>): Promise<ApiResponse<VideoSettingsResponse>> {
    try {
      const response = await apiClient.put<ApiResponse<VideoSettingsResponse>>(
        `${this.baseUrl}/settings`,
        settings
      )
      return response.data
    } catch (error: any) {
      console.error('Update video settings error:', error)
      return {
        success: false,
        error: {
          code: 'UPDATE_SETTINGS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to update video settings'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get recordings list
   */
  async getRecordings(
    limit?: number,
    offset?: number
  ): Promise<ApiResponse<any>> {
    try {
      const params: any = {}
      if (limit) params.limit = limit
      if (offset) params.offset = offset
      
      const response = await apiClient.get<ApiResponse<any>>(
        `${this.baseUrl}/recordings`,
        { params }
      )
      return response.data
    } catch (error: any) {
      console.error('Get recordings error:', error)
      return {
        success: false,
        error: {
          code: 'GET_RECORDINGS_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get recordings'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Delete recording
   */
  async deleteRecording(recordingId: string): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `${this.baseUrl}/recordings/${recordingId}`
      )
      return response.data
    } catch (error: any) {
      console.error('Delete recording error:', error)
      return {
        success: false,
        error: {
          code: 'DELETE_RECORDING_FAILED',
          message: error.response?.data?.error?.message || 'Failed to delete recording'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Download recording
   */
  async downloadRecording(
    recordingId: string,
    filename?: string,
    onProgress?: (progress: number) => void
  ): Promise<void> {
    try {
      await apiClient.downloadFile(
        `${this.baseUrl}/recordings/${recordingId}/download`,
        filename,
        onProgress
      )
    } catch (error: any) {
      console.error('Download recording error:', error)
      throw new Error(error.response?.data?.error?.message || 'Failed to download recording')
    }
  }

  /**
   * Client-side stream management
   */

  /**
   * Connect to WebRTC stream
   */
  async connectWebRTCStream(
    streamId: string,
    videoElement: HTMLVideoElement,
    iceServers?: RTCIceServer[]
  ): Promise<void> {
    try {
      const peerConnection = new RTCPeerConnection({
        iceServers: iceServers || [
          { urls: 'stun:stun.l.google.com:19302' }
        ]
      })

      // Handle incoming stream
      peerConnection.ontrack = (event) => {
        const [stream] = event.streams
        videoElement.srcObject = stream
        this.activeStreams.set(streamId, stream)
        this.streamElements.set(streamId, videoElement)
      }

      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          // Send ICE candidate to server via WebSocket
          this.sendICECandidate(streamId, event.candidate)
        }
      }

      // Create offer and set local description
      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)

      // Send offer to server
      await this.sendWebRTCOffer(streamId, offer)

    } catch (error) {
      console.error('WebRTC connection error:', error)
      throw error
    }
  }

  /**
   * Connect to HTTP stream (MJPEG/HLS)
   */
  connectHTTPStream(
    streamId: string,
    videoElement: HTMLVideoElement,
    streamUrl: string
  ): void {
    try {
      videoElement.src = streamUrl
      videoElement.load()
      
      // Store reference for cleanup
      this.streamElements.set(streamId, videoElement)
      
      // Handle errors
      videoElement.onerror = (error) => {
        console.error('HTTP stream error:', error)
        this.cleanupStream(streamId)
      }
      
    } catch (error) {
      console.error('HTTP stream connection error:', error)
      throw error
    }
  }

  /**
   * Disconnect stream
   */
  disconnectStream(streamId: string): void {
    this.cleanupStream(streamId)
  }

  /**
   * Clean up stream resources
   */
  private cleanupStream(streamId: string): void {
    // Stop media stream
    const stream = this.activeStreams.get(streamId)
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      this.activeStreams.delete(streamId)
    }

    // Clear video element
    const videoElement = this.streamElements.get(streamId)
    if (videoElement) {
      videoElement.srcObject = null
      videoElement.src = ''
      this.streamElements.delete(streamId)
    }
  }

  /**
   * Send WebRTC offer to server
   */
  private async sendWebRTCOffer(
    streamId: string,
    offer: RTCSessionDescriptionInit
  ): Promise<void> {
    try {
      await apiClient.post(
        `${this.baseUrl}/streams/${streamId}/webrtc/offer`,
        { offer }
      )
    } catch (error) {
      console.error('Failed to send WebRTC offer:', error)
      throw error
    }
  }

  /**
   * Send ICE candidate to server
   */
  private sendICECandidate(
    streamId: string,
    candidate: RTCIceCandidate
  ): void {
    // This would typically be sent via WebSocket
    // Implementation depends on WebSocket service
    console.log('Sending ICE candidate:', { streamId, candidate })
  }

  /**
   * Utility methods
   */

  /**
   * Check if stream is active
   */
  isStreamActive(streamId: string): boolean {
    return this.activeStreams.has(streamId)
  }

  /**
   * Get active streams count
   */
  getActiveStreamsCount(): number {
    return this.activeStreams.size
  }

  /**
   * Get stream element
   */
  getStreamElement(streamId: string): HTMLVideoElement | undefined {
    return this.streamElements.get(streamId)
  }

  /**
   * Get stream URL for HTTP streaming
   */
  getStreamUrl(streamId: string, format: 'mjpeg' | 'hls' = 'mjpeg'): string {
    const baseUrl = apiClient.defaults?.baseURL || ''
    return `${baseUrl}${this.baseUrl}/streams/${streamId}/${format}`
  }

  /**
   * Get snapshot URL
   */
  getSnapshotUrl(snapshotId: string): string {
    const baseUrl = apiClient.defaults?.baseURL || ''
    return `${baseUrl}${this.baseUrl}/snapshots/${snapshotId}`
  }

  /**
   * Get recording URL
   */
  getRecordingUrl(recordingId: string): string {
    const baseUrl = apiClient.defaults?.baseURL || ''
    return `${baseUrl}${this.baseUrl}/recordings/${recordingId}/download`
  }

  /**
   * Format file size
   */
  formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  /**
   * Format duration
   */
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  }

  /**
   * Clean up all streams on component unmount
   */
  cleanup(): void {
    this.activeStreams.forEach((_, streamId) => {
      this.cleanupStream(streamId)
    })
  }
}

export const videoService = new VideoService()