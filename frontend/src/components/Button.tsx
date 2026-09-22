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
 * Standardised button.
 *
 * A thin wrapper over the `.btn-*` utilities in index.css, which DESIGN.md
 * names as the source of truth, so this component can't drift from the
 * buttons everywhere else.
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
  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'px-3 text-sm',
    md: 'px-4 text-base',
    lg: 'px-6 text-lg',
  }

  return (
    <button
      className={`btn-${variant} inline-flex items-center justify-center gap-2 ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <LoadingSpinner size="sm" className="text-current" />
          <span>Saving…</span>
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
