import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'outlined' | 'elevated'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  actions?: React.ReactNode
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const cardVariants = {
  default: 'bg-white dark:bg-gray-800',
  outlined: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
  elevated: 'bg-white dark:bg-gray-800 shadow-lg'
}

const cardPadding = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6'
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'outlined',
  padding = 'md',
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'rounded-lg',
        cardVariants[variant],
        cardPadding[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  actions,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'flex items-center justify-between',
        actions ? 'mb-4' : 'mb-3',
        className
      )}
      {...props}
    >
      <div className="flex-1">
        {children}
      </div>
      {actions && (
        <div className="flex items-center space-x-2 ml-4">
          {actions}
        </div>
      )}
    </div>
  )
}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={cn('', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'mt-4 pt-4 border-t border-gray-200 dark:border-gray-700',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// Card title component
interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
  level?: 1 | 2 | 3 | 4 | 5 | 6
}

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  level = 3,
  className,
  ...props
}) => {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements
  
  const titleSizes = {
    1: 'text-3xl',
    2: 'text-2xl',
    3: 'text-xl',
    4: 'text-lg',
    5: 'text-base',
    6: 'text-sm'
  }
  
  return (
    <Tag
      className={cn(
        'font-semibold text-gray-900 dark:text-white',
        titleSizes[level],
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  )
}

// Card description component
interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode
}

export const CardDescription: React.FC<CardDescriptionProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <p
      className={cn(
        'text-sm text-gray-600 dark:text-gray-400 mt-1',
        className
      )}
      {...props}
    >
      {children}
    </p>
  )
}

// Stat card component for metrics
interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon?: React.ReactNode
  trend?: {
    value: number
    label: string
    direction: 'up' | 'down' | 'neutral'
  }
  className?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  description,
  icon,
  trend,
  className
}) => {
  const getTrendColor = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return 'text-green-600 dark:text-green-400'
      case 'down':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }
  
  const getTrendIcon = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return '↗'
      case 'down':
        return '↘'
      default:
        return '→'
    }
  }
  
  return (
    <Card className={cn('', className)}>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {value}
            </p>
            {description && (
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {description}
              </p>
            )}
            {trend && (
              <div className={cn('flex items-center mt-2 text-xs', getTrendColor(trend.direction))}>
                <span className="mr-1">{getTrendIcon(trend.direction)}</span>
                <span className="font-medium">{trend.value}%</span>
                <span className="ml-1">{trend.label}</span>
              </div>
            )}
          </div>
          {icon && (
            <div className="flex-shrink-0 ml-4">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                {icon}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}