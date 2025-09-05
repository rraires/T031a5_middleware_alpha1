import React from 'react'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'default' | 'filled' | 'outlined'
  inputSize?: 'sm' | 'md' | 'lg'
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  variant?: 'default' | 'filled' | 'outlined'
  inputSize?: 'sm' | 'md' | 'lg'
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
}

const inputVariants = {
  default: 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
  filled: 'border-transparent bg-gray-100 dark:bg-gray-700',
  outlined: 'border-2 border-gray-300 dark:border-gray-600 bg-transparent'
}

const inputSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-3 text-base'
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'default',
  inputSize = 'md',
  className,
  type = 'text',
  id,
  ...props
}) => {
  const [showPassword, setShowPassword] = React.useState(false)
  const inputId = id || React.useId()
  const isPassword = type === 'password'
  const inputType = isPassword && showPassword ? 'text' : type
  
  const hasError = Boolean(error)
  
  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <div className="text-gray-400 dark:text-gray-500">
              {leftIcon}
            </div>
          </div>
        )}
        
        <input
          id={inputId}
          type={inputType}
          className={cn(
            'block w-full rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            inputVariants[variant],
            inputSizes[inputSize],
            leftIcon && 'pl-10',
            (rightIcon || isPassword) && 'pr-10',
            hasError && 'border-red-500 dark:border-red-400 focus:ring-red-500',
            props.disabled && 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-900',
            className
          )}
          {...props}
        />
        
        {(rightIcon || isPassword) && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {isPassword ? (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            ) : (
              <div className="text-gray-400 dark:text-gray-500">
                {rightIcon}
              </div>
            )}
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <div className="mt-1 flex items-center">
          {error && (
            <>
              <AlertCircle className="w-4 h-4 text-red-500 mr-1 flex-shrink-0" />
              <p className="text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            </>
          )}
          {!error && helperText && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {helperText}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  helperText,
  variant = 'default',
  inputSize = 'md',
  resize = 'vertical',
  className,
  id,
  rows = 3,
  ...props
}) => {
  const textareaId = id || React.useId()
  const hasError = Boolean(error)
  
  const resizeClasses = {
    none: 'resize-none',
    vertical: 'resize-y',
    horizontal: 'resize-x',
    both: 'resize'
  }
  
  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          {label}
        </label>
      )}
      
      <textarea
        id={textareaId}
        rows={rows}
        className={cn(
          'block w-full rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          inputVariants[variant],
          inputSizes[inputSize],
          resizeClasses[resize],
          hasError && 'border-red-500 dark:border-red-400 focus:ring-red-500',
          props.disabled && 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-900',
          className
        )}
        {...props}
      />
      
      {(error || helperText) && (
        <div className="mt-1 flex items-center">
          {error && (
            <>
              <AlertCircle className="w-4 h-4 text-red-500 mr-1 flex-shrink-0" />
              <p className="text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            </>
          )}
          {!error && helperText && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {helperText}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// Select component
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  helperText?: string
  variant?: 'default' | 'filled' | 'outlined'
  inputSize?: 'sm' | 'md' | 'lg'
  placeholder?: string
  options: Array<{ value: string; label: string; disabled?: boolean }>
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  variant = 'default',
  inputSize = 'md',
  placeholder,
  options,
  className,
  id,
  ...props
}) => {
  const selectId = id || React.useId()
  const hasError = Boolean(error)
  
  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          {label}
        </label>
      )}
      
      <select
        id={selectId}
        className={cn(
          'block w-full rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-no-repeat bg-right bg-[length:16px_16px] pr-8',
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDYiIHN0cm9rZT0iIzZCNzI4MCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+')]",
          inputVariants[variant],
          inputSizes[inputSize],
          hasError && 'border-red-500 dark:border-red-400 focus:ring-red-500',
          props.disabled && 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-900',
          className
        )}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
      
      {(error || helperText) && (
        <div className="mt-1 flex items-center">
          {error && (
            <>
              <AlertCircle className="w-4 h-4 text-red-500 mr-1 flex-shrink-0" />
              <p className="text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            </>
          )}
          {!error && helperText && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {helperText}
            </p>
          )}
        </div>
      )}
    </div>
  )
}