
// ========================================
// Analytics Dashboard Page
// Powered by Thesys C1 Generative UI
// ========================================

import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useTheme } from '../contexts/ThemeContext';
import AnalyticsDashboard from './analytics/AnalyticsDashboard';
import AskQuestionsView from './analytics/AskQuestionsView';
import { ChartLine, ChatCircleDots } from '@phosphor-icons/react';

type ViewMode = 'dashboard' | 'ask';

export default function AnalyticsPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const { theme } = useTheme();

  return (
    <div className="flex min-h-screen bg-neutral-background">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      <div className="flex-1 flex flex-col p-6 md:p-8 lg:ml-60 h-screen overflow-hidden">
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0">
          <div>
            <h1 className="font-heading heading-display text-coffee-brown mb-2">
              {viewMode === 'dashboard' ? 'Analytics Dashboard' : 'Ask Questions'}
            </h1>
            <p className="text-neutral-text-light">
              {viewMode === 'dashboard'
                ? 'View sales, revenue, and performance metrics'
                : 'Interactive conversational analytics powered by Thesys C1'}
            </p>
          </div>

          {/* View Toggle */}
          <div className="flex p-1 rounded-lg border border-neutral-border bg-neutral-surface" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
            <button
              onClick={() => setViewMode('dashboard')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                viewMode === 'dashboard'
                  ? 'bg-coffee-brown text-white shadow-sm'
                  : 'text-neutral-text hover:bg-neutral-light dark:hover:bg-gray-700'
              }`}
            >
              <ChartLine size={18} weight={viewMode === 'dashboard' ? 'bold' : 'regular'} />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setViewMode('ask')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                viewMode === 'ask'
                  ? 'bg-coffee-brown text-white shadow-sm'
                  : 'text-neutral-text hover:bg-neutral-light dark:hover:bg-gray-700'
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
            <AskQuestionsView />
          )}
        </div>
      </div>
    </div>
  );
}
