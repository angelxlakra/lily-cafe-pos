// ========================================
// Bottom Navigation Component
// Mobile navigation for waiter interface
// ========================================

import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { Table, ClipboardText, Sun, Moon } from "@phosphor-icons/react";
import { useTheme } from "../contexts/ThemeContext";

interface BottomNavProps {
  className?: string;
}

export default function BottomNav({ className = "" }: BottomNavProps) {
  const location = useLocation();
  const currentPath = location.pathname;
  const { toggleTheme, theme } = useTheme();

  const navItems: { path: string; icon: ReactNode; label: string }[] = [
    {
      path: "/tables",
      icon: <Table size={24} weight="duotone" />,
      label: "Tables",
    },
    {
      path: "/active-orders",
      icon: <ClipboardText size={24} weight="duotone" />,
      label: "Orders",
    },
  ];

  return (
    <nav
      className={`
        fixed bottom-0 left-0 right-0
        bg-off-white/95 border-t-2 border-neutral-border/50
        backdrop-blur-md
        shadow-[0_-8px_16px_rgba(44,36,32,0.08)]
        h-[64px]
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
                flex-1 flex flex-col items-center justify-center gap-1.5
                smooth-transition
                min-h-touch cursor-pointer
                relative
                ${
                  isActive
                    ? "bg-gradient-primary text-cream"
                    : "text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60"
                }
              `}
            >
              {/* Active indicator line */}
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-cream rounded-b-full"></div>
              )}

              <span className={`text-2xl ${isActive ? 'scale-110' : ''} smooth-transition`} aria-hidden>
                {item.icon}
              </span>
              <span className="text-xs font-semibold tracking-wide">{item.label}</span>
            </Link>
          );
        })}

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="flex-1 flex flex-col items-center justify-center gap-1.5 smooth-transition min-h-touch cursor-pointer text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60"
        >
          <span className="text-2xl">
            {theme === 'dark' ? <Moon size={24} weight="duotone" /> : <Sun size={24} weight="duotone" />}
          </span>
          <span className="text-xs font-semibold tracking-wide">Theme</span>
        </button>
      </div>
    </nav>
  );
}
