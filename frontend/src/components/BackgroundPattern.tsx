// ========================================
// Background Pattern Component
// Decorative cafe-themed background pattern
// ========================================

interface BackgroundPatternProps {
  opacity?: number;
  density?: 'light' | 'medium' | 'dense';
}

export default function BackgroundPattern({
  opacity = 0.03,
  density = 'light'
}: BackgroundPatternProps) {
  // Adjust spacing based on density
  const spacing = {
    light: '120px',
    medium: '80px',
    dense: '50px'
  }[density];

  return (
    <div
      className="fixed inset-0 pointer-events-none z-0"
      style={{ opacity }}
      aria-hidden="true"
    >
      <svg
        width="100%"
        height="100%"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id="cafe-pattern"
            x="0"
            y="0"
            width={spacing}
            height={spacing}
            patternUnits="userSpaceOnUse"
          >
            {/* Coffee Bean */}
            <g transform="translate(20, 20)">
              <ellipse
                cx="12"
                cy="12"
                rx="8"
                ry="10"
                fill="none"
                stroke="var(--color-coffee-light)"
                strokeWidth="1.5"
              />
              <path
                d="M 12 6 Q 8 12 12 18"
                fill="none"
                stroke="var(--color-coffee-light)"
                strokeWidth="1.5"
              />
            </g>

            {/* Coffee Cup */}
            <g transform="translate(60, 60)">
              <path
                d="M 8 16 L 6 24 L 18 24 L 16 16 Z"
                fill="none"
                stroke="var(--color-coffee-light)"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <line
                x1="6"
                y1="16"
                x2="18"
                y2="16"
                stroke="var(--color-coffee-light)"
                strokeWidth="1.5"
              />
              {/* Steam */}
              <path
                d="M 9 14 Q 9 12 10 12 Q 11 12 11 10"
                fill="none"
                stroke="var(--color-coffee-light)"
                strokeWidth="1"
                opacity="0.6"
              />
              <path
                d="M 13 14 Q 13 12 14 12 Q 15 12 15 10"
                fill="none"
                stroke="var(--color-coffee-light)"
                strokeWidth="1"
                opacity="0.6"
              />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#cafe-pattern)" />
      </svg>
    </div>
  );
}
