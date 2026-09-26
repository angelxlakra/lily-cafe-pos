// The morning digest, shown above the Ask thread.
//
// Every sentence here was composed by the backend from the same reports the
// cards below use — nothing on this card is written or derived in the
// browser, so it cannot disagree with the answer to the same question asked
// directly.

import { Warning } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';

import { fetchDigest, type Digest } from '../../api/ask';
import { cn } from '../../utils/cn';

export default function TodayCard() {
  const [digest, setDigest] = useState<Digest | null>(null);

  useEffect(() => {
    let cancelled = false;
    // A missing digest is the normal state on a quiet morning or a fresh
    // install, so a failure here is silence, not an error the owner must read.
    fetchDigest()
      .then((result) => {
        if (!cancelled) setDigest(result);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  if (!digest || (digest.lines.length === 0 && digest.flags.length === 0)) return null;

  return (
    <section
      aria-label="Morning digest"
      className="mb-3 rounded-2xl border border-neutral-border bg-cream p-4"
    >
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold text-neutral-text-dark">Today</h2>
        <span className="shrink-0 text-xs text-neutral-text-light">{formatDay(digest.date)}</span>
      </div>

      <ul className="space-y-1.5">
        {digest.lines.map((line) => (
          <li key={line.kind} className="text-sm leading-relaxed text-neutral-text-body">
            {line.text}
          </li>
        ))}
      </ul>

      {digest.flags.length > 0 && (
        <ul className="mt-3 space-y-1.5 border-t border-neutral-border pt-3">
          {digest.flags.map((flag) => (
            <li
              key={flag.rule}
              className={cn(
                'flex items-start gap-2 text-sm leading-relaxed',
                flag.severity === 'warn' ? 'text-warning' : 'text-neutral-text-body',
              )}
            >
              {flag.severity === 'warn' && (
                <Warning size={16} weight="fill" className="mt-0.5 shrink-0" aria-hidden />
              )}
              <span>{flag.sentence}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** "2026-09-19" → "Sat 19 Sep". The digest is always about one IST day. */
function formatDay(iso: string): string {
  const [year, month, day] = iso.split('-').map(Number);
  if (!year || !month || !day) return iso;
  return new Date(year, month - 1, day).toLocaleDateString('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}
