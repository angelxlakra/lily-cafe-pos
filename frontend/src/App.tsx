import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

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

        <div className="mt-8 text-sm text-neutral-text-light">
          <p>Version 0.1.0 - The Order Taker</p>
          <p className="mt-2">Built with Vite + React 18 + TypeScript + Tailwind CSS v4</p>
        </div>
      </div>
    </div>
  )
}

export default App
