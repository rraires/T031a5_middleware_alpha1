import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  systemTheme: 'light' | 'dark'
  effectiveTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  setSystemTheme: (theme: 'light' | 'dark') => void
}

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const getEffectiveTheme = (theme: Theme, systemTheme: 'light' | 'dark'): 'light' | 'dark' => {
  return theme === 'system' ? systemTheme : theme
}

const applyTheme = (theme: 'light' | 'dark') => {
  if (typeof document === 'undefined') return
  
  const root = document.documentElement
  if (theme === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => {
      const systemTheme = getSystemTheme()
      const initialTheme: Theme = 'system'
      const effectiveTheme = getEffectiveTheme(initialTheme, systemTheme)
      
      // Apply initial theme
      applyTheme(effectiveTheme)
      
      // Listen for system theme changes
      if (typeof window !== 'undefined') {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handleChange = (e: MediaQueryListEvent) => {
          const newSystemTheme = e.matches ? 'dark' : 'light'
          const state = get()
          const newEffectiveTheme = getEffectiveTheme(state.theme, newSystemTheme)
          
          set({ 
            systemTheme: newSystemTheme, 
            effectiveTheme: newEffectiveTheme 
          })
          
          applyTheme(newEffectiveTheme)
        }
        
        mediaQuery.addEventListener('change', handleChange)
      }
      
      return {
        theme: initialTheme,
        systemTheme,
        effectiveTheme,
        
        setTheme: (theme: Theme) => {
          const state = get()
          const newEffectiveTheme = getEffectiveTheme(theme, state.systemTheme)
          
          set({ 
            theme, 
            effectiveTheme: newEffectiveTheme 
          })
          
          applyTheme(newEffectiveTheme)
        },
        
        toggleTheme: () => {
          const state = get()
          const newTheme = state.effectiveTheme === 'dark' ? 'light' : 'dark'
          
          set({ 
            theme: newTheme, 
            effectiveTheme: newTheme 
          })
          
          applyTheme(newTheme)
        },
        
        setSystemTheme: (systemTheme: 'light' | 'dark') => {
          const state = get()
          const newEffectiveTheme = getEffectiveTheme(state.theme, systemTheme)
          
          set({ 
            systemTheme, 
            effectiveTheme: newEffectiveTheme 
          })
          
          if (state.theme === 'system') {
            applyTheme(newEffectiveTheme)
          }
        }
      }
    },
    {
      name: 'theme-storage',
      partialize: (state) => ({ theme: state.theme })
    }
  )
)

// Selectors for better performance
export const useTheme = () => useThemeStore((state) => state.theme)
export const useEffectiveTheme = () => useThemeStore((state) => state.effectiveTheme)
export const useToggleTheme = () => useThemeStore((state) => state.toggleTheme)