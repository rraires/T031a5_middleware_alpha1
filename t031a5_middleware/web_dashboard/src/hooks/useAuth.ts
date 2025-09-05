import { useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../stores/authStore'
import { authService } from '../services/authService'
import { User } from '../types'
import toast from 'react-hot-toast'

/**
 * Hook for authentication operations
 */
export const useAuth = () => {
  const queryClient = useQueryClient()
  const {
    user,
    token,
    isAuthenticated,
    isLoading,
    login: loginStore,
    logout: logoutStore,
    updateUser,
    initializeAuth
  } = useAuthStore()

  // Initialize authentication on mount
  useEffect(() => {
    initializeAuth()
  }, [])

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async ({ username, password }: { username: string; password: string }) => {
      const response = await authService.login(username, password)
      if (!response.success) {
        throw new Error(response.error?.message || 'Login failed')
      }
      return response.data!
    },
    onSuccess: (data) => {
      loginStore(data.user, data.token)
      toast.success('Login successful!')
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      const response = await authService.logout()
      if (!response.success) {
        console.warn('Logout API call failed, but proceeding with local logout')
      }
    },
    onSuccess: () => {
      logoutStore()
      queryClient.clear()
      toast.success('Logged out successfully')
    },
    onError: (error: Error) => {
      // Even if API call fails, logout locally
      logoutStore()
      queryClient.clear()
      console.error('Logout error:', error)
    }
  })

  // Get current user query
  const userQuery = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await authService.getCurrentUser()
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to get user')
      }
      return response.data!
    },
    enabled: isAuthenticated && !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 401 errors
      if (error?.response?.status === 401) {
        return false
      }
      return failureCount < 3
    }
  })

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (userData: Partial<User>) => {
      const response = await authService.updateProfile(userData)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to update profile')
      }
      return response.data!
    },
    onSuccess: (updatedUser) => {
      updateUser(updatedUser)
      queryClient.setQueryData(['user'], updatedUser)
      toast.success('Profile updated successfully!')
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: async ({ currentPassword, newPassword }: {
      currentPassword: string
      newPassword: string
    }) => {
      const response = await authService.changePassword(currentPassword, newPassword)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to change password')
      }
    },
    onSuccess: () => {
      toast.success('Password changed successfully!')
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Request password reset mutation
  const requestPasswordResetMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await authService.requestPasswordReset(email)
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to request password reset')
      }
    },
    onSuccess: () => {
      toast.success('Password reset email sent!')
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // Helper functions
  const login = useCallback((username: string, password: string) => {
    loginMutation.mutate({ username, password })
  }, [loginMutation])

  const logout = useCallback(() => {
    logoutMutation.mutate()
  }, [logoutMutation])

  const updateProfile = useCallback((userData: Partial<User>) => {
    updateProfileMutation.mutate(userData)
  }, [updateProfileMutation])

  const changePassword = useCallback((currentPassword: string, newPassword: string) => {
    changePasswordMutation.mutate({ currentPassword, newPassword })
  }, [changePasswordMutation])

  const requestPasswordReset = useCallback((email: string) => {
    requestPasswordResetMutation.mutate(email)
  }, [requestPasswordResetMutation])

  // Permission and role helpers
  const hasPermission = useCallback((permission: string) => {
    return authService.hasPermission(user, permission)
  }, [user])

  const hasRole = useCallback((role: string) => {
    return authService.hasRole(user, role)
  }, [user])

  const isAdmin = useCallback(() => {
    return hasRole('admin')
  }, [hasRole])

  const isOperator = useCallback(() => {
    return hasRole('operator')
  }, [hasRole])

  const isViewer = useCallback(() => {
    return hasRole('viewer')
  }, [hasRole])

  const canControlRobot = useCallback(() => {
    return hasPermission('robot:control')
  }, [hasPermission])

  const canViewVideo = useCallback(() => {
    return hasPermission('video:view')
  }, [hasPermission])

  const canRecordVideo = useCallback(() => {
    return hasPermission('video:record')
  }, [hasPermission])

  const canConfigureSystem = useCallback(() => {
    return hasPermission('system:admin')
  }, [hasPermission])

  const getUserDisplayName = useCallback(() => {
    return authService.getUserDisplayName(user)
  }, [user])

  const isUserActive = useCallback(() => {
    return authService.isUserActive(user)
  }, [user])

  return {
    // State
    user: userQuery.data || user,
    token,
    isAuthenticated,
    isLoading: isLoading || loginMutation.isPending || userQuery.isLoading,
    
    // Actions
    login,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    
    // Mutation states
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    isUpdatingProfile: updateProfileMutation.isPending,
    isChangingPassword: changePasswordMutation.isPending,
    isRequestingPasswordReset: requestPasswordResetMutation.isPending,
    
    // Permission helpers
    hasPermission,
    hasRole,
    isAdmin,
    isOperator,
    isViewer,
    canControlRobot,
    canViewVideo,
    canRecordVideo,
    canConfigureSystem,
    
    // Utility helpers
    getUserDisplayName,
    isUserActive,
    
    // Query states
    userError: userQuery.error,
    isUserLoading: userQuery.isLoading,
    refetchUser: userQuery.refetch
  }
}

/**
 * Hook for checking if user has specific permission
 */
export const usePermission = (permission: string) => {
  const { hasPermission } = useAuth()
  return hasPermission(permission)
}

/**
 * Hook for checking if user has specific role
 */
export const useRole = (role: string) => {
  const { hasRole } = useAuth()
  return hasRole(role)
}

/**
 * Hook for admin-only operations
 */
export const useAdminOnly = () => {
  const { isAdmin } = useAuth()
  
  if (!isAdmin()) {
    throw new Error('Admin access required')
  }
  
  return true
}

/**
 * Hook for operator access
 */
export const useOperatorAccess = () => {
  const { isAdmin, isOperator } = useAuth()
  
  if (!isAdmin() && !isOperator()) {
    throw new Error('Operator access required')
  }
  
  return true
}