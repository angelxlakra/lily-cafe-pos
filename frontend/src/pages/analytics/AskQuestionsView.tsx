
import { C1Chat, ThemeProvider, useThreadListManager, useThreadManager } from '@thesysai/genui-sdk';
import '../../../node_modules/@thesysai/genui-sdk/dist/genui-sdk.css';
import '../../../node_modules/@crayonai/react-ui/dist/styles/index.css';
import { useTheme } from '../../contexts/ThemeContext';
import { useState, useCallback } from 'react';

// Thread Types (matching Thesys SDK expectations)
interface Thread {
  threadId: string;
  title: string;
  createdAt: Date;  // Must be Date object, not string!
}

export default function AskQuestionsView() {
  const { theme } = useTheme();

  // Local state to simulate backend thread persistence
  const [threads, setThreads] = useState<Thread[]>([{ threadId: 'current', title: 'Current Session', createdAt: new Date() }]);
  const [activeThreadId, setActiveThreadId] = useState<string>('current');
  const [messagesByThread, setMessagesByThread] = useState<Record<string, any[]>>({ 'current': [] });

  // Simulated Thread List Manager
  const threadListManager = useThreadListManager({
    fetchThreadList: async () => {
        // Return local threads
        return threads;
    },
    createThread: async (firstMessage: any) => {
        const newThreadId = `thread-${Date.now()}`;
        const newThread: Thread = {
            threadId: newThreadId,
            title: firstMessage?.content?.substring(0, 30) || 'New Chat',
            createdAt: new Date()  // Date object, not ISO string!
        };
        setThreads(prev => [newThread, ...prev]);
        setMessagesByThread(prev => ({ ...prev, [newThreadId]: [] }));
        setActiveThreadId(newThreadId);
        return newThread;
    },
    deleteThread: async (threadId: string) => {
        setThreads(prev => prev.filter(t => t.threadId !== threadId));
        if (activeThreadId === threadId) {
            setActiveThreadId('');
        }
    },
    updateThread: async (thread: any) => {
        setThreads(prev => prev.map(t => t.threadId === thread.threadId ? { ...t, title: thread.name } : t));
    },
    onSelectThread: (threadId: string) => {
        setActiveThreadId(threadId);
    },
    onSwitchToNew: () => {
        setActiveThreadId(''); // Empty ID usually signifies "new thread" state in generic UIs, or we create one immediately
    }
  });

  // Simulated Thread Manager
  const threadManager = useThreadManager({
    threadListManager,
    loadThread: async (threadId: string) => {
        if (!threadId) return [];
        return messagesByThread[threadId] || [];
    },
    apiUrl: "http://localhost:8000/api/v1/analytics/query",
    // We need to intercept messages to save them locally if we want persistence across clicks
    // But useThreadManager with apiUrl handles sending. 
    // We might need to sync the state back to messagesByThread if we want "switching" to work without a real backend.
    // For now, let's just see if this structure enables the buttons.
  });

  return (
    <div className="p-6 rounded-lg shadow-md border border-neutral-border flex flex-col h-[700px]" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
      <h2 className="font-heading text-xl mb-4" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
        Ask Questions About Your Data
      </h2>
      <p className="mb-6 text-sm" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : '#6b7280' }}>
        Use natural language to explore your data.
      </p>

      <div className="flex-1 min-h-0 border rounded-lg overflow-hidden border-neutral-border bg-neutral-background">
        <ThemeProvider mode={theme === 'dark' ? 'dark' : 'light'}>
          <C1Chat
              threadManager={threadManager}
              threadListManager={threadListManager}
              agentName="Lily Cafe Analytics"
          />
        </ThemeProvider>
      </div>
    </div>
  );
}
