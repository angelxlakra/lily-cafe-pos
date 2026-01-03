import { toast as sonnerToast, ExternalToast } from 'sonner'

/**
 * Toast notification utilities
 * Provides a consistent interface for showing notifications throughout the app
 */

interface ToastOptions extends ExternalToast {
  duration?: number
  description?: string
}

export const toast = {
  /**
   * Show a success message
   * @param message - The success message to display
   * @param options - Optional configuration
   */
  success: (message: string, options?: ToastOptions) => {
    return sonnerToast.success(message, {
      duration: options?.duration ?? 3000,
      ...options,
    })
  },

  /**
   * Show an error message
   * @param message - The error message to display
   * @param options - Optional configuration
   */
  error: (message: string, options?: ToastOptions) => {
    return sonnerToast.error(message, {
      duration: options?.duration ?? 4000,
      ...options,
    })
  },

  /**
   * Show an info message
   * @param message - The info message to display
   * @param options - Optional configuration
   */
  info: (message: string, options?: ToastOptions) => {
    return sonnerToast.info(message, {
      duration: options?.duration ?? 3000,
      ...options,
    })
  },

  /**
   * Show a warning message
   * @param message - The warning message to display
   * @param options - Optional configuration
   */
  warning: (message: string, options?: ToastOptions) => {
    return sonnerToast.warning(message, {
      duration: options?.duration ?? 3000,
      ...options,
    })
  },

  /**
   * Show a loading message
   * Returns a toast ID that can be used to dismiss or update the toast
   * @param message - The loading message to display
   */
  loading: (message: string) => {
    return sonnerToast.loading(message)
  },

  /**
   * Show a promise-based toast that automatically updates based on promise state
   * @param promise - The promise to track
   * @param messages - Messages for loading, success, and error states
   */
  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string
      success: string | ((data: T) => string)
      error: string | ((error: Error) => string)
    }
  ) => {
    return sonnerToast.promise(promise, messages)
  },

  /**
   * Dismiss a specific toast by ID
   * @param toastId - The ID of the toast to dismiss
   */
  dismiss: (toastId?: string | number) => {
    return sonnerToast.dismiss(toastId)
  },
}
