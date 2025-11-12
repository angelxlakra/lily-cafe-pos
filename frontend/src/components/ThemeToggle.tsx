import { Moon, Sun } from '@phosphor-icons/react';
import { useTheme } from '../contexts/ThemeContext';

export function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="relative flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 hover:scale-110 active:scale-95"
      style={{
        background: isDark
          ? 'linear-gradient(135deg, #2A2419 0%, #1C1812 100%)'
          : 'linear-gradient(135deg, #F5E6D3 0%, #FAF8F5 100%)',
        border: isDark ? '2px solid #4A4034' : '2px solid #D4C4B0',
        boxShadow: isDark
          ? '0 4px 12px rgba(0, 0, 0, 0.3)'
          : '0 4px 12px rgba(44, 36, 32, 0.12)',
      }}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {/* Icon Container with rotation animation */}
      <div
        className="flex items-center justify-center transition-transform duration-500"
        style={{
          transform: isDark ? 'rotate(180deg)' : 'rotate(0deg)',
        }}
      >
        {isDark ? (
          <Moon
            size={24}
            weight="fill"
            style={{
              color: '#B8916A',
              filter: 'drop-shadow(0 0 8px rgba(184, 145, 106, 0.4))',
            }}
          />
        ) : (
          <Sun
            size={24}
            weight="fill"
            style={{
              color: '#6F4E37',
              filter: 'drop-shadow(0 0 8px rgba(111, 78, 55, 0.3))',
            }}
          />
        )}
      </div>
    </button>
  );
}
