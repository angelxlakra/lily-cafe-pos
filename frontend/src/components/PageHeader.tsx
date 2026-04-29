// frontend/src/components/PageHeader.tsx
import type { ReactNode } from 'react';
import { useSidebar } from '../context/SidebarContext';
import { List } from '@phosphor-icons/react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export default function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  const { setMobileOpen } = useSidebar();

  return (
    <header className="bg-off-white border-b-2 border-coffee-brown px-4 py-4 md:px-6 md:py-5 relative z-10">
      <div className="flex items-start gap-4">
        {/* Hamburger — mobile only */}
        <button
          onClick={() => setMobileOpen(true)}
          className="lg:hidden flex-shrink-0 mt-1 w-9 h-9 flex items-center justify-center rounded-lg text-coffee-brown hover:bg-cream/60 transition-colors"
          aria-label="Open menu"
        >
          <List size={22} weight="bold" />
        </button>

        {/* Title block */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold tracking-widest uppercase text-lily-green mb-0.5">
            Lily Cafe · Admin
          </p>
          <h1 className="font-heading italic text-2xl md:text-3xl text-coffee-dark leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-neutral-text-light mt-0.5">{subtitle}</p>
          )}
        </div>

        {/* Action slot — desktop: right-aligned in same row */}
        {action && (
          <div className="hidden lg:flex flex-shrink-0 items-center">
            {action}
          </div>
        )}
      </div>

      {/* Action slot — mobile: full-width second row */}
      {action && (
        <div className="lg:hidden mt-3">
          {action}
        </div>
      )}
    </header>
  );
}
