// Ask — natural-language questions about the cafe, answered by fixed reports.
//
// Built for a phone first: quick-question chips, a scrolling thread, and a
// composer pinned to the bottom. Every answer shows which report and which
// period it is, so a misread question is visible rather than silent.

import { ArrowCounterClockwise, PaperPlaneRight } from '@phosphor-icons/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { askQuestion, type AskResponse, type RouterDecision } from '../../api/ask';
import TodayCard from '../../components/ask/TodayCard';
import { ReportView } from '../../components/ask/renderers';
import { cn } from '../../utils/cn';

const QUICK_QUESTIONS = [
  'Sales today',
  'Sales this week',
  'Top items this month',
  'Best day this month',
  'Are we doing better than last week?',
  'Low stock',
  'Cash counter today',
];

type Message =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'assistant'; response: AskResponse }
  | { id: number; role: 'assistant'; error: string }
  | { id: number; role: 'assistant'; pending: true };

export default function AskView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const context = useRef<{ decision: RouterDecision | null; question: string | null }>({
    decision: null,
    question: null,
  });
  const nextId = useRef(1);
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const send = useCallback(
    async (question: string) => {
      const text = question.trim();
      if (!text || busy) return;
      setDraft('');
      setBusy(true);

      const userId = nextId.current++;
      const pendingId = nextId.current++;
      setMessages((prev) => [
        ...prev,
        { id: userId, role: 'user', text },
        { id: pendingId, role: 'assistant', pending: true },
      ]);

      try {
        const response = await askQuestion({
          question: text,
          previous: context.current.decision,
          previous_question: context.current.question,
        });
        // Carry context for clarifications too: after "Which one did you
        // mean?", the owner's next message is the answer, not a new question.
        context.current = { decision: response.decision, question: text };
        setMessages((prev) => prev.map((m) => (m.id === pendingId ? { id: pendingId, role: 'assistant', response } : m)));
      } catch (err) {
        const message = describeError(err);
        setMessages((prev) => prev.map((m) => (m.id === pendingId ? { id: pendingId, role: 'assistant', error: message } : m)));
      } finally {
        setBusy(false);
      }
    },
    [busy],
  );

  const reset = () => {
    context.current = { decision: null, question: null };
    setMessages([]);
    input.current?.focus();
  };

  return (
    <div className="flex h-full flex-col">
      {/* Quick questions */}
      <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => send(q)}
            disabled={busy}
            className="shrink-0 rounded-full border border-neutral-border bg-neutral-background px-3 py-1.5 text-sm text-neutral-text-body active:bg-cream disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Thread */}
      <div className="flex-1 space-y-3 overflow-y-auto pb-28 lg:pb-4">
        <TodayCard />
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-neutral-border p-4 text-sm text-neutral-text-light">
            Ask in English, Hindi or Hinglish — “which dish sold best since August?”, “kal ka cash counter”,
            “sabse zyada revenue kis din hua?”. Every answer shows the period it covers.
          </div>
        )}
        {messages.map((m) => (
          <MessageView key={m.id} message={m} onPick={send} />
        ))}
        <div ref={bottom} />
      </div>

      {/* Composer */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        // Below lg the admin layout scrolls as a document, so "sticky" would
        // just sit at the end of the thread; pin to the viewport instead.
        className="fixed inset-x-0 bottom-0 z-30 flex items-center gap-2 border-t border-neutral-border bg-neutral-background px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:sticky lg:inset-x-auto lg:-mx-4"
      >
        {messages.length > 0 && (
          <button
            type="button"
            onClick={reset}
            aria-label="Start over"
            title="Start over"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-neutral-text-light active:bg-cream"
          >
            <ArrowCounterClockwise size={20} />
          </button>
        )}
        <input
          ref={input}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about sales, items, stock…"
          enterKeyHint="send"
          autoComplete="off"
          autoCapitalize="sentences"
          className="h-11 min-w-0 flex-1 rounded-full border border-neutral-border bg-white px-4 text-base text-neutral-text-dark placeholder:text-neutral-text-muted focus:outline-none focus:ring-2 focus:ring-coffee-brown/40 dark:bg-off-white"
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          aria-label="Send"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-coffee-brown text-white disabled:opacity-40"
        >
          <PaperPlaneRight size={20} weight="fill" />
        </button>
      </form>
    </div>
  );
}

function MessageView({ message, onPick }: { message: Message; onPick: (q: string) => void }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-coffee-brown px-4 py-2 text-sm text-white">
          {message.text}
        </div>
      </div>
    );
  }

  if ('pending' in message) {
    return (
      <Card>
        <div className="flex items-center gap-2 text-sm text-neutral-text-light">
          <span className="h-2 w-2 animate-pulse rounded-full bg-coffee-brown" />
          Looking that up…
        </div>
      </Card>
    );
  }

  if ('error' in message) {
    return (
      <Card tone="error">
        <p className="text-sm text-error">{message.error}</p>
      </Card>
    );
  }

  const r = message.response;

  if (r.kind === 'report' && r.report_id && r.data) {
    return (
      <Card>
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
          <h2 className="text-base font-semibold text-neutral-text-dark">
            {r.title}
            {r.dish ? ` · ${r.dish}` : ''}
          </h2>
          {r.period_label && (
            <span className="shrink-0 rounded-full bg-cream px-2 py-0.5 text-xs text-neutral-text-body">{r.period_label}</span>
          )}
        </div>
        {r.caption && <p className="mb-4 text-sm leading-relaxed text-neutral-text-body">{r.caption}</p>}
        <ReportView reportId={r.report_id} data={r.data} />
      </Card>
    );
  }

  return (
    <Card tone={r.kind === 'unsupported' ? 'muted' : undefined}>
      <p className="text-sm text-neutral-text-body">{r.message}</p>
      {r.candidates.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {r.candidates.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => onPick(c)}
              className="rounded-full border border-coffee-brown px-3 py-1.5 text-sm text-coffee-brown active:bg-cream"
            >
              {c}
            </button>
          ))}
        </div>
      )}
    </Card>
  );
}

function Card({ children, tone }: { children: React.ReactNode; tone?: 'error' | 'muted' }) {
  return (
    <div
      className={cn(
        'rounded-2xl rounded-bl-md border border-neutral-border bg-white p-4 shadow-sm dark:bg-off-white',
        tone === 'error' && 'border-error/40',
        tone === 'muted' && 'bg-neutral-background',
      )}
    >
      {children}
    </div>
  );
}

function describeError(err: unknown): string {
  const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
  if (status?.status === 503) return 'Ask isn’t set up on this server yet.';
  if (status?.status === 403) return 'Only the owner login can use Ask.';
  if (status?.data?.detail) return String(status.data.detail);
  return 'Something went wrong. Please try again.';
}
