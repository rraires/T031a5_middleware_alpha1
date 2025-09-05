import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { cn } from '../lib/utils'

interface LayoutProps {
  children?: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
  const [sidebarVisible, setSidebarVisible] = React.useState(true)
  
  // Handle responsive sidebar
  React.useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768
      if (isMobile) {
        setSidebarCollapsed(false)
        setSidebarVisible(false)
      } else {
        setSidebarVisible(true)
      }
    }
    
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  const toggleSidebar = () => {
    const isMobile = window.innerWidth < 768
    if (isMobile) {
      setSidebarVisible(!sidebarVisible)
    } else {
      setSidebarCollapsed(!sidebarCollapsed)
    }
  }
  
  const closeMobileSidebar = () => {
    const isMobile = window.innerWidth < 768
    if (isMobile && sidebarVisible) {
      setSidebarVisible(false)
    }
  }
  
  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Mobile overlay */}
      {sidebarVisible && window.innerWidth < 768 && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeMobileSidebar}
        />
      )}
      
      {/* Sidebar */}
      <div
        className={cn(
          'fixed md:relative z-50 h-full transition-transform duration-300',
          sidebarVisible ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
          window.innerWidth < 768 && !sidebarVisible && 'hidden'
        )}
      >
        <Sidebar
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="h-full"
        />
      </div>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          onMenuToggle={toggleSidebar}
          showMenuButton={true}
        />
        
        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto px-4 py-6">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  )
}

// Loading component for lazy-loaded routes
export const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
  </div>
)

// Error boundary component
interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props)
    this.state = { hasError: false }
  }
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo)
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="text-center">
              <div className="text-red-500 text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                An unexpected error occurred. Please refresh the page or contact support.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Refresh Page
              </button>
            </div>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 text-sm">
                <summary className="cursor-pointer text-gray-600 dark:text-gray-400">
                  Error Details
                </summary>
                <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-auto">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }
    
    return this.props.children
  }
}

// Protected route wrapper
interface ProtectedRouteProps {
  children: React.ReactNode
  permission?: string
  role?: string
  fallback?: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  permission,
  role,
  fallback
}) => {
  // This would typically use your auth hook
  // For now, we'll assume access is granted
  const hasAccess = true // Replace with actual permission/role check
  
  if (!hasAccess) {
    return (
      fallback || (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-red-500 text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              You don't have permission to access this page.
            </p>
          </div>
        </div>
      )
    )
  }
  
  return <>{children}</>
}