/**
 * DailyCountTab
 *
 * Where tonight's count starts: its status (not started, in progress on this
 * phone, or done) with one action, plus the last few saved counts. The count
 * itself happens full-screen at /admin/inventory/count.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ClipboardText, Upload } from '@phosphor-icons/react';
import { inventoryApi } from '../../api/inventory';
import TemplateImportModal from './TemplateImportModal';
import ConfirmDialog from '../ConfirmDialog';
import LoadingSpinner from '../LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';
import { clearCountDraft, loadCountDraft } from '../../utils/countDraft';
import type { CountSummary } from '../../types/inventory';

const formatTime = (date: Date) => date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

/** business_date is a plain YYYY-MM-DD, not a timestamp. */
const formatBusinessDate = (value: string) => {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
};

/** Stored timestamps are UTC; SQLite returns them without an offset. */
const savedAt = (count: CountSummary) =>
  count.created_at
    ? new Date(/([zZ]|[+-]\d\d:?\d\d)$/.test(count.created_at) ? count.created_at : `${count.created_at}Z`)
        .toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: 'numeric', minute: '2-digit' })
    : null;

const tally = (count: CountSummary) =>
  `${count.items_checked} checked · ${count.items_changed} changed · ${count.items_skipped} not counted`;

export default function DailyCountTab() {
  const { isOwner } = useAuth();
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [draft, setDraft] = useState(loadCountDraft);
  const [confirmingDiscard, setConfirmingDiscard] = useState(false);

  const { data: groups, isLoading } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });
  const { data: today } = useQuery({
    queryKey: ['inventory', 'counts', 'today'],
    queryFn: inventoryApi.getTodaysCount,
  });
  const { data: recent = [] } = useQuery({
    queryKey: ['inventory', 'counts', 'recent'],
    queryFn: () => inventoryApi.getCounts(7),
  });
  const { data: categories = [] } = useQuery({
    queryKey: ['inventory', 'categories'],
    queryFn: inventoryApi.getCategories,
    enabled: isOwner,
  });

  if (isLoading) {
    return (
      <div className="py-12 flex justify-center gap-3 text-neutral-text-muted">
        <LoadingSpinner /> Loading…
      </div>
    );
  }

  const itemTotal = groups?.reduce((sum, group) => sum + group.items.length, 0) ?? 0;

  if (itemTotal === 0) {
    return (
      <>
        <div className="card p-8 text-center">
          <Upload size={48} className="mx-auto text-neutral-text-muted mb-3" aria-hidden />
          <h2 className="font-heading text-xl! text-neutral-text-dark mb-2">No inventory items</h2>
          <p className="text-neutral-text-muted mb-6">
            {isOwner
              ? 'Import your items from the WhatsApp checklist, or add them in the Items tab.'
              : 'No items to count yet. Ask the owner to add them.'}
          </p>
          {isOwner && (
            <button onClick={() => setIsImportModalOpen(true)} className="btn-primary inline-flex items-center gap-2">
              <Upload size={20} weight="fill" aria-hidden />
              Import from WhatsApp checklist
            </button>
          )}
        </div>
        <TemplateImportModal
          isOpen={isImportModalOpen && isOwner}
          onClose={() => setIsImportModalOpen(false)}
          existingCategories={categories}
        />
      </>
    );
  }

  const draftEntries = draft ? Object.keys(draft.counts).length : 0;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <section className="card p-5" aria-labelledby="tonights-count">
        <div className="flex items-start gap-3">
          <ClipboardText size={28} className="text-coffee-brown shrink-0 mt-1" aria-hidden />
          <div className="flex-1 min-w-0">
            <h2 id="tonights-count" className="font-heading text-2xl! text-neutral-text-dark">Tonight's count</h2>
            <p className="mt-1 text-neutral-text-body tabular-nums">
              {draftEntries > 0
                ? `In progress on this phone · ${Math.min(draftEntries, itemTotal)} of ${itemTotal} counted · started ${formatTime(new Date(draft!.startedAt))}`
                : today
                  ? `Counted tonight${savedAt(today) ? ` at ${savedAt(today)}` : ''} by ${today.counted_by} · ${tally(today)}`
                  : `Not started · ${itemTotal} items to count`}
            </p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Link
            to="/admin/inventory/count"
            className={`${today && draftEntries === 0 ? 'btn-secondary' : 'btn-primary'} inline-flex items-center justify-center flex-1 sm:flex-none sm:min-w-56`}
          >
            {draftEntries > 0 ? 'Resume count' : today ? 'Count again' : "Start tonight's count"}
          </Link>
          {draftEntries > 0 && (
            <button type="button" onClick={() => setConfirmingDiscard(true)} className="btn-ghost">
              Discard
            </button>
          )}
        </div>
      </section>

      {recent.length > 0 && (
        <section aria-labelledby="recent-counts">
          <h2 id="recent-counts" className="font-heading text-xl! text-neutral-text-dark mb-2">Recent counts</h2>
          <ul className="card divide-y divide-neutral-border overflow-hidden">
            {recent.map(count => (
              <li key={count.id} className="px-4 py-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <span className="font-medium text-neutral-text-dark">
                  {formatBusinessDate(count.business_date)}
                  <span className="font-normal text-neutral-text-muted">
                    {savedAt(count) && <> · {savedAt(count)}</>} · {count.counted_by}
                  </span>
                </span>
                <span className={`text-sm tabular-nums ${count.items_skipped > 0 ? 'text-neutral-text-body' : 'text-neutral-text-muted'}`}>
                  {tally(count)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <ConfirmDialog
        isOpen={confirmingDiscard}
        onClose={() => setConfirmingDiscard(false)}
        onConfirm={() => {
          clearCountDraft();
          setDraft(null);
          setConfirmingDiscard(false);
        }}
        title="Discard this count?"
        message={`This removes the ${draftEntries} numbers entered on this phone. Saved stock doesn't change.`}
        confirmText="Discard"
        cancelText="Keep it"
        variant="danger"
      />
    </div>
  );
}
