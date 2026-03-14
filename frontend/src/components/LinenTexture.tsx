// frontend/src/components/LinenTexture.tsx
import { useTheme } from '../contexts/ThemeContext';

export default function LinenTexture() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div
      className="fixed inset-0 pointer-events-none z-0"
      style={{ opacity: isDark ? 0.05 : 0.08 }}
      aria-hidden="true"
    >
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern
            id="linen-pattern"
            x="0"
            y="0"
            width="4"
            height="4"
            patternUnits="userSpaceOnUse"
          >
            {/* Horizontal thread */}
            <line
              x1="0" y1="0" x2="4" y2="0"
              stroke="var(--color-coffee-light)"
              strokeWidth="0.5"
            />
            {/* Vertical thread */}
            <line
              x1="0" y1="0" x2="0" y2="4"
              stroke="var(--color-coffee-light)"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#linen-pattern)" />
      </svg>
    </div>
  );
}
