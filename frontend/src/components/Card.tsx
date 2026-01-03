import { ReactNode, HTMLAttributes } from 'react'

type CardElevation = 0 | 1 | 2 | 3 | 4
type CardVariant = 'default' | 'outlined' | 'filled' | 'glass'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  elevation?: CardElevation
  variant?: CardVariant
  interactive?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

/**
 * Standardized Card component
 * Provides consistent styling for all card elements across the app
 */
export default function Card({
  children,
  elevation = 1,
  variant = 'default',
  interactive = false,
  padding = 'md',
  className = '',
  ...props
}: CardProps) {
  const baseStyles = 'rounded-xl transition-all duration-200'

  const elevationStyles: Record<CardElevation, string> = {
    0: 'shadow-none',
    1: 'shadow-soft', // Subtle shadow for slight elevation
    2: 'shadow-medium', // Standard card elevation
    3: 'shadow-strong', // Prominent elevation
    4: 'shadow-strong hover:shadow-[0_12px_32px_rgba(44,36,32,0.15)]', // Maximum elevation
  }

  const variantStyles: Record<CardVariant, string> = {
    default: 'bg-off-white dark:bg-neutral-800 border border-neutral-border/50 dark:border-neutral-700',
    outlined: 'bg-transparent border-2 border-neutral-border dark:border-neutral-700',
    filled: 'bg-cream dark:bg-neutral-700 border-0',
    glass: 'surface-glass backdrop-blur-md',
  }

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-3',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  }

  const interactiveStyles = interactive
    ? 'cursor-pointer hover:shadow-medium hover:-translate-y-0.5 active:translate-y-0 active:shadow-soft'
    : ''

  return (
    <div
      className={`
        ${baseStyles}
        ${elevationStyles[elevation]}
        ${variantStyles[variant]}
        ${paddingStyles[padding]}
        ${interactiveStyles}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
      {...props}
    >
      {children}
    </div>
  )
}

/**
 * Card Header - Consistent header styling
 */
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  divider?: boolean
}

export function CardHeader({ children, divider = true, className = '', ...props }: CardHeaderProps) {
  return (
    <div
      className={`${divider ? 'pb-4 border-b border-neutral-border dark:border-neutral-700' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

/**
 * Card Body - Main content area
 */
interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export function CardBody({ children, className = '', ...props }: CardBodyProps) {
  return (
    <div className={`py-4 ${className}`} {...props}>
      {children}
    </div>
  )
}

/**
 * Card Footer - Footer with consistent styling
 */
interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  divider?: boolean
}

export function CardFooter({ children, divider = true, className = '', ...props }: CardFooterProps) {
  return (
    <div
      className={`${divider ? 'pt-4 border-t border-neutral-border dark:border-neutral-700' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
