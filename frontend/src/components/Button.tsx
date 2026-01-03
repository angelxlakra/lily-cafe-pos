import { ButtonHTMLAttributes, ReactNode } from 'react'
import LoadingSpinner from './LoadingSpinner'

type ButtonVariant = 'primary' | 'secondary' | 'destructive' | 'ghost' | 'success'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  children: ReactNode
  leftIcon?: ReactNode
  rightIcon?: ReactNode
}

/**
 * Standardized Button component
 * Provides consistent styling across the application
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'

  const variantStyles: Record<ButtonVariant, string> = {
    primary: 'bg-gradient-to-r from-coffee-brown to-coffee-dark text-cream hover:from-coffee-dark hover:to-coffee-brown shadow-md hover:shadow-lg focus:ring-coffee-brown',
    secondary: 'bg-transparent border-2 border-neutral-border text-neutral-text-dark hover:bg-neutral-50 dark:hover:bg-neutral-800 focus:ring-neutral-border',
    destructive: 'bg-error text-white hover:bg-error/90 shadow-md hover:shadow-lg focus:ring-error',
    ghost: 'bg-transparent text-neutral-text-dark hover:bg-neutral-50 dark:hover:bg-neutral-800 focus:ring-neutral-border',
    success: 'bg-success text-white hover:bg-success/90 shadow-md hover:shadow-lg focus:ring-success',
  }

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <LoadingSpinner size="sm" className="text-current" />
          <span>Processing...</span>
        </>
      ) : (
        <>
          {leftIcon && <span aria-hidden="true">{leftIcon}</span>}
          {children}
          {rightIcon && <span aria-hidden="true">{rightIcon}</span>}
        </>
      )}
    </button>
  )
}
