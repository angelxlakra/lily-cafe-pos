
// ========================================
// Analytics Dashboard Page
// Powered by Thesys C1 Generative UI
// ========================================

import { useState } from 'react';
import AnalyticsDashboard from './analytics/AnalyticsDashboard';
import AskQuestionsView from './analytics/AskQuestionsView';
import PageHeader from '../components/PageHeader';

type ViewMode = 'dashboard' | 'ask';

export default function AnalyticsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');

  return (
    <div className="flex flex-col h-full bg-neutral-background">

      <PageHeader title="Analytics" />

      {/* View Toggle */}
      <div className="flex p-1 bg-cream border border-neutral-border rounded-full mx-4 mt-3 mb-0 w-fit">
        <button
          onClick={() => setViewMode('dashboard')}
          className={`px-4 py-1.5 text-sm font-semibold rounded-full transition-colors ${
            viewMode === 'dashboard'
              ? 'bg-coffee-brown text-cream shadow-sm'
              : 'text-neutral-text-light hover:text-coffee-dark'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setViewMode('ask')}
          className={`px-4 py-1.5 text-sm font-semibold rounded-full transition-colors ${
            viewMode === 'ask'
              ? 'bg-coffee-brown text-cream shadow-sm'
              : 'text-neutral-text-light hover:text-coffee-dark'
          }`}
        >
          Ask Questions
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6 md:p-8">
        {viewMode === 'dashboard' ? (
          <AnalyticsDashboard />
        ) : (
          <AskQuestionsView />
        )}
      </div>
    </div>
  );
}
