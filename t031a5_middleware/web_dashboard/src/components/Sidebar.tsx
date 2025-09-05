import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Home,
  Bot,
  Video,
  Volume2,
  Lightbulb,
  BarChart3,
  Settings,
  Users,
  FileText,
  Activity,
  Camera,
  Mic,
  Palette,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { useAuth } from '../hooks'
import { USER_ROLES, PERMISSIONS } from '../utils'
import { cn } from '../lib/utils'

interface SidebarProps {
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  className?: string
}

interface NavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  path: string
  permission?: string
  role?: string
  children?: NavItem[]
}

const navigationItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: Home,
    path: '/'
  },
  {
    id: 'robot',
    label: 'Robot Control',
    icon: Bot,
    path: '/robot',
    permission: PERMISSIONS.ROBOT_VIEW,
    children: [
      {
        id: 'robot-status',
        label: 'Status',
        icon: Activity,
        path: '/robot/status',
        permission: PERMISSIONS.ROBOT_VIEW
      },
      {
        id: 'robot-control',
        label: 'Control',
        icon: Bot,
        path: '/robot/control',
        permission: PERMISSIONS.ROBOT_CONTROL
      }
    ]
  },
  {
    id: 'video',
    label: 'Video',
    icon: Video,
    path: '/video',
    permission: PERMISSIONS.VIDEO_STREAM,
    children: [
      {
        id: 'video-live',
        label: 'Live Stream',
        icon: Camera,
        path: '/video/live',
        permission: PERMISSIONS.VIDEO_STREAM
      },
      {
        id: 'video-recordings',
        label: 'Recordings',
        icon: Video,
        path: '/video/recordings',
        permission: PERMISSIONS.VIDEO_RECORD
      }
    ]
  },
  {
    id: 'audio',
    label: 'Audio',
    icon: Volume2,
    path: '/audio',
    permission: PERMISSIONS.AUDIO_CONTROL,
    children: [
      {
        id: 'audio-control',
        label: 'Control',
        icon: Mic,
        path: '/audio/control',
        permission: PERMISSIONS.AUDIO_CONTROL
      },
      {
        id: 'audio-settings',
        label: 'Settings',
        icon: Settings,
        path: '/audio/settings',
        permission: PERMISSIONS.AUDIO_CONFIGURE
      }
    ]
  },
  {
    id: 'led',
    label: 'LED Control',
    icon: Lightbulb,
    path: '/led',
    permission: PERMISSIONS.LED_CONTROL,
    children: [
      {
        id: 'led-control',
        label: 'Control',
        icon: Palette,
        path: '/led/control',
        permission: PERMISSIONS.LED_CONTROL
      },
      {
        id: 'led-patterns',
        label: 'Patterns',
        icon: Lightbulb,
        path: '/led/patterns',
        permission: PERMISSIONS.LED_CONFIGURE
      }
    ]
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: BarChart3,
    path: '/analytics',
    permission: PERMISSIONS.SYSTEM_VIEW
  },
  {
    id: 'logs',
    label: 'Logs',
    icon: FileText,
    path: '/logs',
    permission: PERMISSIONS.SYSTEM_LOGS
  },
  {
    id: 'users',
    label: 'Users',
    icon: Users,
    path: '/users',
    permission: PERMISSIONS.USER_MANAGE,
    role: USER_ROLES.ADMIN
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    path: '/settings',
    permission: PERMISSIONS.SYSTEM_CONFIGURE
  }
]

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed = false,
  onToggleCollapse,
  className
}) => {
  const { hasPermission, hasRole } = useAuth()
  const [expandedItems, setExpandedItems] = React.useState<Set<string>>(new Set())
  
  const toggleExpanded = (itemId: string) => {
    if (isCollapsed) return
    
    setExpandedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }
  
  const isItemVisible = (item: NavItem): boolean => {
    // Check role requirement
    if (item.role && !hasRole(item.role)) {
      return false
    }
    
    // Check permission requirement
    if (item.permission && !hasPermission(item.permission)) {
      return false
    }
    
    return true
  }
  
  const renderNavItem = (item: NavItem, level = 0) => {
    if (!isItemVisible(item)) {
      return null
    }
    
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.has(item.id)
    const Icon = item.icon
    
    return (
      <div key={item.id}>
        {hasChildren ? (
          <button
            onClick={() => toggleExpanded(item.id)}
            className={cn(
              'w-full flex items-center px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors',
              'hover:bg-gray-100 dark:hover:bg-gray-700',
              'text-gray-700 dark:text-gray-300',
              level > 0 && 'ml-4'
            )}
          >
            <Icon className={cn('flex-shrink-0', isCollapsed ? 'w-5 h-5' : 'w-4 h-4 mr-3')} />
            {!isCollapsed && (
              <>
                <span className="flex-1">{item.label}</span>
                {isExpanded ? (
                  <ChevronLeft className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </>
            )}
          </button>
        ) : (
          <NavLink
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                isActive
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                  : 'text-gray-700 dark:text-gray-300',
                level > 0 && 'ml-4'
              )
            }
          >
            <Icon className={cn('flex-shrink-0', isCollapsed ? 'w-5 h-5' : 'w-4 h-4 mr-3')} />
            {!isCollapsed && <span>{item.label}</span>}
          </NavLink>
        )}
        
        {/* Render children */}
        {hasChildren && isExpanded && !isCollapsed && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }
  
  return (
    <aside
      className={cn(
        'bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        {!isCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              Unitree
            </span>
          </div>
        )}
        
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
      
      {/* Navigation */}
      <nav className="p-4 space-y-2 overflow-y-auto flex-1">
        {navigationItems.map(item => renderNavItem(item))}
      </nav>
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {!isCollapsed && (
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Unitree Robot Dashboard
            <br />
            v1.0.0
          </div>
        )}
      </div>
    </aside>
  )
}