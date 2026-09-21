import React, { createContext, useContext, useEffect, useRef, useState } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'lily-cafe-theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Load theme from localStorage or default to light
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
    return 'light';
  });

  // Apply theme to document
  const isFirstApply = useRef(true);
  useEffect(() => {
    // Update document root class
    const root = document.documentElement;

    // Fade colours only during an actual switch, never on first paint
    // (see .theme-switching in index.css).
    let switchTimer: number | undefined;
    if (!isFirstApply.current) {
      root.classList.add('theme-switching');
      switchTimer = window.setTimeout(() => root.classList.remove('theme-switching'), 300);
    }
    isFirstApply.current = false;

    root.classList.remove('light', 'dark');
    root.classList.add(theme);

    // Store preference
    localStorage.setItem(THEME_STORAGE_KEY, theme);

    return () => window.clearTimeout(switchTimer);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((current) => (current === 'light' ? 'dark' : 'light'));
  };

  const value: ThemeContextType = {
    theme,
    setTheme,
    toggleTheme,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook to access theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
