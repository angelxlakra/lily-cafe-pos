// ========================================
// Login Page Component
// Admin authentication with JWT
// ========================================

import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoggingIn, isAuthenticated } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Redirect if already authenticated
  if (isAuthenticated) {
    navigate('/admin/active-orders', { replace: true });
    return null;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    try {
      await login({ username: username.trim(), password });
      // Success - navigate to admin dashboard
      navigate('/admin/active-orders', { replace: true });
    } catch (err) {
      // Handle login error
      if (err instanceof Error) {
        setError(err.message || 'Invalid credentials');
      } else {
        setError('Login failed. Please check your credentials.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-neutral-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-coffee-brown mb-2">
            Lily Cafe POS
          </h1>
          <p className="text-neutral-text-light">
            Admin Portal
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-off-white border border-neutral-border rounded-lg shadow-lg p-8">
          <h2 className="text-xl font-semibold text-neutral-text-dark mb-6">
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username Field */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoggingIn}
                className="w-full px-4 py-3 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown
                         disabled:bg-neutral-border disabled:cursor-not-allowed
                         transition-colors"
                placeholder="admin"
                autoComplete="username"
                autoFocus
              />
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoggingIn}
                className="w-full px-4 py-3 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown
                         disabled:bg-neutral-border disabled:cursor-not-allowed
                         transition-colors"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-error/10 border border-error rounded-lg p-3">
                <p className="text-sm text-error font-medium">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full btn bg-coffee-brown text-cream hover:bg-coffee-dark
                       disabled:bg-neutral-border disabled:cursor-not-allowed
                       transition-colors h-12 text-base font-semibold"
            >
              {isLoggingIn ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
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
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Info Text */}
          <div className="mt-6 text-center">
            <p className="text-sm text-neutral-text-light">
              Default credentials: <span className="font-mono font-medium text-neutral-text-dark">admin</span> / <span className="font-mono font-medium text-neutral-text-dark">changeme123</span>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/tables')}
            className="text-sm text-neutral-text-light hover:text-coffee-brown transition-colors"
          >
            � Back to Waiter Interface
          </button>
        </div>
      </div>
    </div>
  );
}
