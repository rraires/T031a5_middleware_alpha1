import React, { useState } from 'react'
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Wifi,
  Volume2,
  Video,
  Palette,
  Bell,
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  Check,
  X
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  Button,
  Input,
  Select,
  Textarea
} from '../components'
import { useAuth } from '../hooks'
import { useThemeStore } from '../stores'
import {
  VIDEO_RESOLUTIONS,
  VIDEO_FRAME_RATES,
  VIDEO_QUALITY_LEVELS,
  AUDIO_SAMPLE_RATES,
  TTS_LANGUAGES,
  LED_BRIGHTNESS_LEVELS,
  ROBOT_SPEED_LEVELS,
  USER_ROLES
} from '../utils'
import { toast } from 'sonner'

interface UserSettings {
  profile: {
    name: string
    email: string
    avatar?: string
    timezone: string
    language: string
  }
  security: {
    currentPassword: string
    newPassword: string
    confirmPassword: string
    twoFactorEnabled: boolean
  }
  notifications: {
    emailNotifications: boolean
    pushNotifications: boolean
    soundEnabled: boolean
    robotAlerts: boolean
    systemAlerts: boolean
    maintenanceAlerts: boolean
  }
  robot: {
    defaultSpeed: string
    maxSpeed: number
    autoStandby: boolean
    standbyTimeout: number
    emergencyStopEnabled: boolean
    collisionAvoidance: boolean
  }
  video: {
    defaultResolution: string
    defaultFrameRate: number
    defaultQuality: string
    autoRecord: boolean
    recordingPath: string
    maxRecordingSize: number
  }
  audio: {
    masterVolume: number
    ttsVolume: number
    alertVolume: number
    defaultLanguage: string
    sampleRate: number
    noiseReduction: boolean
  }
  led: {
    defaultBrightness: number
    autoMode: boolean
    defaultPattern: string
    colorTheme: string
  }
  network: {
    wifiSSID: string
    wifiPassword: string
    staticIP: boolean
    ipAddress: string
    subnet: string
    gateway: string
    dns: string
  }
}

export const Settings: React.FC = () => {
  const { user } = useAuth()
  const { theme, setTheme } = useThemeStore()
  const [activeTab, setActiveTab] = useState('profile')
  const [showPasswords, setShowPasswords] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  
  const [settings, setSettings] = useState<UserSettings>({
    profile: {
      name: user?.name || '',
      email: user?.email || '',
      timezone: 'UTC-3',
      language: 'pt-BR'
    },
    security: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      twoFactorEnabled: false
    },
    notifications: {
      emailNotifications: true,
      pushNotifications: true,
      soundEnabled: true,
      robotAlerts: true,
      systemAlerts: true,
      maintenanceAlerts: false
    },
    robot: {
      defaultSpeed: 'normal',
      maxSpeed: 2.0,
      autoStandby: true,
      standbyTimeout: 300,
      emergencyStopEnabled: true,
      collisionAvoidance: true
    },
    video: {
      defaultResolution: '1920x1080',
      defaultFrameRate: 30,
      defaultQuality: 'high',
      autoRecord: false,
      recordingPath: '/recordings',
      maxRecordingSize: 1000
    },
    audio: {
      masterVolume: 80,
      ttsVolume: 70,
      alertVolume: 90,
      defaultLanguage: 'pt-BR',
      sampleRate: 44100,
      noiseReduction: true
    },
    led: {
      defaultBrightness: 80,
      autoMode: true,
      defaultPattern: 'breathing',
      colorTheme: 'blue'
    },
    network: {
      wifiSSID: '',
      wifiPassword: '',
      staticIP: false,
      ipAddress: '',
      subnet: '',
      gateway: '',
      dns: ''
    }
  })
  
  const tabs = [
    { id: 'profile', label: 'Profile', icon: <User className="w-4 h-4" /> },
    { id: 'security', label: 'Security', icon: <Shield className="w-4 h-4" /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell className="w-4 h-4" /> },
    { id: 'robot', label: 'Robot', icon: <SettingsIcon className="w-4 h-4" /> },
    { id: 'video', label: 'Video', icon: <Video className="w-4 h-4" /> },
    { id: 'audio', label: 'Audio', icon: <Volume2 className="w-4 h-4" /> },
    { id: 'led', label: 'LED', icon: <Palette className="w-4 h-4" /> },
    { id: 'network', label: 'Network', icon: <Wifi className="w-4 h-4" /> }
  ]
  
  const timezoneOptions = [
    { value: 'UTC-3', label: 'UTC-3 (Brasília)' },
    { value: 'UTC-2', label: 'UTC-2' },
    { value: 'UTC-1', label: 'UTC-1' },
    { value: 'UTC+0', label: 'UTC+0 (London)' },
    { value: 'UTC+1', label: 'UTC+1 (Paris)' },
    { value: 'UTC+8', label: 'UTC+8 (Beijing)' },
    { value: 'UTC-5', label: 'UTC-5 (New York)' },
    { value: 'UTC-8', label: 'UTC-8 (Los Angeles)' }
  ]
  
  const languageOptions = [
    { value: 'pt-BR', label: 'Português (Brasil)' },
    { value: 'en-US', label: 'English (US)' },
    { value: 'es-ES', label: 'Español' },
    { value: 'fr-FR', label: 'Français' },
    { value: 'de-DE', label: 'Deutsch' },
    { value: 'zh-CN', label: '中文 (简体)' },
    { value: 'ja-JP', label: '日本語' }
  ]
  
  const themeOptions = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'system', label: 'System' }
  ]
  
  const updateSetting = (section: keyof UserSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }))
    setHasChanges(true)
  }
  
  const handleSave = async () => {
    try {
      // Validate password change if attempted
      if (settings.security.newPassword) {
        if (settings.security.newPassword !== settings.security.confirmPassword) {
          toast.error('New passwords do not match')
          return
        }
        if (settings.security.newPassword.length < 8) {
          toast.error('Password must be at least 8 characters long')
          return
        }
      }
      
      // Here you would typically send the settings to your API
      console.log('Saving settings:', settings)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      toast.success('Settings saved successfully')
      setHasChanges(false)
      
      // Clear password fields after successful save
      setSettings(prev => ({
        ...prev,
        security: {
          ...prev.security,
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
      }))
    } catch (error) {
      toast.error('Failed to save settings')
    }
  }
  
  const handleReset = () => {
    // Reset to default values
    setSettings({
      profile: {
        name: user?.name || '',
        email: user?.email || '',
        timezone: 'UTC-3',
        language: 'pt-BR'
      },
      security: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        twoFactorEnabled: false
      },
      notifications: {
        emailNotifications: true,
        pushNotifications: true,
        soundEnabled: true,
        robotAlerts: true,
        systemAlerts: true,
        maintenanceAlerts: false
      },
      robot: {
        defaultSpeed: 'normal',
        maxSpeed: 2.0,
        autoStandby: true,
        standbyTimeout: 300,
        emergencyStopEnabled: true,
        collisionAvoidance: true
      },
      video: {
        defaultResolution: '1920x1080',
        defaultFrameRate: 30,
        defaultQuality: 'high',
        autoRecord: false,
        recordingPath: '/recordings',
        maxRecordingSize: 1000
      },
      audio: {
        masterVolume: 80,
        ttsVolume: 70,
        alertVolume: 90,
        defaultLanguage: 'pt-BR',
        sampleRate: 44100,
        noiseReduction: true
      },
      led: {
        defaultBrightness: 80,
        autoMode: true,
        defaultPattern: 'breathing',
        colorTheme: 'blue'
      },
      network: {
        wifiSSID: '',
        wifiPassword: '',
        staticIP: false,
        ipAddress: '',
        subnet: '',
        gateway: '',
        dns: ''
      }
    })
    setHasChanges(false)
    toast.success('Settings reset to defaults')
  }
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Full Name"
                value={settings.profile.name}
                onChange={(e) => updateSetting('profile', 'name', e.target.value)}
                placeholder="Enter your full name"
              />
              
              <Input
                label="Email Address"
                type="email"
                value={settings.profile.email}
                onChange={(e) => updateSetting('profile', 'email', e.target.value)}
                placeholder="Enter your email"
              />
              
              <Select
                label="Timezone"
                value={settings.profile.timezone}
                onChange={(value) => updateSetting('profile', 'timezone', value)}
                options={timezoneOptions}
                placeholder="Select timezone"
              />
              
              <Select
                label="Language"
                value={settings.profile.language}
                onChange={(value) => updateSetting('profile', 'language', value)}
                options={languageOptions}
                placeholder="Select language"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Theme
              </label>
              <Select
                value={theme}
                onChange={setTheme}
                options={themeOptions}
                placeholder="Select theme"
              />
            </div>
          </div>
        )
        
      case 'security':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Current Password"
                type={showPasswords ? 'text' : 'password'}
                value={settings.security.currentPassword}
                onChange={(e) => updateSetting('security', 'currentPassword', e.target.value)}
                placeholder="Enter current password"
              />
              
              <div className="flex items-center justify-end pt-6">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPasswords(!showPasswords)}
                  icon={showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                >
                  {showPasswords ? 'Hide' : 'Show'} Passwords
                </Button>
              </div>
              
              <Input
                label="New Password"
                type={showPasswords ? 'text' : 'password'}
                value={settings.security.newPassword}
                onChange={(e) => updateSetting('security', 'newPassword', e.target.value)}
                placeholder="Enter new password"
                helpText="Minimum 8 characters"
              />
              
              <Input
                label="Confirm New Password"
                type={showPasswords ? 'text' : 'password'}
                value={settings.security.confirmPassword}
                onChange={(e) => updateSetting('security', 'confirmPassword', e.target.value)}
                placeholder="Confirm new password"
                error={settings.security.newPassword && settings.security.confirmPassword && 
                       settings.security.newPassword !== settings.security.confirmPassword ? 
                       'Passwords do not match' : undefined}
              />
            </div>
            
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="twoFactor"
                checked={settings.security.twoFactorEnabled}
                onChange={(e) => updateSetting('security', 'twoFactorEnabled', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="twoFactor" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Enable Two-Factor Authentication
              </label>
            </div>
          </div>
        )
        
      case 'notifications':
        return (
          <div className="space-y-6">
            <div className="space-y-4">
              {Object.entries(settings.notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </label>
                    <p className="text-xs text-gray-500">
                      {key === 'emailNotifications' && 'Receive notifications via email'}
                      {key === 'pushNotifications' && 'Receive push notifications in browser'}
                      {key === 'soundEnabled' && 'Play sound for notifications'}
                      {key === 'robotAlerts' && 'Alerts about robot status and errors'}
                      {key === 'systemAlerts' && 'System performance and connectivity alerts'}
                      {key === 'maintenanceAlerts' && 'Scheduled maintenance reminders'}
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={value as boolean}
                    onChange={(e) => updateSetting('notifications', key, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>
          </div>
        )
        
      case 'robot':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Select
                label="Default Speed"
                value={settings.robot.defaultSpeed}
                onChange={(value) => updateSetting('robot', 'defaultSpeed', value)}
                options={Object.entries(ROBOT_SPEED_LEVELS).map(([key, value]) => ({
                  value: key,
                  label: `${value.name} (${value.value}x)`
                }))}
                placeholder="Select default speed"
              />
              
              <Input
                label="Maximum Speed (m/s)"
                type="number"
                value={settings.robot.maxSpeed}
                onChange={(e) => updateSetting('robot', 'maxSpeed', parseFloat(e.target.value))}
                min={0.1}
                max={5.0}
                step={0.1}
                placeholder="2.0"
              />
              
              <Input
                label="Standby Timeout (seconds)"
                type="number"
                value={settings.robot.standbyTimeout}
                onChange={(e) => updateSetting('robot', 'standbyTimeout', parseInt(e.target.value))}
                min={60}
                max={3600}
                placeholder="300"
              />
            </div>
            
            <div className="space-y-4">
              {[
                { key: 'autoStandby', label: 'Auto Standby', desc: 'Automatically enter standby mode when idle' },
                { key: 'emergencyStopEnabled', label: 'Emergency Stop', desc: 'Enable emergency stop functionality' },
                { key: 'collisionAvoidance', label: 'Collision Avoidance', desc: 'Enable automatic collision detection and avoidance' }
              ].map(({ key, label, desc }) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {label}
                    </label>
                    <p className="text-xs text-gray-500">{desc}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.robot[key as keyof typeof settings.robot] as boolean}
                    onChange={(e) => updateSetting('robot', key, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>
          </div>
        )
        
      case 'video':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Select
                label="Default Resolution"
                value={settings.video.defaultResolution}
                onChange={(value) => updateSetting('video', 'defaultResolution', value)}
                options={Object.entries(VIDEO_RESOLUTIONS).map(([key, value]) => ({
                  value: key,
                  label: `${value.name} (${value.width}x${value.height})`
                }))}
                placeholder="Select resolution"
              />
              
              <Select
                label="Default Frame Rate"
                value={settings.video.defaultFrameRate.toString()}
                onChange={(value) => updateSetting('video', 'defaultFrameRate', parseInt(value))}
                options={VIDEO_FRAME_RATES.map(rate => ({
                  value: rate.toString(),
                  label: `${rate} FPS`
                }))}
                placeholder="Select frame rate"
              />
              
              <Select
                label="Default Quality"
                value={settings.video.defaultQuality}
                onChange={(value) => updateSetting('video', 'defaultQuality', value)}
                options={Object.entries(VIDEO_QUALITY_LEVELS).map(([key, value]) => ({
                  value: key,
                  label: `${value.name} (${value.bitrate})`
                }))}
                placeholder="Select quality"
              />
              
              <Input
                label="Max Recording Size (MB)"
                type="number"
                value={settings.video.maxRecordingSize}
                onChange={(e) => updateSetting('video', 'maxRecordingSize', parseInt(e.target.value))}
                min={100}
                max={10000}
                placeholder="1000"
              />
              
              <Input
                label="Recording Path"
                value={settings.video.recordingPath}
                onChange={(e) => updateSetting('video', 'recordingPath', e.target.value)}
                placeholder="/recordings"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Auto Record
                </label>
                <p className="text-xs text-gray-500">Automatically start recording when streaming begins</p>
              </div>
              <input
                type="checkbox"
                checked={settings.video.autoRecord}
                onChange={(e) => updateSetting('video', 'autoRecord', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
          </div>
        )
        
      case 'audio':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Master Volume: {settings.audio.masterVolume}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.audio.masterVolume}
                  onChange={(e) => updateSetting('audio', 'masterVolume', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  TTS Volume: {settings.audio.ttsVolume}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.audio.ttsVolume}
                  onChange={(e) => updateSetting('audio', 'ttsVolume', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Alert Volume: {settings.audio.alertVolume}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.audio.alertVolume}
                  onChange={(e) => updateSetting('audio', 'alertVolume', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
              
              <Select
                label="Default TTS Language"
                value={settings.audio.defaultLanguage}
                onChange={(value) => updateSetting('audio', 'defaultLanguage', value)}
                options={Object.entries(TTS_LANGUAGES).map(([key, value]) => ({
                  value: key,
                  label: value.name
                }))}
                placeholder="Select language"
              />
              
              <Select
                label="Sample Rate"
                value={settings.audio.sampleRate.toString()}
                onChange={(value) => updateSetting('audio', 'sampleRate', parseInt(value))}
                options={AUDIO_SAMPLE_RATES.map(rate => ({
                  value: rate.toString(),
                  label: `${rate} Hz`
                }))}
                placeholder="Select sample rate"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Noise Reduction
                </label>
                <p className="text-xs text-gray-500">Enable noise reduction for audio input</p>
              </div>
              <input
                type="checkbox"
                checked={settings.audio.noiseReduction}
                onChange={(e) => updateSetting('audio', 'noiseReduction', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
          </div>
        )
        
      case 'led':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Default Brightness: {settings.led.defaultBrightness}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.led.defaultBrightness}
                  onChange={(e) => updateSetting('led', 'defaultBrightness', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
              
              <Select
                label="Default Pattern"
                value={settings.led.defaultPattern}
                onChange={(value) => updateSetting('led', 'defaultPattern', value)}
                options={[
                  { value: 'solid', label: 'Solid' },
                  { value: 'breathing', label: 'Breathing' },
                  { value: 'pulse', label: 'Pulse' },
                  { value: 'rainbow', label: 'Rainbow' },
                  { value: 'wave', label: 'Wave' },
                  { value: 'strobe', label: 'Strobe' }
                ]}
                placeholder="Select pattern"
              />
              
              <Select
                label="Color Theme"
                value={settings.led.colorTheme}
                onChange={(value) => updateSetting('led', 'colorTheme', value)}
                options={[
                  { value: 'blue', label: 'Blue' },
                  { value: 'red', label: 'Red' },
                  { value: 'green', label: 'Green' },
                  { value: 'purple', label: 'Purple' },
                  { value: 'orange', label: 'Orange' },
                  { value: 'white', label: 'White' },
                  { value: 'rainbow', label: 'Rainbow' }
                ]}
                placeholder="Select color theme"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Auto Mode
                </label>
                <p className="text-xs text-gray-500">Automatically adjust LED patterns based on robot status</p>
              </div>
              <input
                type="checkbox"
                checked={settings.led.autoMode}
                onChange={(e) => updateSetting('led', 'autoMode', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
          </div>
        )
        
      case 'network':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="WiFi SSID"
                value={settings.network.wifiSSID}
                onChange={(e) => updateSetting('network', 'wifiSSID', e.target.value)}
                placeholder="Enter WiFi network name"
              />
              
              <Input
                label="WiFi Password"
                type={showPasswords ? 'text' : 'password'}
                value={settings.network.wifiPassword}
                onChange={(e) => updateSetting('network', 'wifiPassword', e.target.value)}
                placeholder="Enter WiFi password"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Use Static IP
                </label>
                <p className="text-xs text-gray-500">Configure static IP address instead of DHCP</p>
              </div>
              <input
                type="checkbox"
                checked={settings.network.staticIP}
                onChange={(e) => updateSetting('network', 'staticIP', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
            
            {settings.network.staticIP && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  label="IP Address"
                  value={settings.network.ipAddress}
                  onChange={(e) => updateSetting('network', 'ipAddress', e.target.value)}
                  placeholder="192.168.1.100"
                />
                
                <Input
                  label="Subnet Mask"
                  value={settings.network.subnet}
                  onChange={(e) => updateSetting('network', 'subnet', e.target.value)}
                  placeholder="255.255.255.0"
                />
                
                <Input
                  label="Gateway"
                  value={settings.network.gateway}
                  onChange={(e) => updateSetting('network', 'gateway', e.target.value)}
                  placeholder="192.168.1.1"
                />
                
                <Input
                  label="DNS Server"
                  value={settings.network.dns}
                  onChange={(e) => updateSetting('network', 'dns', e.target.value)}
                  placeholder="8.8.8.8"
                />
              </div>
            )}
          </div>
        )
        
      default:
        return null
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Configure your robot and application preferences
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={handleReset}
            icon={<RotateCcw className="w-4 h-4" />}
            disabled={!hasChanges}
          >
            Reset
          </Button>
          
          <Button
            onClick={handleSave}
            icon={<Save className="w-4 h-4" />}
            disabled={!hasChanges}
          >
            Save Changes
          </Button>
        </div>
      </div>
      
      {/* Settings Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-0">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 text-left text-sm font-medium rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-r-2 border-blue-500'
                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </CardContent>
          </Card>
        </div>
        
        {/* Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                {tabs.find(tab => tab.id === activeTab)?.icon}
                <span>{tabs.find(tab => tab.id === activeTab)?.label} Settings</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {renderTabContent()}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Changes Indicator */}
      {hasChanges && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">You have unsaved changes</span>
        </div>
      )}
    </div>
  )
}