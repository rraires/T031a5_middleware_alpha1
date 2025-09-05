import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { useThemeStore } from '../stores/themeStore'
import { Theme } from '../types'

interface ThemeContextType {
  theme: Theme
  effectiveTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  setSystemTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const {
    theme,
    effectiveTheme,
    setTheme,
    toggleTheme,
    setSystemTheme
  } = useThemeStore()

  useEffect(() => {
    // Apply theme to document
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(effectiveTheme)
  }, [effectiveTheme])

  const contextValue: ThemeContextType = {
    theme,
    effectiveTheme,
    setTheme,
    toggleTheme,
    setSystemTheme
  }

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useThemeContext = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useThemeContext must be used within a ThemeProvider')
  }
  return context
}