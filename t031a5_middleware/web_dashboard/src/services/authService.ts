import { ApiResponse, User } from '../types'
import { apiClient } from './apiClient'

interface LoginRequest {
  username: string
  password: string
}

interface LoginResponse {
  user: User
  token: string
  expires_in: number
}

interface RefreshTokenResponse {
  user: User
  token: string
  expires_in: number
}

interface VerifyTokenResponse {
  user: User
  valid: boolean
}

class AuthService {
  private readonly baseUrl = '/api/auth'

  /**
   * Login user with username and password
   */
  async login(username: string, password: string): Promise<ApiResponse<LoginResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<LoginResponse>>(
        `${this.baseUrl}/login`,
        { username, password }
      )
      return response.data
    } catch (error: any) {
      console.error('Login error:', error)
      return {
        success: false,
        error: {
          code: 'LOGIN_FAILED',
          message: error.response?.data?.error?.message || 'Login failed'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `${this.baseUrl}/logout`
      )
      return response.data
    } catch (error: any) {
      console.error('Logout error:', error)
      return {
        success: false,
        error: {
          code: 'LOGOUT_FAILED',
          message: error.response?.data?.error?.message || 'Logout failed'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(token: string): Promise<ApiResponse<RefreshTokenResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>(
        `${this.baseUrl}/refresh`,
        { token }
      )
      return response.data
    } catch (error: any) {
      console.error('Token refresh error:', error)
      return {
        success: false,
        error: {
          code: 'TOKEN_REFRESH_FAILED',
          message: error.response?.data?.error?.message || 'Token refresh failed'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Verify if token is still valid
   */
  async verifyToken(token: string): Promise<ApiResponse<VerifyTokenResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<VerifyTokenResponse>>(
        `${this.baseUrl}/verify`,
        { token }
      )
      return response.data
    } catch (error: any) {
      console.error('Token verification error:', error)
      return {
        success: false,
        error: {
          code: 'TOKEN_VERIFICATION_FAILED',
          message: error.response?.data?.error?.message || 'Token verification failed'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.get<ApiResponse<User>>(
        `${this.baseUrl}/me`
      )
      return response.data
    } catch (error: any) {
      console.error('Get current user error:', error)
      return {
        success: false,
        error: {
          code: 'GET_USER_FAILED',
          message: error.response?.data?.error?.message || 'Failed to get user profile'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.put<ApiResponse<User>>(
        `${this.baseUrl}/profile`,
        userData
      )
      return response.data
    } catch (error: any) {
      console.error('Update profile error:', error)
      return {
        success: false,
        error: {
          code: 'UPDATE_PROFILE_FAILED',
          message: error.response?.data?.error?.message || 'Failed to update profile'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Change user password
   */
  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `${this.baseUrl}/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword
        }
      )
      return response.data
    } catch (error: any) {
      console.error('Change password error:', error)
      return {
        success: false,
        error: {
          code: 'CHANGE_PASSWORD_FAILED',
          message: error.response?.data?.error?.message || 'Failed to change password'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<ApiResponse<void>> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `${this.baseUrl}/reset-password`,
        { email }
      )
      return response.data
    } catch (error: any) {
      console.error('Password reset request error:', error)
      return {
        success: false,
        error: {
          code: 'PASSWORD_RESET_FAILED',
          message: error.response?.data?.error?.message || 'Failed to request password reset'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      }
    }
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false
    
    // Admin has all permissions
    if (user.role === 'admin') return true
    
    // Check if user has specific permission
    return user.permissions.includes(permission as any)
  }

  /**
   * Check if user has specific role
   */
  hasRole(user: User | null, role: string): boolean {
    if (!user) return false
    return user.role === role
  }

  /**
   * Get user display name
   */
  getUserDisplayName(user: User | null): string {
    if (!user) return 'Guest'
    return user.username || user.email || 'Unknown User'
  }

  /**
   * Check if user account is active
   */
  isUserActive(user: User | null): boolean {
    if (!user) return false
    return user.is_active
  }

  /**
   * Get user role display name
   */
  getRoleDisplayName(role: string): string {
    const roleNames: Record<string, string> = {
      admin: 'Administrator',
      operator: 'Operator',
      viewer: 'Viewer'
    }
    return roleNames[role] || role
  }

  /**
   * Get permission display name
   */
  getPermissionDisplayName(permission: string): string {
    const permissionNames: Record<string, string> = {
      'system:read': 'System Read',
      'system:write': 'System Write',
      'system:admin': 'System Admin',
      'robot:read': 'Robot Read',
      'robot:control': 'Robot Control',
      'robot:config': 'Robot Config',
      'video:view': 'Video View',
      'video:record': 'Video Record',
      'video:config': 'Video Config',
      'audio:listen': 'Audio Listen',
      'audio:speak': 'Audio Speak',
      'audio:config': 'Audio Config',
      'led:view': 'LED View',
      'led:control': 'LED Control',
      'sensor:read': 'Sensor Read',
      'sensor:config': 'Sensor Config'
    }
    return permissionNames[permission] || permission
  }
}

export const authService = new AuthService()