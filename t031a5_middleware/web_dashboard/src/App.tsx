import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { Layout, ProtectedRoute } from './components'
import { Dashboard, Control, Video, Sensors, Settings } from './pages'
import { AuthProvider, ThemeProvider, WebSocketProvider, RobotProvider } from './hooks'
import './index.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <WebSocketProvider>
            <RobotProvider>
            <Router>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
                <Routes>
                  {/* Protected Routes */}
                  <Route path="/" element={<Layout />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    
                    <Route
                      path="/dashboard"
                      element={
                        <ProtectedRoute requiredPermissions={['dashboard.view']}>
                          <Dashboard />
                        </ProtectedRoute>
                      }
                    />
                    
                    <Route
                      path="/control"
                      element={
                        <ProtectedRoute requiredPermissions={['robot.control']}>
                          <Control />
                        </ProtectedRoute>
                      }
                    />
                    
                    <Route
                      path="/video"
                      element={
                        <ProtectedRoute requiredPermissions={['video.view']}>
                          <Video />
                        </ProtectedRoute>
                      }
                    />
                    
                    <Route
                      path="/sensors"
                      element={
                        <ProtectedRoute requiredPermissions={['sensors.view']}>
                          <Sensors />
                        </ProtectedRoute>
                      }
                    />
                    
                    <Route
                      path="/settings"
                      element={
                        <ProtectedRoute requiredPermissions={['settings.view']}>
                          <Settings />
                        </ProtectedRoute>
                      }
                    />
                    
                    {/* Catch all route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Route>
                </Routes>
                
                {/* Toast Notifications */}
                <Toaster
                  position="top-right"
                  expand={true}
                  richColors
                  closeButton
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: 'var(--background)',
                      color: 'var(--foreground)',
                      border: '1px solid var(--border)'
                    }
                  }}
                />
              </div>
            </Router>
            </RobotProvider>
          </WebSocketProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App