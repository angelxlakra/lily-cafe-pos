
// ========================================
// Analytics Dashboard Page
// Dashboard, plus Ask: questions answered by fixed reports
// ========================================

import { useState } from 'react';
import { useSidebar } from '../context/SidebarContext';
import AnalyticsDashboard from './analytics/AnalyticsDashboard';
import AskView from './analytics/AskView';
import { ChartLine, ChatCircleDots } from '@phosphor-icons/react';

type ViewMode = 'dashboard' | 'ask';

export default function AnalyticsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const { setMobileOpen } = useSidebar();

  return (
    <div className="flex flex-col h-full bg-neutral-background">

      <div className="flex-1 flex flex-col p-6 md:p-8 overflow-hidden">
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0">
          <div className="flex items-start gap-4">
             {/* Hamburger Menu Button for Mobile */}
             <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden mt-1 w-10 h-10 flex items-center justify-center rounded-lg bg-coffee-brown text-cream hover:bg-coffee-dark transition-colors flex-shrink-0"
              aria-label="Open menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 className="font-heading heading-display text-coffee-brown mb-2">
                {viewMode === 'dashboard' ? 'Analytics Dashboard' : 'Ask Questions'}
              </h1>
              <p className="text-neutral-text-light">
                {viewMode === 'dashboard'
                  ? 'View sales, revenue, and performance metrics'
                  : 'Ask about sales, items, stock and cash in plain words'}
              </p>
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex w-full md:w-auto p-1 rounded-lg border border-neutral-border bg-off-white">
            <button
              onClick={() => setViewMode('dashboard')}
              className={`flex flex-1 md:flex-none items-center justify-center gap-2 px-4 py-2 rounded-md transition-all ${
                viewMode === 'dashboard'
                  ? 'bg-coffee-brown text-white shadow-sm'
                  : 'text-neutral-text-body hover:bg-cream/60'
              }`}
            >
              <ChartLine size={18} weight={viewMode === 'dashboard' ? 'bold' : 'regular'} />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setViewMode('ask')}
              className={`flex flex-1 md:flex-none items-center justify-center gap-2 px-4 py-2 rounded-md transition-all ${
                viewMode === 'ask'
                  ? 'bg-coffee-brown text-white shadow-sm'
                  : 'text-neutral-text-body hover:bg-cream/60'
              }`}
            >
              <ChatCircleDots size={18} weight={viewMode === 'ask' ? 'bold' : 'regular'} />
              <span>Ask Questions</span>
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          {viewMode === 'dashboard' ? (
            <AnalyticsDashboard />
          ) : (
            <AskView />
          )}
        </div>
      </div>
    </div>
  );
}
