import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, AuthState } from '../types'
import { authService } from '../services/authService'
import toast from 'react-hot-toast'

interface AuthStore extends AuthState {
  // Actions
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  refreshToken: () => Promise<boolean>
  updateUser: (user: Partial<User>) => void
  initializeAuth: () => Promise<void>
  checkPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,

      // Actions
      login: async (username: string, password: string) => {
        try {
          set({ isLoading: true })
          
          const response = await authService.login(username, password)
          
          if (response.success && response.data) {
            const { user, token } = response.data
            
            set({
              user,
              token,
              isAuthenticated: true,
              isLoading: false
            })
            
            // Store token in localStorage for API calls
            localStorage.setItem('auth_token', token)
            
            toast.success(`Welcome back, ${user.username}!`)
            return true
          } else {
            set({ isLoading: false })
            toast.error(response.error?.message || 'Login failed')
            return false
          }
        } catch (error) {
          set({ isLoading: false })
          console.error('Login error:', error)
          toast.error('Login failed. Please try again.')
          return false
        }
      },

      logout: () => {
        try {
          // Call logout API
          authService.logout()
          
          // Clear state
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false
          })
          
          // Clear localStorage
          localStorage.removeItem('auth_token')
          
          toast.success('Logged out successfully')
        } catch (error) {
          console.error('Logout error:', error)
          // Still clear state even if API call fails
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false
          })
          localStorage.removeItem('auth_token')
        }
      },

      refreshToken: async () => {
        try {
          const currentToken = get().token
          if (!currentToken) {
            return false
          }
          
          const response = await authService.refreshToken(currentToken)
          
          if (response.success && response.data) {
            const { user, token } = response.data
            
            set({
              user,
              token,
              isAuthenticated: true
            })
            
            localStorage.setItem('auth_token', token)
            return true
          } else {
            // Token refresh failed, logout user
            get().logout()
            return false
          }
        } catch (error) {
          console.error('Token refresh error:', error)
          get().logout()
          return false
        }
      },

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          })
        }
      },

      initializeAuth: async () => {
        try {
          set({ isLoading: true })
          
          const token = localStorage.getItem('auth_token')
          
          if (!token) {
            set({ isLoading: false })
            return
          }
          
          // Verify token with server
          const response = await authService.verifyToken(token)
          
          if (response.success && response.data) {
            const { user } = response.data
            
            set({
              user,
              token,
              isAuthenticated: true,
              isLoading: false
            })
          } else {
            // Token is invalid, clear it
            localStorage.removeItem('auth_token')
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false
            })
          }
        } catch (error) {
          console.error('Auth initialization error:', error)
          localStorage.removeItem('auth_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false
          })
        }
      },

      checkPermission: (permission: string) => {
        const user = get().user
        if (!user) return false
        
        // Admin has all permissions
        if (user.role === 'admin') return true
        
        // Check if user has specific permission
        return user.permissions.includes(permission as any)
      },

      hasRole: (role: string) => {
        const user = get().user
        if (!user) return false
        
        return user.role === role
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

// Auto refresh token every 15 minutes
setInterval(() => {
  const { isAuthenticated, refreshToken } = useAuthStore.getState()
  if (isAuthenticated) {
    refreshToken()
  }
}, 15 * 60 * 1000)

// Export selectors for better performance
export const selectUser = () => useAuthStore((state) => state.user)
export const selectIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated)
export const selectIsLoading = () => useAuthStore((state) => state.isLoading)
export const selectToken = () => useAuthStore((state) => state.token)