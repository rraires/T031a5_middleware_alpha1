import React from 'react'
import {
  Bot,
  Battery,
  Wifi,
  Camera,
  Activity,
  Thermometer,
  Gauge,
  MapPin,
  Clock,
  AlertTriangle
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  StatCard,
  Button
} from '../components'
import { useRobot, useWebSocket, useSensorData } from '../hooks'
import {
  formatBatteryLevel,
  formatUptime,
  formatTemperature,
  formatCoordinates,
  ROBOT_STATUS,
  CONNECTION_STATUS
} from '../utils'
import { toast } from 'sonner'

export const Dashboard: React.FC = () => {
  const { robotStatus, systemMetrics, isLoading, emergencyStop } = useRobot()
  const { connectionStatus, isConnected } = useWebSocket()
  const { sensorData } = useSensorData(['imu', 'battery', 'temperature', 'gps'])
  
  const handleEmergencyStop = async () => {
    try {
      await emergencyStop()
      toast.success('Emergency stop activated')
    } catch (error) {
      toast.error('Failed to activate emergency stop')
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case ROBOT_STATUS.ONLINE:
        return 'text-green-600 dark:text-green-400'
      case ROBOT_STATUS.OFFLINE:
        return 'text-red-600 dark:text-red-400'
      case ROBOT_STATUS.ERROR:
        return 'text-red-600 dark:text-red-400'
      case ROBOT_STATUS.CHARGING:
        return 'text-blue-600 dark:text-blue-400'
      case ROBOT_STATUS.LOW_BATTERY:
        return 'text-yellow-600 dark:text-yellow-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }
  
  const getConnectionColor = (status: string) => {
    switch (status) {
      case CONNECTION_STATUS.CONNECTED:
        return 'text-green-600 dark:text-green-400'
      case CONNECTION_STATUS.CONNECTING:
        return 'text-yellow-600 dark:text-yellow-400'
      default:
        return 'text-red-600 dark:text-red-400'
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Robot Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor and control your Unitree robot
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="danger"
            onClick={handleEmergencyStop}
            icon={<AlertTriangle className="w-4 h-4" />}
            disabled={!isConnected}
          >
            Emergency Stop
          </Button>
        </div>
      </div>
      
      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Robot Status"
          value={robotStatus?.status || 'Unknown'}
          icon={<Bot className={getStatusColor(robotStatus?.status || '')} />}
          description={robotStatus?.mode || 'No mode data'}
        />
        
        <StatCard
          title="Connection"
          value={connectionStatus}
          icon={<Wifi className={getConnectionColor(connectionStatus)} />}
          description={isConnected ? 'Real-time data' : 'Offline mode'}
        />
        
        <StatCard
          title="Battery Level"
          value={`${robotStatus?.battery_level || 0}%`}
          icon={<Battery className="text-blue-600 dark:text-blue-400" />}
          description={formatBatteryLevel(robotStatus?.battery_level || 0).status}
          trend={{
            value: robotStatus?.battery_level || 0,
            label: 'charge',
            direction: (robotStatus?.battery_level || 0) > 50 ? 'up' : 'down'
          }}
        />
        
        <StatCard
          title="Uptime"
          value={formatUptime(systemMetrics?.uptime || 0)}
          icon={<Clock className="text-purple-600 dark:text-purple-400" />}
          description="System running time"
        />
      </div>
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Robot Information */}
        <Card>
          <CardHeader>
            <CardTitle>Robot Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Model
                </span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {robotStatus?.model || 'Unitree Go1'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Firmware Version
                </span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {robotStatus?.firmware_version || 'v1.0.0'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Serial Number
                </span>
                <span className="text-sm text-gray-900 dark:text-white font-mono">
                  {robotStatus?.serial_number || 'UN-001-2024'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Last Update
                </span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {robotStatus?.last_update ? new Date(robotStatus.last_update).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* System Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    CPU Usage
                  </span>
                </div>
                <span className="text-sm text-gray-900 dark:text-white">
                  {systemMetrics?.cpu_usage?.toFixed(1) || 0}%
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Gauge className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Memory Usage
                  </span>
                </div>
                <span className="text-sm text-gray-900 dark:text-white">
                  {systemMetrics?.memory_usage?.toFixed(1) || 0}%
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Thermometer className="w-4 h-4 text-red-600 dark:text-red-400" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Temperature
                  </span>
                </div>
                <span className="text-sm text-gray-900 dark:text-white">
                  {formatTemperature(sensorData.temperature?.[0]?.value || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Position
                  </span>
                </div>
                <span className="text-sm text-gray-900 dark:text-white font-mono">
                  {sensorData.gps?.[0] ? 
                    formatCoordinates(sensorData.gps[0].value.latitude, sensorData.gps[0].value.longitude) :
                    'No GPS data'
                  }
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Sensor Data */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sensor Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* IMU Data */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                IMU Sensor
              </h4>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Accel X:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.imu?.[0]?.value?.acceleration?.x?.toFixed(3) || '0.000'} m/s²
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Accel Y:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.imu?.[0]?.value?.acceleration?.y?.toFixed(3) || '0.000'} m/s²
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Accel Z:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.imu?.[0]?.value?.acceleration?.z?.toFixed(3) || '0.000'} m/s²
                  </span>
                </div>
              </div>
            </div>
            
            {/* Battery Data */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Battery Status
              </h4>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Voltage:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.battery?.[0]?.value?.voltage?.toFixed(2) || '0.00'} V
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Current:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.battery?.[0]?.value?.current?.toFixed(2) || '0.00'} A
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Temperature:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    {sensorData.battery?.[0]?.value?.temperature?.toFixed(1) || '0.0'} °C
                  </span>
                </div>
              </div>
            </div>
            
            {/* Camera Status */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Camera Status
              </h4>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Status:</span>
                  <span className="text-green-600 dark:text-green-400 font-medium">
                    Active
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Resolution:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    1280x720
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">FPS:</span>
                  <span className="text-gray-900 dark:text-white font-mono">
                    30
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}