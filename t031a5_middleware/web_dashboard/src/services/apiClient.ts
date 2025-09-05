import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ApiResponse, ApiError } from '../types'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add request timestamp
    config.metadata = {
      startTime: Date.now()
    }
    
    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response time
    const endTime = Date.now()
    const startTime = response.config.metadata?.startTime || endTime
    const duration = endTime - startTime
    
    if (duration > 5000) {
      console.warn(`Slow API response: ${response.config.url} took ${duration}ms`)
    }
    
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any
    
    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const { refreshToken } = useAuthStore.getState()
        const currentToken = useAuthStore.getState().token
        
        if (currentToken) {
          await refreshToken()
          
          // Retry original request with new token
          const newToken = useAuthStore.getState().token
          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return apiClient(originalRequest)
          }
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)
        useAuthStore.getState().logout()
        toast.error('Session expired. Please login again.')
        return Promise.reject(refreshError)
      }
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message)
      toast.error('Network error. Please check your connection.')
      return Promise.reject({
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: 'Network connection failed'
        },
        timestamp: new Date().toISOString(),
        request_id: ''
      } as ApiResponse<never>)
    }
    
    // Handle server errors
    const status = error.response.status
    const errorData = error.response.data as ApiError
    
    // Log error details
    console.error('API Error:', {
      status,
      url: error.config?.url,
      method: error.config?.method,
      error: errorData
    })
    
    // Show user-friendly error messages
    switch (status) {
      case 400:
        toast.error(errorData?.message || 'Invalid request')
        break
      case 403:
        toast.error('Access denied. Insufficient permissions.')
        break
      case 404:
        toast.error('Resource not found')
        break
      case 429:
        toast.error('Too many requests. Please try again later.')
        break
      case 500:
        toast.error('Server error. Please try again later.')
        break
      case 503:
        toast.error('Service unavailable. Please try again later.')
        break
      default:
        toast.error(errorData?.message || 'An unexpected error occurred')
    }
    
    return Promise.reject(error)
  }
)

// Retry mechanism for failed requests
const retryRequest = async (
  requestFn: () => Promise<any>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<any> => {
  try {
    return await requestFn()
  } catch (error: any) {
    if (retries > 0 && shouldRetry(error)) {
      console.log(`Retrying request in ${delay}ms... (${retries} retries left)`)
      await new Promise(resolve => setTimeout(resolve, delay))
      return retryRequest(requestFn, retries - 1, delay * 2) // Exponential backoff
    }
    throw error
  }
}

// Determine if request should be retried
const shouldRetry = (error: any): boolean => {
  // Retry on network errors or 5xx server errors
  if (!error.response) return true
  const status = error.response.status
  return status >= 500 && status < 600
}

// API client wrapper with retry logic
class ApiClient {
  private client: AxiosInstance
  
  constructor(client: AxiosInstance) {
    this.client = client
  }
  
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return retryRequest(() => this.client.get<T>(url, config))
  }
  
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return retryRequest(() => this.client.post<T>(url, data, config))
  }
  
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return retryRequest(() => this.client.put<T>(url, data, config))
  }
  
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return retryRequest(() => this.client.patch<T>(url, data, config))
  }
  
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return retryRequest(() => this.client.delete<T>(url, config))
  }
  
  // Upload file with progress tracking
  async uploadFile<T = any>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.client.post<T>(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }
  
  // Download file with progress tracking
  async downloadFile(
    url: string,
    filename?: string,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<void> {
    const response = await this.client.get(url, {
      ...config,
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
    
    // Create download link
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
  
  // Get request with caching
  async getCached<T = any>(
    url: string,
    cacheKey: string,
    ttl: number = 300000, // 5 minutes
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    const cacheData = localStorage.getItem(`api_cache_${cacheKey}`)
    
    if (cacheData) {
      const { data, timestamp } = JSON.parse(cacheData)
      if (Date.now() - timestamp < ttl) {
        return { data } as AxiosResponse<T>
      }
    }
    
    const response = await this.get<T>(url, config)
    
    // Cache the response
    localStorage.setItem(`api_cache_${cacheKey}`, JSON.stringify({
      data: response.data,
      timestamp: Date.now()
    }))
    
    return response
  }
  
  // Clear cache
  clearCache(cacheKey?: string): void {
    if (cacheKey) {
      localStorage.removeItem(`api_cache_${cacheKey}`)
    } else {
      // Clear all API cache
      Object.keys(localStorage)
        .filter(key => key.startsWith('api_cache_'))
        .forEach(key => localStorage.removeItem(key))
    }
  }
  
  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health')
      return true
    } catch (error) {
      console.error('Health check failed:', error)
      return false
    }
  }
  
  // Get API version
  async getVersion(): Promise<string> {
    try {
      const response = await this.get<{ version: string }>('/version')
      return response.data.version
    } catch (error) {
      console.error('Failed to get API version:', error)
      return 'unknown'
    }
  }
}

// Export the configured API client
const configuredApiClient = new ApiClient(apiClient)
export { configuredApiClient as apiClient, API_BASE_URL, API_TIMEOUT }

// Type augmentation for axios config
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime: number
    }
  }
}