// ========================================
// Bottom Navigation Component
// Mobile navigation for waiter interface
// ========================================

import { Link, useLocation } from "react-router-dom";

interface BottomNavProps {
  className?: string;
}

export default function BottomNav({ className = "" }: BottomNavProps) {
  const location = useLocation();
  const currentPath = location.pathname;

  const navItems = [
    {
      path: "/tables",
      icon: "🪑",
      label: "Tables",
    },
    {
      path: "/active-orders",
      icon: "📋",
      label: "Orders",
    },
  ];

  return (
    <nav
      className={`
        fixed bottom-0 left-0 right-0
        bg-off-white border-t border-neutral-border
        shadow-[0_-4px_6px_rgba(0,0,0,0.07)]
        h-[60px]
        z-40
        ${className}
      `}
    >
      <div className="flex h-full">
        {navItems.map((item) => {
          const isActive = currentPath === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex-1 flex flex-col items-center justify-center gap-1
                transition-colors duration-200
                min-h-touch cursor-pointer
                ${
                  isActive
                    ? "bg-coffee-brown text-cream"
                    : "text-neutral-text-light hover:text-coffee-brown hover:bg-cream"
                }
              `}
            >
              <span className="text-xl" role="img" aria-label={item.label}>
                {item.icon}
              </span>
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
