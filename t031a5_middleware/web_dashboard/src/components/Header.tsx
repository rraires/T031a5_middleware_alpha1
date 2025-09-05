import React from 'react'
import { Bell, Settings, User, LogOut, Menu, Wifi, WifiOff } from 'lucide-react'
import { useAuth, useWebSocket } from '../hooks'
import { useThemeStore } from '../stores'
import { formatDateTime, CONNECTION_STATUS } from '../utils'
import { toast } from 'sonner'

interface HeaderProps {
  onMenuToggle?: () => void
  showMenuButton?: boolean
}

export const Header: React.FC<HeaderProps> = ({ 
  onMenuToggle, 
  showMenuButton = false 
}) => {
  const { user, logout } = useAuth()
  const { connectionStatus, lastConnected } = useWebSocket()
  const { theme, toggleTheme } = useThemeStore()
  
  const [showUserMenu, setShowUserMenu] = React.useState(false)
  const [showNotifications, setShowNotifications] = React.useState(false)
  
  const userMenuRef = React.useRef<HTMLDivElement>(null)
  const notificationRef = React.useRef<HTMLDivElement>(null)
  
  // Close menus when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  const handleLogout = async () => {
    try {
      await logout()
      toast.success('Logged out successfully')
    } catch (error) {
      toast.error('Failed to logout')
    }
    setShowUserMenu(false)
  }
  
  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case CONNECTION_STATUS.CONNECTED:
        return <Wifi className="w-5 h-5 text-green-500" />
      case CONNECTION_STATUS.CONNECTING:
        return <Wifi className="w-5 h-5 text-yellow-500 animate-pulse" />
      default:
        return <WifiOff className="w-5 h-5 text-red-500" />
    }
  }
  
  const getConnectionText = () => {
    switch (connectionStatus) {
      case CONNECTION_STATUS.CONNECTED:
        return 'Connected'
      case CONNECTION_STATUS.CONNECTING:
        return 'Connecting...'
      case CONNECTION_STATUS.DISCONNECTED:
        return lastConnected ? `Disconnected (${formatDateTime(lastConnected)})` : 'Disconnected'
      default:
        return 'Connection Error'
    }
  }
  
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left section */}
        <div className="flex items-center space-x-4">
          {showMenuButton && (
            <button
              onClick={onMenuToggle}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Unitree Robot Dashboard
            </h1>
          </div>
        </div>
        
        {/* Center section - Connection status */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700">
          {getConnectionIcon()}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {getConnectionText()}
          </span>
        </div>
        
        {/* Right section */}
        <div className="flex items-center space-x-2">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <span className="w-5 h-5 text-yellow-500">☀️</span>
            ) : (
              <span className="w-5 h-5 text-gray-600">🌙</span>
            )}
          </button>
          
          {/* Notifications */}
          <div className="relative" ref={notificationRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {/* Notification badge */}
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
            </button>
            
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Notifications
                  </h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                    No new notifications
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Settings */}
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
          
          {/* User menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden md:block">
                {user?.name || user?.email || 'User'}
              </span>
            </button>
            
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.email}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                    {user?.role}
                  </p>
                </div>
                <div className="py-2">
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <User className="w-4 h-4" />
                    <span>Profile</span>
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </button>
                  <hr className="my-2 border-gray-200 dark:border-gray-700" />
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                    onClick={handleLogout}
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}