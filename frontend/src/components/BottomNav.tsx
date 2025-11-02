// ========================================
// Bottom Navigation Component
// Mobile navigation for waiter interface
// ========================================

import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { Table, ClipboardText } from "@phosphor-icons/react";

interface BottomNavProps {
  className?: string;
}

export default function BottomNav({ className = "" }: BottomNavProps) {
  const location = useLocation();
  const currentPath = location.pathname;

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
              <span className="text-xl" aria-hidden>
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
