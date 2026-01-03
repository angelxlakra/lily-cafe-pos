import { X, Keyboard } from '@phosphor-icons/react'
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut'
import { useState } from 'react'

interface Shortcut {
  keys: string
  description: string
  section: 'General' | 'Navigation' | 'Actions'
}

const shortcuts: Shortcut[] = [
  // General
  { keys: '?', description: 'Show keyboard shortcuts', section: 'General' },
  { keys: 'Esc', description: 'Close modal or drawer', section: 'General' },
  { keys: '/', description: 'Focus search', section: 'General' },

  // Navigation
  { keys: 'Ctrl+B', description: 'Go back', section: 'Navigation' },

  // Actions
  { keys: 'Ctrl+S', description: 'Open cart / Save', section: 'Actions' },
  { keys: 'Ctrl+Enter', description: 'Submit form', section: 'Actions' },
]

export default function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false)

  // Trigger with Shift+? (which is just "?")
  useKeyboardShortcut('?', () => setIsOpen(true), { shift: true })
  useKeyboardShortcut('Escape', () => setIsOpen(false), { enabled: isOpen })

  if (!isOpen) return null

  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.section]) {
      acc[shortcut.section] = []
    }
    acc[shortcut.section].push(shortcut)
    return acc
  }, {} as Record<string, Shortcut[]>)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) setIsOpen(false)
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <div className="bg-off-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-2xl w-full p-6 animate-in zoom-in duration-300">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-coffee-brown/10 flex items-center justify-center">
              <Keyboard size={24} className="text-coffee-brown" aria-hidden="true" />
            </div>
            <h2
              id="shortcuts-title"
              className="text-2xl font-heading font-bold text-neutral-text-dark dark:text-neutral-text-light"
            >
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-neutral-text-light hover:text-neutral-text-dark dark:hover:text-white transition-colors"
            aria-label="Close shortcuts help"
          >
            <X size={24} aria-hidden="true" />
          </button>
        </div>

        {/* Shortcuts List */}
        <div className="space-y-6">
          {Object.entries(groupedShortcuts).map(([section, items]) => (
            <div key={section}>
              <h3 className="text-sm font-semibold text-neutral-text-light dark:text-neutral-text uppercase tracking-wider mb-3">
                {section}
              </h3>
              <div className="space-y-2">
                {items.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-neutral-background dark:hover:bg-neutral-700 transition-colors"
                  >
                    <span className="text-neutral-text-dark dark:text-neutral-text-light">
                      {shortcut.description}
                    </span>
                    <kbd className="px-3 py-1.5 text-sm font-semibold bg-white dark:bg-neutral-900 border border-neutral-border dark:border-neutral-600 rounded-md shadow-sm font-mono">
                      {shortcut.keys}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-neutral-border dark:border-neutral-700">
          <p className="text-sm text-neutral-text-light dark:text-neutral-text text-center">
            Press <kbd className="px-2 py-1 bg-white dark:bg-neutral-900 border border-neutral-border dark:border-neutral-600 rounded font-mono text-xs">?</kbd> anytime to see this help
          </p>
        </div>
      </div>
    </div>
  )
}
