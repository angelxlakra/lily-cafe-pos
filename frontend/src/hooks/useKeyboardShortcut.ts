import { useEffect } from 'react'

/**
 * Keyboard shortcut hook
 * Enables keyboard shortcuts throughout the application
 *
 * @example
 * useKeyboardShortcut('Escape', handleClose)
 * useKeyboardShortcut('s', handleSave, { ctrl: true })
 * useKeyboardShortcut('/', handleSearch, { preventDefault: true })
 */

interface ShortcutOptions {
  /** Require Ctrl/Cmd key */
  ctrl?: boolean
  /** Require Shift key */
  shift?: boolean
  /** Require Alt key */
  alt?: boolean
  /** Prevent default browser behavior */
  preventDefault?: boolean
  /** Only trigger when condition is true */
  enabled?: boolean
}

export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  options: ShortcutOptions = {}
) {
  const {
    ctrl = false,
    shift = false,
    alt = false,
    preventDefault = false,
    enabled = true,
  } = options

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if modifiers match
      const ctrlPressed = event.ctrlKey || event.metaKey // Support both Ctrl and Cmd
      const shiftPressed = event.shiftKey
      const altPressed = event.altKey

      // Check if the key matches (case-insensitive for letters)
      const keyMatches = event.key.toLowerCase() === key.toLowerCase()

      if (
        keyMatches &&
        ctrlPressed === ctrl &&
        shiftPressed === shift &&
        altPressed === alt
      ) {
        if (preventDefault) {
          event.preventDefault()
        }
        callback()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [key, callback, ctrl, shift, alt, preventDefault, enabled])
}

/**
 * Multiple keyboard shortcuts hook
 *
 * @example
 * useKeyboardShortcuts({
 *   's': { handler: handleSave, ctrl: true },
 *   'Escape': { handler: handleClose },
 *   '/': { handler: focusSearch, preventDefault: true }
 * })
 */

interface ShortcutConfig extends ShortcutOptions {
  handler: () => void
}

export function useKeyboardShortcuts(
  shortcuts: Record<string, ShortcutConfig>
) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase()
      const config = shortcuts[key] || shortcuts[event.key]

      if (!config) return

      const {
        handler,
        ctrl = false,
        shift = false,
        alt = false,
        preventDefault = false,
        enabled = true,
      } = config

      if (!enabled) return

      const ctrlPressed = event.ctrlKey || event.metaKey
      const shiftPressed = event.shiftKey
      const altPressed = event.altKey

      if (
        ctrlPressed === ctrl &&
        shiftPressed === shift &&
        altPressed === alt
      ) {
        if (preventDefault) {
          event.preventDefault()
        }
        handler()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}

/**
 * Common keyboard shortcuts for reference
 */
export const KEYBOARD_SHORTCUTS = {
  SAVE: { key: 's', ctrl: true, description: 'Save' },
  CLOSE: { key: 'Escape', description: 'Close modal/drawer' },
  SEARCH: { key: '/', description: 'Focus search' },
  NEW: { key: 'n', ctrl: true, description: 'New item' },
  EDIT: { key: 'e', ctrl: true, description: 'Edit' },
  DELETE: { key: 'Delete', description: 'Delete' },
  HELP: { key: '?', shift: true, description: 'Show keyboard shortcuts' },
  NEXT: { key: 'ArrowDown', description: 'Next item' },
  PREV: { key: 'ArrowUp', description: 'Previous item' },
  SUBMIT: { key: 'Enter', ctrl: true, description: 'Submit form' },
} as const
