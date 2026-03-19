import { useEffect, useRef } from 'react'
import { Warning, Info } from '@phosphor-icons/react'

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'info'
  isLoading?: boolean
}

const VARIANT_CONFIG = {
  danger: {
    gradient: 'linear-gradient(135deg, #c04e30, #b5462a)',
    icon: Warning,
    confirmClass: 'bg-error hover:bg-error/90 text-white',
  },
  warning: {
    gradient: 'linear-gradient(135deg, #C27A2A, #a06020)',
    icon: Warning,
    confirmClass: 'bg-warning hover:bg-warning/90 text-white',
  },
  info: {
    gradient: 'linear-gradient(135deg, #2196F3, #1565C0)',
    icon: Info,
    confirmClass: 'bg-info hover:bg-info/90 text-white',
  },
}

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'warning',
  isLoading = false,
}: ConfirmDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, isLoading, onClose])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => { document.body.style.overflow = 'unset' }
  }, [isOpen])

  if (!isOpen) return null

  const { gradient, icon: Icon, confirmClass } = VARIANT_CONFIG[variant]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget && !isLoading) onClose() }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div className="bg-off-white border border-neutral-border rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div style={{ background: gradient }} className="flex items-center gap-3 px-5 py-4">
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <Icon size={20} weight="duotone" color="white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2
              id="dialog-title"
              className="text-white font-heading italic text-base font-bold leading-tight"
            >
              {title}
            </h2>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close"
            className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0 disabled:opacity-50"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <p
          id="dialog-description"
          className="px-5 py-4 text-neutral-text-body text-sm leading-relaxed"
        >
          {message}
        </p>

        {/* Footer */}
        <div className="px-5 pb-5 flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            type="button"
          >
            {cancelText}
          </button>
          <button
            ref={confirmButtonRef}
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 rounded-lg font-semibold text-sm ${confirmClass} disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-w-[100px] flex items-center justify-center`}
            type="button"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Processing...
              </>
            ) : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
