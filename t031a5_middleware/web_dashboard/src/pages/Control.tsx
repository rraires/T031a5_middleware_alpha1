import React, { useState } from 'react'
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  RotateCw,
  Zap,
  Settings,
  AlertTriangle
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
import { useRobot, useMovement } from '../hooks'
import { ROBOT_MODES, MOVEMENT_SPEEDS } from '../utils'
import { toast } from 'sonner'

export const Control: React.FC = () => {
  const {
    robotStatus,
    moveRobot,
    stopMovement,
    emergencyStop,
    calibrateRobot,
    setPowerState,
    resetPosition,
    isLoading
  } = useRobot()
  
  const { isMoving, currentCommand } = useMovement()
  
  const [selectedSpeed, setSelectedSpeed] = useState<number>(MOVEMENT_SPEEDS.NORMAL)
  const [customSpeed, setCustomSpeed] = useState<string>('')
  const [selectedMode, setSelectedMode] = useState<string>(ROBOT_MODES.WALK)
  const [isAdvancedMode, setIsAdvancedMode] = useState<boolean>(false)
  
  // Movement commands
  const handleMove = async (direction: string) => {
    try {
      const speed = customSpeed ? parseFloat(customSpeed) : selectedSpeed
      await moveRobot({
        direction,
        speed,
        mode: selectedMode
      })
      toast.success(`Moving ${direction}`)
    } catch (error) {
      toast.error(`Failed to move ${direction}`)
    }
  }
  
  const handleStop = async () => {
    try {
      await stopMovement()
      toast.success('Movement stopped')
    } catch (error) {
      toast.error('Failed to stop movement')
    }
  }
  
  const handleEmergencyStop = async () => {
    try {
      await emergencyStop()
      toast.success('Emergency stop activated')
    } catch (error) {
      toast.error('Failed to activate emergency stop')
    }
  }
  
  const handleCalibrate = async () => {
    try {
      await calibrateRobot()
      toast.success('Robot calibration started')
    } catch (error) {
      toast.error('Failed to start calibration')
    }
  }
  
  const handlePowerToggle = async () => {
    try {
      const newState = robotStatus?.power_state === 'on' ? 'off' : 'on'
      await setPowerState(newState)
      toast.success(`Robot power ${newState}`)
    } catch (error) {
      toast.error('Failed to change power state')
    }
  }
  
  const handleResetPosition = async () => {
    try {
      await resetPosition()
      toast.success('Position reset')
    } catch (error) {
      toast.error('Failed to reset position')
    }
  }
  
  const speedOptions = [
    { value: MOVEMENT_SPEEDS.SLOW.toString(), label: 'Slow' },
    { value: MOVEMENT_SPEEDS.NORMAL.toString(), label: 'Normal' },
    { value: MOVEMENT_SPEEDS.FAST.toString(), label: 'Fast' }
  ]
  
  const modeOptions = [
    { value: ROBOT_MODES.WALK, label: 'Walk' },
    { value: ROBOT_MODES.TROT, label: 'Trot' },
    { value: ROBOT_MODES.RUN, label: 'Run' },
    { value: ROBOT_MODES.STAND, label: 'Stand' },
    { value: ROBOT_MODES.LIE, label: 'Lie Down' }
  ]
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Robot Control
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Control your Unitree robot movement and behavior
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => setIsAdvancedMode(!isAdvancedMode)}
            icon={<Settings className="w-4 h-4" />}
          >
            {isAdvancedMode ? 'Basic' : 'Advanced'}
          </Button>
          
          <Button
            variant="danger"
            onClick={handleEmergencyStop}
            icon={<AlertTriangle className="w-4 h-4" />}
            disabled={isLoading}
          >
            Emergency Stop
          </Button>
        </div>
      </div>
      
      {/* Status Bar */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Status:
                </span>
                <span className={`text-sm font-medium ${
                  robotStatus?.status === 'online' 
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {robotStatus?.status || 'Unknown'}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Mode:
                </span>
                <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                  {robotStatus?.mode || 'Unknown'}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Moving:
                </span>
                <span className={`text-sm font-medium ${
                  isMoving 
                    ? 'text-yellow-600 dark:text-yellow-400'
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {isMoving ? currentCommand || 'Yes' : 'No'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Battery:
              </span>
              <span className={`text-sm font-medium ${
                (robotStatus?.battery_level || 0) > 20
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>
                {robotStatus?.battery_level || 0}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Movement Controls */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Movement Controls</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Directional Controls */}
              <div className="flex flex-col items-center space-y-4">
                {/* Forward */}
                <Button
                  size="lg"
                  onClick={() => handleMove('forward')}
                  disabled={isLoading}
                  icon={<ArrowUp className="w-6 h-6" />}
                  className="w-20 h-20"
                >
                </Button>
                
                {/* Left, Stop, Right */}
                <div className="flex items-center space-x-4">
                  <Button
                    size="lg"
                    onClick={() => handleMove('left')}
                    disabled={isLoading}
                    icon={<ArrowLeft className="w-6 h-6" />}
                    className="w-20 h-20"
                  >
                  </Button>
                  
                  <Button
                    size="lg"
                    variant="danger"
                    onClick={handleStop}
                    disabled={isLoading}
                    icon={<Square className="w-6 h-6" />}
                    className="w-20 h-20"
                  >
                  </Button>
                  
                  <Button
                    size="lg"
                    onClick={() => handleMove('right')}
                    disabled={isLoading}
                    icon={<ArrowRight className="w-6 h-6" />}
                    className="w-20 h-20"
                  >
                  </Button>
                </div>
                
                {/* Backward */}
                <Button
                  size="lg"
                  onClick={() => handleMove('backward')}
                  disabled={isLoading}
                  icon={<ArrowDown className="w-6 h-6" />}
                  className="w-20 h-20"
                >
                </Button>
              </div>
              
              {/* Rotation Controls */}
              <div className="mt-8 flex justify-center space-x-4">
                <Button
                  onClick={() => handleMove('rotate_left')}
                  disabled={isLoading}
                  icon={<RotateCcw className="w-5 h-5" />}
                >
                  Rotate Left
                </Button>
                
                <Button
                  onClick={() => handleMove('rotate_right')}
                  disabled={isLoading}
                  icon={<RotateCw className="w-5 h-5" />}
                >
                  Rotate Right
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Settings Panel */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Control Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Movement Mode */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Movement Mode
                </label>
                <Select
                  value={selectedMode}
                  onChange={(value) => setSelectedMode(value)}
                  options={modeOptions}
                  placeholder="Select mode"
                />
              </div>
              
              {/* Speed Control */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Speed
                </label>
                <Select
                  value={selectedSpeed.toString()}
                  onChange={(value) => {
                    setSelectedSpeed(parseFloat(value))
                    setCustomSpeed('')
                  }}
                  options={speedOptions}
                  placeholder="Select speed"
                />
              </div>
              
              {/* Custom Speed */}
              {isAdvancedMode && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Custom Speed (m/s)
                  </label>
                  <Input
                    type="number"
                    value={customSpeed}
                    onChange={(e) => setCustomSpeed(e.target.value)}
                    placeholder="0.0 - 2.0"
                    min="0"
                    max="2"
                    step="0.1"
                  />
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="space-y-2 pt-4">
                <Button
                  fullWidth
                  variant="outline"
                  onClick={handleCalibrate}
                  disabled={isLoading}
                  icon={<Settings className="w-4 h-4" />}
                >
                  Calibrate Robot
                </Button>
                
                <Button
                  fullWidth
                  variant="outline"
                  onClick={handleResetPosition}
                  disabled={isLoading}
                  icon={<RotateCcw className="w-4 h-4" />}
                >
                  Reset Position
                </Button>
                
                <Button
                  fullWidth
                  variant={robotStatus?.power_state === 'on' ? 'danger' : 'primary'}
                  onClick={handlePowerToggle}
                  disabled={isLoading}
                  icon={<Zap className="w-4 h-4" />}
                >
                  {robotStatus?.power_state === 'on' ? 'Power Off' : 'Power On'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Advanced Controls */}
      {isAdvancedMode && (
        <Card>
          <CardHeader>
            <CardTitle>Advanced Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <ButtonGroup>
                <Button
                  onClick={() => handleMove('stand')}
                  disabled={isLoading}
                  icon={<Play className="w-4 h-4" />}
                >
                  Stand Up
                </Button>
                <Button
                  onClick={() => handleMove('lie')}
                  disabled={isLoading}
                  icon={<Pause className="w-4 h-4" />}
                >
                  Lie Down
                </Button>
              </ButtonGroup>
              
              <ButtonGroup>
                <Button
                  onClick={() => handleMove('jump')}
                  disabled={isLoading}
                >
                  Jump
                </Button>
                <Button
                  onClick={() => handleMove('dance')}
                  disabled={isLoading}
                >
                  Dance
                </Button>
              </ButtonGroup>
              
              <ButtonGroup>
                <Button
                  onClick={() => handleMove('stretch')}
                  disabled={isLoading}
                >
                  Stretch
                </Button>
                <Button
                  onClick={() => handleMove('shake')}
                  disabled={isLoading}
                >
                  Shake
                </Button>
              </ButtonGroup>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}