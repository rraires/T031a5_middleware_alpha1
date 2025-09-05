import React, { useState, useRef, useEffect } from 'react'
import {
  Play,
  Pause,
  Square,
  Camera,
  Video as VideoIcon,
  Download,
  Trash2,
  Settings,
  Maximize,
  Volume2,
  VolumeX,
  RotateCw,
  Zap,
  Eye,
  EyeOff
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  Button,
  ButtonGroup,
  Input,
  Select
} from '../components'
import { useVideo, useVideoStream, useVideoRecording } from '../hooks'
import {
  VIDEO_RESOLUTIONS,
  VIDEO_FRAME_RATES,
  VIDEO_QUALITY,
  formatFileSize,
  formatDuration
} from '../utils'
import { toast } from 'sonner'

export const Video: React.FC = () => {
  const {
    streams,
    recordings,
    videoConfig,
    startStream,
    stopStream,
    startRecording,
    stopRecording,
    takeSnapshot,
    updateConfig,
    deleteRecording,
    downloadRecording,
    isLoading
  } = useVideo()
  
  const { activeRecordings, completedRecordings, totalSize, totalDuration } = useVideoRecording()
  
  const [selectedCamera, setSelectedCamera] = useState<string>('front')
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [showSettings, setShowSettings] = useState<boolean>(false)
  const [recordingName, setRecordingName] = useState<string>('')
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const fullscreenRef = useRef<HTMLDivElement>(null)
  
  const { streamData, isConnected, connectionType } = useVideoStream(selectedCamera)
  
  // Camera options
  const cameraOptions = [
    { value: 'front', label: 'Front Camera' },
    { value: 'rear', label: 'Rear Camera' },
    { value: 'left', label: 'Left Camera' },
    { value: 'right', label: 'Right Camera' }
  ]
  
  const resolutionOptions = Object.entries(VIDEO_RESOLUTIONS).map(([key, value]) => ({
    value: key,
    label: `${value.width}x${value.height} (${key})`
  }))
  
  const frameRateOptions = VIDEO_FRAME_RATES.map(rate => ({
    value: rate.toString(),
    label: `${rate} FPS`
  }))
  
  const qualityOptions = Object.entries(VIDEO_QUALITY).map(([key, value]) => ({
    value: key,
    label: `${key} (${value}%)`
  }))
  
  // Stream controls
  const handleStartStream = async () => {
    try {
      await startStream(selectedCamera)
      toast.success(`Started ${selectedCamera} camera stream`)
    } catch (error) {
      toast.error('Failed to start stream')
    }
  }
  
  const handleStopStream = async () => {
    try {
      await stopStream(selectedCamera)
      toast.success('Stream stopped')
    } catch (error) {
      toast.error('Failed to stop stream')
    }
  }
  
  // Recording controls
  const handleStartRecording = async () => {
    try {
      const name = recordingName || `recording_${Date.now()}`
      await startRecording(selectedCamera, { name })
      toast.success('Recording started')
      setRecordingName('')
    } catch (error) {
      toast.error('Failed to start recording')
    }
  }
  
  const handleStopRecording = async () => {
    try {
      await stopRecording(selectedCamera)
      toast.success('Recording stopped')
    } catch (error) {
      toast.error('Failed to stop recording')
    }
  }
  
  const handleTakeSnapshot = async () => {
    try {
      await takeSnapshot(selectedCamera)
      toast.success('Snapshot taken')
    } catch (error) {
      toast.error('Failed to take snapshot')
    }
  }
  
  // Settings
  const handleUpdateConfig = async (config: any) => {
    try {
      await updateConfig(selectedCamera, config)
      toast.success('Settings updated')
    } catch (error) {
      toast.error('Failed to update settings')
    }
  }
  
  // Fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      fullscreenRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }
  
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])
  
  const isRecording = activeRecordings.some(rec => rec.camera === selectedCamera)
  const isStreaming = streams.some(stream => stream.camera === selectedCamera && stream.status === 'active')
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Video Control
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor camera feeds and manage recordings
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => setShowSettings(!showSettings)}
            icon={<Settings className="w-4 h-4" />}
          >
            Settings
          </Button>
        </div>
      </div>
      
      {/* Camera Selection */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Select
                value={selectedCamera}
                onChange={setSelectedCamera}
                options={cameraOptions}
                placeholder="Select camera"
              />
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Status:
                </span>
                <span className={`text-sm font-medium ${
                  isConnected
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {connectionType && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Type:
                  </span>
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {connectionType}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                isStreaming ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
              }`}></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isStreaming ? 'Streaming' : 'Offline'}
              </span>
              
              {isRecording && (
                <>
                  <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
                  <span className="text-sm text-red-600 dark:text-red-400">
                    Recording
                  </span>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Player */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Live Feed - {cameraOptions.find(c => c.value === selectedCamera)?.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div ref={fullscreenRef} className="relative bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  className="w-full aspect-video object-cover"
                  autoPlay
                  muted={isMuted}
                  playsInline
                >
                  <source src={streamData?.url} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
                
                {/* Video Overlay Controls */}
                <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 hover:opacity-100">
                  <div className="flex items-center space-x-4">
                    {isStreaming ? (
                      <Button
                        size="lg"
                        variant="danger"
                        onClick={handleStopStream}
                        icon={<Pause className="w-6 h-6" />}
                        disabled={isLoading}
                      >
                        Stop Stream
                      </Button>
                    ) : (
                      <Button
                        size="lg"
                        onClick={handleStartStream}
                        icon={<Play className="w-6 h-6" />}
                        disabled={isLoading}
                      >
                        Start Stream
                      </Button>
                    )}
                  </div>
                </div>
                
                {/* Video Controls Bar */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setIsMuted(!isMuted)}
                        icon={isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                        className="text-white hover:bg-white hover:bg-opacity-20"
                      >
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleTakeSnapshot}
                        icon={<Camera className="w-4 h-4" />}
                        disabled={!isStreaming || isLoading}
                        className="text-white hover:bg-white hover:bg-opacity-20"
                      >
                      </Button>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-white text-sm">
                        {streamData?.resolution || '1280x720'} • {streamData?.fps || 30} FPS
                      </span>
                      
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={toggleFullscreen}
                        icon={<Maximize className="w-4 h-4" />}
                        className="text-white hover:bg-white hover:bg-opacity-20"
                      >
                      </Button>
                    </div>
                  </div>
                </div>
                
                {/* No Signal Overlay */}
                {!isStreaming && (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                    <div className="text-center text-white">
                      <EyeOff className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium">No Signal</p>
                      <p className="text-sm opacity-75">Camera stream is not active</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Controls Panel */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Stream Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Stream Controls */}
              <div className="space-y-2">
                <ButtonGroup fullWidth>
                  {isStreaming ? (
                    <Button
                      variant="danger"
                      onClick={handleStopStream}
                      icon={<Square className="w-4 h-4" />}
                      disabled={isLoading}
                    >
                      Stop Stream
                    </Button>
                  ) : (
                    <Button
                      onClick={handleStartStream}
                      icon={<Play className="w-4 h-4" />}
                      disabled={isLoading}
                    >
                      Start Stream
                    </Button>
                  )}
                  
                  <Button
                    variant="outline"
                    onClick={handleTakeSnapshot}
                    icon={<Camera className="w-4 h-4" />}
                    disabled={!isStreaming || isLoading}
                  >
                    Snapshot
                  </Button>
                </ButtonGroup>
              </div>
              
              {/* Recording Controls */}
              <div className="space-y-2">
                <Input
                  value={recordingName}
                  onChange={(e) => setRecordingName(e.target.value)}
                  placeholder="Recording name (optional)"
                  disabled={isRecording}
                />
                
                {isRecording ? (
                  <Button
                    fullWidth
                    variant="danger"
                    onClick={handleStopRecording}
                    icon={<Square className="w-4 h-4" />}
                    disabled={isLoading}
                  >
                    Stop Recording
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    onClick={handleStartRecording}
                    icon={<VideoIcon className="w-4 h-4" />}
                    disabled={!isStreaming || isLoading}
                  >
                    Start Recording
                  </Button>
                )}
              </div>
              
              {/* Recording Stats */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Active:</span>
                    <span className="text-gray-900 dark:text-white">
                      {activeRecordings.length} recording{activeRecordings.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Completed:</span>
                    <span className="text-gray-900 dark:text-white">
                      {completedRecordings.length} recording{completedRecordings.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Size:</span>
                    <span className="text-gray-900 dark:text-white">
                      {formatFileSize(totalSize)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Duration:</span>
                    <span className="text-gray-900 dark:text-white">
                      {formatDuration(totalDuration)}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Settings Panel */}
          {showSettings && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Video Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Resolution
                  </label>
                  <Select
                    value={videoConfig?.resolution || 'HD'}
                    onChange={(value) => handleUpdateConfig({ resolution: value })}
                    options={resolutionOptions}
                    placeholder="Select resolution"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Frame Rate
                  </label>
                  <Select
                    value={videoConfig?.fps?.toString() || '30'}
                    onChange={(value) => handleUpdateConfig({ fps: parseInt(value) })}
                    options={frameRateOptions}
                    placeholder="Select frame rate"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quality
                  </label>
                  <Select
                    value={videoConfig?.quality || 'HIGH'}
                    onChange={(value) => handleUpdateConfig({ quality: value })}
                    options={qualityOptions}
                    placeholder="Select quality"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      
      {/* Recordings List */}
      <Card>
        <CardHeader>
          <CardTitle>Recordings</CardTitle>
        </CardHeader>
        <CardContent>
          {recordings.length === 0 ? (
            <div className="text-center py-8">
              <VideoIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No recordings available</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recordings.map((recording) => (
                <div
                  key={recording.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <VideoIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {recording.name}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDuration(recording.duration)} • {formatFileSize(recording.size)} • {recording.camera}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        {new Date(recording.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadRecording(recording.id)}
                      icon={<Download className="w-4 h-4" />}
                    >
                      Download
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => deleteRecording(recording.id)}
                      icon={<Trash2 className="w-4 h-4" />}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}