import { Moon, Sun } from '@phosphor-icons/react';
import { useTheme } from '../contexts/ThemeContext';

export function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative flex items-center justify-center w-12 h-12 rounded-full 
        transition-all duration-300 hover:scale-110 active:scale-95
        border-2 border-neutral-border
        bg-gradient-soft dark:bg-gradient-primary
        shadow-medium dark:shadow-strong
      `}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {/* Icon Container with rotation animation */}
      <div
        className={`flex items-center justify-center transition-transform duration-500 ${
          isDark ? 'rotate-180' : 'rotate-0'
        }`}
      >
        {isDark ? (
          <Moon
            size={24}
            weight="fill"
            className="text-coffee-brown drop-shadow-md"
          />
        ) : (
          <Sun
            size={24}
            weight="fill"
            className="text-coffee-brown drop-shadow-md"
          />
        )}
      </div>
    </button>
  );
}
