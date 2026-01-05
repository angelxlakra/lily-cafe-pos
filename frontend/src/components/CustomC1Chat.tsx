import { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { PaperPlaneRight, Spinner } from '@phosphor-icons/react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function CustomC1Chat() {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/analytics/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: { role: 'user', content: userMessage.content },
          threadId: 'custom-chat',
          responseId: Date.now().toString()
        })
      });

      if (!response.ok) throw new Error('Failed to get response');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          assistantContent += decoder.decode(value, { stream: true });
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="flex flex-col mx-auto w-full rounded-lg shadow-sm border border-neutral-border"
      style={{
        maxWidth: '900px',
        height: 'calc(100vh - 280px)',
        backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff'
      }}
    >
      {/* Header */}
      <div
        className="px-6 py-4 border-b border-neutral-border"
        style={{ backgroundColor: theme === 'dark' ? '#111827' : '#f9fafb' }}
      >
        <h2
          className="text-lg font-semibold"
          style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}
        >
          Analytics Assistant
        </h2>
        <p
          className="text-sm"
          style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}
        >
          Ask questions about your cafe's performance
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <p
              className="text-sm mb-4"
              style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}
            >
              Start by asking a question about your analytics
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                'What is the total revenue this month?',
                'Show me top selling products',
                'What were yesterday\'s sales?'
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-2 text-sm rounded-lg border transition-colors"
                  style={{
                    borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                    backgroundColor: theme === 'dark' ? '#1f2937' : '#f9fafb',
                    color: theme === 'dark' ? 'rgba(255, 255, 255, 0.8)' : '#6b7280'
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className="max-w-[80%] rounded-lg px-4 py-3"
              style={{
                backgroundColor: message.role === 'user'
                  ? '#5C3D2E'
                  : theme === 'dark' ? '#374151' : '#f3f4f6',
                color: message.role === 'user'
                  ? '#ffffff'
                  : theme === 'dark' ? 'rgba(255, 255, 255, 0.9)' : '#1f2937'
              }}
            >
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: message.content }}
              />
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div
              className="rounded-lg px-4 py-3 flex items-center gap-2"
              style={{
                backgroundColor: theme === 'dark' ? '#374151' : '#f3f4f6',
                color: theme === 'dark' ? 'rgba(255, 255, 255, 0.9)' : '#1f2937'
              }}
            >
              <Spinner className="animate-spin" size={16} />
              <span className="text-sm">Analyzing data...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        className="p-4 border-t border-neutral-border"
        style={{ backgroundColor: theme === 'dark' ? '#111827' : '#f9fafb' }}
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about revenue, products, orders..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-coffee-brown transition-all"
            style={{
              backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
              borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
              color: theme === 'dark' ? '#ffffff' : '#1f2937'
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            style={{
              backgroundColor: '#5C3D2E',
              color: '#ffffff'
            }}
          >
            {isLoading ? (
              <Spinner className="animate-spin" size={20} />
            ) : (
              <PaperPlaneRight size={20} weight="fill" />
            )}
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
