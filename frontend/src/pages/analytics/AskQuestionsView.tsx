import { C1Chat, ThemeProvider, useThreadListManager, useThreadManager } from '@thesysai/genui-sdk';
import '../../../node_modules/@thesysai/genui-sdk/dist/genui-sdk.css';
import '../../../node_modules/@crayonai/react-ui/dist/styles/index.css';
import { useTheme } from '../../contexts/ThemeContext';
import { themePresets } from "@crayonai/react-ui";
import { useState } from 'react';

// Thread Types (matching Thesys SDK expectations)
interface Thread {
  threadId: string;
  title: string;
  createdAt: Date;
}
 
export default function AskQuestionsView() {
  const { theme } = useTheme();

  // Local state to simulate backend thread persistence
  const [threads, setThreads] = useState<Thread[]>([{ threadId: 'current', title: 'Current Session', createdAt: new Date() }]);
  const [activeThreadId, setActiveThreadId] = useState<string>('current');
  const [messagesByThread, setMessagesByThread] = useState<Record<string, any[]>>({ 'current': [] });

  // Simulated Thread List Manager
  const threadListManager = useThreadListManager({
    fetchThreadList: async () => threads,
    createThread: async (firstMessage: any) => {
        const newThreadId = `thread-${Date.now()}`;
        const newThread: Thread = {
            threadId: newThreadId,
            title: firstMessage?.content?.substring(0, 30) || 'New Chat',
            createdAt: new Date()
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
        return {
            threadId: thread.threadId,
            title: thread.name,
            createdAt: new Date()
        }
    },
    onSelectThread: (threadId: string) => {
        setActiveThreadId(threadId);
    },
    onSwitchToNew: () => {
        setActiveThreadId('');
    }
  });
   
  // Simulated Thread Manager
  const threadManager = useThreadManager({
    threadListManager,
    loadThread: async (threadId: string) => {
        if (!threadId) return [];
        return messagesByThread[threadId] || [];
    },
    onUpdateMessage: ({ message }) => {
        setMessagesByThread(prev => {
            const threadId = activeThreadId; 
            const existing = prev[threadId] || [];
            // Check if message already exists to avoid duplicates if necessary, or just append
            // Assuming message has an ID or we just append
            return { ...prev, [threadId]: [...existing, message] };
        });
    },
    apiUrl: "http://localhost:8000/api/v1/analytics/query",
  });

  return (
    <div className="w-full flex items-start justify-center">
      <div
        className="rounded-lg shadow-sm"
        style={{
          width: '100%',
          height: "60px",
          minHeight: '80vh',
          backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
        }}
      >
        <ThemeProvider { ...themePresets.neon } mode={theme === 'dark' ? 'dark' : 'light' }>
          <C1Chat
              threadManager={threadManager}
              threadListManager={threadListManager}
              agentName="Lily Cafe Analytics"
              logoUrl="/logos/Lilycleaned.png"
              formFactor='full-page'
          />
        </ThemeProvider>
      </div>
    </div>
  );
}
