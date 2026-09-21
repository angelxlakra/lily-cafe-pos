import { useEffect, useRef, useState } from 'react';

export type Presence = 'arrive' | 'highlight' | 'leave' | null;

const HIGHLIGHT_MS = 1700; // a little longer than the 1600ms highlight animation

/**
 * Tracks how a live list changed between refreshes so each row can animate
 * the change: new rows "arrive", rows for which `changed(before, after)` is
 * true "highlight", and removed rows stay one short exit ("leave") at their
 * old position before disappearing. The first load animates nothing.
 */
export function useListPresence<T extends { id: number }>(
  items: T[] | undefined,
  changed: (before: T, after: T) => boolean,
  exitMs = 220,
): { item: T; presence: Presence }[] {
  const previous = useRef<T[] | null>(null);
  const [marks, setMarks] = useState<Map<number, Presence>>(new Map());
  const [leaving, setLeaving] = useState<{ item: T; index: number }[]>([]);

  useEffect(() => {
    if (!items) return;
    const before = previous.current;
    previous.current = items;
    if (!before) return;

    const beforeById = new Map(before.map(item => [item.id, item]));
    const afterIds = new Set(items.map(item => item.id));
    const timers: number[] = [];

    const newMarks = new Map<number, Presence>();
    items.forEach(item => {
      const old = beforeById.get(item.id);
      if (!old) newMarks.set(item.id, 'arrive');
      else if (changed(old, item)) newMarks.set(item.id, 'highlight');
    });
    if (newMarks.size) {
      setMarks(current => new Map([...current, ...newMarks]));
      timers.push(window.setTimeout(() => {
        setMarks(current => {
          const next = new Map(current);
          newMarks.forEach((_, id) => next.delete(id));
          return next;
        });
      }, HIGHLIGHT_MS));
    }

    const gone = before
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => !afterIds.has(item.id));
    if (gone.length) {
      setLeaving(current => [...current, ...gone]);
      const goneIds = new Set(gone.map(({ item }) => item.id));
      timers.push(window.setTimeout(() => {
        setLeaving(current => current.filter(({ item }) => !goneIds.has(item.id)));
      }, exitMs));
    }
    // Timers are deliberately not cleared on the next refresh: each batch
    // removes only its own marks, so overlapping refreshes don't cut exits short.
  }, [items]); // eslint-disable-line react-hooks/exhaustive-deps

  const rows: { item: T; presence: Presence }[] = (items ?? []).map(item => ({
    item,
    presence: marks.get(item.id) ?? null,
  }));
  // Put leaving rows back where they were so the exit happens in place.
  [...leaving]
    .sort((a, b) => a.index - b.index)
    .forEach(({ item, index }) => {
      if (!rows.some(row => row.item.id === item.id)) {
        rows.splice(Math.min(index, rows.length), 0, { item, presence: 'leave' });
      }
    });
  return rows;
}

export const presenceClass: Record<Exclude<Presence, null>, string> = {
  arrive: 'animate-arrive',
  highlight: 'animate-highlight',
  leave: 'animate-depart pointer-events-none',
};
