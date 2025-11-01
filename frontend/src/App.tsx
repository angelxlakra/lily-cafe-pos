import { useState } from 'react'
import { printTestReceipt, viewTestReceipt } from './utils/printTestReceipt'

function App() {
  const [count, setCount] = useState(0)
  const [isPrinting, setIsPrinting] = useState(false)
  const [printStatus, setPrintStatus] = useState<string>('')
  const [printError, setPrintError] = useState<string>('')

  const handlePrintReceipt = async () => {
    setIsPrinting(true)
    setPrintStatus('')
    setPrintError('')

    try {
      await printTestReceipt((message) => {
        setPrintStatus(message)
      })

      // Show success for 3 seconds then clear
      setTimeout(() => {
        setPrintStatus('')
      }, 3000)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      setPrintError(message)

      // Clear error after 5 seconds
      setTimeout(() => {
        setPrintError('')
      }, 5000)
    } finally {
      setIsPrinting(false)
    }
  }

  const handleViewReceipt = async () => {
    setIsPrinting(true)
    setPrintStatus('')
    setPrintError('')

    try {
      await viewTestReceipt((message) => {
        setPrintStatus(message)
      })

      // Show success for 3 seconds then clear
      setTimeout(() => {
        setPrintStatus('')
      }, 3000)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      setPrintError(message)

      // Clear error after 5 seconds
      setTimeout(() => {
        setPrintError('')
      }, 5000)
    } finally {
      setIsPrinting(false)
    }
  }

  return (
    <div className="min-h-screen bg-neutral-background flex items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-coffee-brown mb-4">
          Lily Cafe POS System
        </h1>
        <p className="text-lg text-neutral-text-light mb-8">
          Welcome to Mary's Kitchen Point of Sale
        </p>

        <div className="bg-white p-8 rounded-lg shadow-lg border border-neutral-border">
          <p className="text-neutral-text-dark mb-4">
            Frontend setup is complete!
          </p>
          <button
            onClick={() => setCount((count) => count + 1)}
            className="btn bg-coffee-brown text-white hover:bg-coffee-dark"
          >
            Count is {count}
          </button>
          <p className="mt-4 text-sm text-neutral-text-light">
            Click the button to test interactivity
          </p>
        </div>

        {/* Test Receipt Printing Section */}
        <div className="mt-6 bg-cream p-6 rounded-lg shadow-md border border-neutral-border">
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="text-2xl">🖨️</span>
            <h2 className="text-lg font-semibold text-coffee-brown">
              Test Receipt Printer
            </h2>
          </div>

          <p className="text-sm text-neutral-text-light mb-4">
            One-click test: Create order → Process payment → Print/View receipt
          </p>

          <div className="flex gap-3 justify-center">
            <button
              onClick={handlePrintReceipt}
              disabled={isPrinting}
              className="btn bg-info text-white hover:bg-[#1976D2] disabled:bg-neutral-border disabled:cursor-not-allowed"
            >
              {isPrinting ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  {printStatus || 'Processing...'}
                </span>
              ) : (
                '🖨️ Print Receipt'
              )}
            </button>

            <button
              onClick={handleViewReceipt}
              disabled={isPrinting}
              className="btn bg-lily-green text-white hover:bg-[#7A8C75] disabled:bg-neutral-border disabled:cursor-not-allowed"
            >
              {isPrinting ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  {printStatus || 'Processing...'}
                </span>
              ) : (
                '👁️ View in Tab'
              )}
            </button>
          </div>

          {/* Success Message */}
          {printStatus && !isPrinting && (
            <div className="mt-4 p-3 bg-success/10 border border-success rounded-md">
              <p className="text-sm text-success font-medium">{printStatus}</p>
            </div>
          )}

          {/* Error Message */}
          {printError && (
            <div className="mt-4 p-3 bg-error/10 border border-error rounded-md">
              <p className="text-sm text-error font-medium">{printError}</p>
            </div>
          )}

          <div className="mt-4 text-xs text-neutral-text-light">
            <p>💡 Tip: "Print" requires thermal printer connected. "View in Tab" works without printer.</p>
          </div>
        </div>

        <div className="mt-8 text-sm text-neutral-text-light">
          <p>Version 0.1.0 - The Order Taker</p>
          <p className="mt-2">Built with Vite + React 18 + TypeScript + Tailwind CSS v4</p>

          <div className="mt-6">
            <a
              href="/api-test"
              className="inline-block px-6 py-3 bg-info text-white rounded-lg hover:bg-[#1976D2] transition-colors"
            >
              🧪 Test API Client
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
