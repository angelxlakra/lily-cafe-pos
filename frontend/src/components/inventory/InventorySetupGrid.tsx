/**
 * InventorySetupGrid (owner only)
 *
 * Every active item as one editable table: kind, unit, pack size, alert
 * level and price, plus retiring dead items. Nothing is written until Save,
 * which sends only the changed rows in one request.
 *
 * Plain inputs in table cells, no grid library. Rows are memoized and only
 * the edited row gets a new object, so a keystroke re-renders one row, not
 * ~1,600 inputs. Paste from Google Sheets fills from the focused cell.
 */

import { memo, useCallback, useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowCounterClockwise, ArrowsIn, ArrowsOut, Copy, Lock, LockOpen, MagnifyingGlass } from '@phosphor-icons/react';
import { inventoryApi } from '../../api/inventory';
import { useInventoryCategories, useInventoryItems } from '../../hooks/useInventory';
import ConfirmDialog from '../ConfirmDialog';
import LoadingSpinner from '../LoadingSpinner';
import { describeApiError } from '../../utils/apiError';
import { formatQty, parseQty } from '../../utils/countQuantity';
import type { BulkItemUpdate, InventoryCategory, InventoryItem } from '../../types/inventory';

type Field =
  | 'category_id' | 'name' | 'count_mode' | 'current_quantity' | 'unit'
  | 'pack_size' | 'pack_unit' | 'min_threshold' | 'cost_per_unit';
type Cells = Record<Field, string>;
type RowState = { cells: Cells; retired: boolean };

const TICK_WIDTH = 44;
const RETIRE_WIDTH = 96;
const COLUMNS: { field: Field; label: string; width: number; left?: number; numeric?: boolean }[] = [
  { field: 'category_id', label: 'Category', width: 150, left: 44 },
  { field: 'name', label: 'Name', width: 220, left: 194 },
  { field: 'count_mode', label: 'Counted as', width: 130 },
  { field: 'current_quantity', label: 'Stock', width: 84, numeric: true },
  { field: 'unit', label: 'Unit', width: 96 },
  { field: 'pack_size', label: 'Pack size', width: 104, numeric: true },
  { field: 'pack_unit', label: 'Pack unit', width: 104 },
  { field: 'min_threshold', label: 'Alert below', width: 120, numeric: true },
  { field: 'cost_per_unit', label: 'Price ₹', width: 96, numeric: true },
];
const NUMERIC = new Set(COLUMNS.filter(c => c.numeric).map(c => c.field));
// A yes/no item has none of these; the server sets them.
const NOT_FOR_PRESENCE = new Set<Field>(['unit', 'pack_size', 'pack_unit', 'min_threshold', 'cost_per_unit']);
const MODE_LABEL: Record<string, string> = { number: 'Number', presence: 'Yes / no' };
const UNITS = ['pcs', 'kg', 'g', 'L', 'ml', 'bottle', 'tin', 'pkt', 'portion', 'box'];

// Stock is state, not configuration: editing it writes an adjustment that
// competes with the nightly count. Name and category are rarely what you came for.
const DEFAULT_LOCKS: Field[] = ['category_id', 'name', 'current_quantity'];
const LOCKS_KEY = 'inventory-setup-grid-locks';

function loadLocks(): Set<Field> {
  try {
    const saved = localStorage.getItem(LOCKS_KEY);
    if (saved) return new Set(JSON.parse(saved) as Field[]);
  } catch { /* private window or bad value: fall back to defaults */ }
  return new Set(DEFAULT_LOCKS);
}

const num = (value: unknown) => (value == null || value === '' ? '' : String(Number(value)));

function toCells(item: InventoryItem): Cells {
  return {
    category_id: item.category_id ? String(item.category_id) : '',
    name: item.name,
    count_mode: item.count_mode ?? 'number',
    current_quantity: num(item.current_quantity),
    unit: item.unit,
    pack_size: num(item.pack_size),
    pack_unit: item.pack_unit ?? '',
    min_threshold: num(item.min_threshold),
    cost_per_unit: num(item.cost_per_unit),
  };
}

/** Compare what a cell means, so "46" and "46.0" aren't a change. */
function norm(field: Field, value: string): string {
  const text = value.trim();
  if (NUMERIC.has(field) && text !== '') return String(parseQty(text) ?? text);
  return text;
}

const isDirty = (field: Field, original: Cells, cells: Cells) => norm(field, original[field]) !== norm(field, cells[field]);
const applies = (field: Field, cells: Cells) => cells.count_mode !== 'presence' || !NOT_FOR_PRESENCE.has(field);

function cellError(field: Field, cells: Cells): string | null {
  if (!applies(field, cells)) return null;
  const text = cells[field].trim();
  if (field === 'name' || field === 'unit') return text ? null : 'Required';
  if (field === 'pack_unit' && !text && cells.pack_size.trim()) return 'Needs a unit';
  if (field === 'pack_size' && !text && cells.pack_unit.trim()) return 'Needs a size';
  if (!NUMERIC.has(field)) return null;
  if (text === '') return field === 'current_quantity' || field === 'min_threshold' ? 'Required' : null;
  const value = parseQty(text);
  if (value === null || value < 0) return 'Not a number';
  if (field === 'pack_size' && value === 0) return 'Must be above 0';
  return null;
}

function toUpdate(id: number, original: Cells, row: RowState): BulkItemUpdate | null {
  const update: Record<string, unknown> = { id };
  let changed = false;
  for (const { field } of COLUMNS) {
    if (!isDirty(field, original, row.cells) || !applies(field, row.cells)) continue;
    changed = true;
    const text = row.cells[field].trim();
    if (field === 'category_id') update[field] = text ? Number(text) : null;
    else if (NUMERIC.has(field)) update[field] = text === '' ? null : parseQty(text);
    else if (field === 'pack_unit') update[field] = text || null;
    else update[field] = text;
  }
  if (row.retired) {
    update.is_active = false;
    changed = true;
  }
  return changed ? (update as unknown as BulkItemUpdate) : null;
}

/** A pasted value in the form the cell stores, or null if it can't be read. */
function coerce(field: Field, raw: string, categories: InventoryCategory[]): string | null {
  const text = raw.trim();
  if (field === 'category_id') {
    if (!text) return '';
    const match = categories.find(c => c.name.toLowerCase() === text.toLowerCase());
    return match ? String(match.id) : null;
  }
  if (field === 'count_mode') {
    const lower = text.toLowerCase();
    if (lower.includes('yes') || lower.includes('presence')) return 'presence';
    if (lower.startsWith('num') || lower.startsWith('count')) return 'number';
    return null;
  }
  return text;
}

export default function InventorySetupGrid({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient();
  const { data: itemsData, isLoading, refetch } = useInventoryItems({ is_active: true });
  const { data: categories = [] } = useInventoryCategories();

  // A snapshot, not live data: a background refetch must never wipe edits.
  const [base, setBase] = useState<InventoryItem[] | null>(null);
  const [rows, setRows] = useState<Map<number, RowState>>(new Map());
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [locked, setLocked] = useState<Set<Field>>(loadLocks);
  const [search, setSearch] = useState('');
  const [atZeroOnly, setAtZeroOnly] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [fullScreen, setFullScreen] = useState(false);

  const load = useCallback((items: InventoryItem[]) => {
    setBase(items);
    setRows(new Map(items.map(item => [item.id, { cells: toCells(item), retired: false }])));
    setSelected(new Set());
  }, []);

  useEffect(() => {
    if (!base && itemsData) load(itemsData.items);
  }, [base, itemsData, load]);

  useEffect(() => {
    try { localStorage.setItem(LOCKS_KEY, JSON.stringify([...locked])); } catch { /* not critical */ }
  }, [locked]);

  const originals = useMemo(() => new Map((base ?? []).map(item => [item.id, toCells(item)])), [base]);

  // Count order: categories in their order, then uncategorized.
  const ordered = useMemo(() => {
    if (!base) return [];
    const known = new Set(categories.map(c => c.id));
    return [
      ...categories.flatMap(c => base.filter(item => item.category_id === c.id)),
      ...base.filter(item => !item.category_id || !known.has(item.category_id)),
    ];
  }, [base, categories]);

  const visibleIds = useMemo(() => {
    const query = search.trim().toLowerCase();
    return ordered
      .filter(item => !query || item.name.toLowerCase().includes(query))
      .filter(item => !atZeroOnly || Number(item.current_quantity) === 0)
      .map(item => item.id);
  }, [ordered, search, atZeroOnly]);

  const summary = useMemo(() => {
    let cells = 0, items = 0, retired = 0, errors = 0;
    const updates: BulkItemUpdate[] = [];
    rows.forEach((row, id) => {
      const original = originals.get(id);
      if (!original) return;
      const changedCells = COLUMNS.filter(({ field }) => isDirty(field, original, row.cells)).length;
      cells += changedCells;
      if (changedCells) items++;
      if (row.retired) retired++;
      if (!row.retired) errors += COLUMNS.filter(({ field }) => cellError(field, row.cells)).length;
      const update = toUpdate(id, original, row);
      if (update) updates.push(update);
    });
    return { cells, items, retired, errors, updates };
  }, [rows, originals]);
  const dirty = summary.updates.length > 0;

  // Closing the tab with unsaved edits would lose an hour of setup.
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  useEffect(() => {
    if (!fullScreen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !(event.target as HTMLElement).dataset?.field) setFullScreen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [fullScreen]);

  const setCell = useCallback((id: number, field: Field, value: string) => {
    setRows(prev => {
      const row = prev.get(id);
      if (!row) return prev;
      const next = new Map(prev);
      next.set(id, { ...row, cells: { ...row.cells, [field]: value } });
      return next;
    });
  }, []);

  const setRetired = useCallback((ids: Iterable<number>, retired: boolean) => {
    setRows(prev => {
      const next = new Map(prev);
      for (const id of ids) {
        const row = next.get(id);
        if (row) next.set(id, { ...row, retired });
      }
      return next;
    });
  }, []);
  const toggleRetire = useCallback((id: number) => {
    setRows(prev => {
      const row = prev.get(id);
      if (!row) return prev;
      return new Map(prev).set(id, { ...row, retired: !row.retired });
    });
  }, []);

  const toggleSelect = useCallback((id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }, []);

  const setModeForSelected = (mode: string) => {
    setRows(prev => {
      const next = new Map(prev);
      selected.forEach(id => {
        const row = next.get(id);
        if (row) next.set(id, { ...row, cells: { ...row.cells, count_mode: mode } });
      });
      return next;
    });
    setNotice(`Set ${selected.size} item${selected.size === 1 ? '' : 's'} to ${MODE_LABEL[mode]}.`);
  };

  const toggleLock = (field: Field) =>
    setLocked(prev => {
      const next = new Set(prev);
      if (!next.delete(field)) next.add(field);
      return next;
    });

  const onPaste = (event: React.ClipboardEvent<HTMLTableElement>) => {
    const target = event.target as HTMLElement;
    const field = target.dataset.field as Field | undefined;
    if (!field) return;
    const text = event.clipboardData.getData('text/plain').replace(/\r?\n$/, '');
    if (!/[\t\n]/.test(text)) return; // one value: let the input paste it normally
    event.preventDefault();

    let lines = text.split(/\r?\n/).map(line => line.split('\t'));
    // A copy of this grid carries a header row; don't write it into an item.
    if (lines[0]?.[0]?.trim() === COLUMNS[0].label) lines = lines.slice(1);

    const startRow = Number(target.dataset.row);
    const startCol = COLUMNS.findIndex(c => c.field === field);
    let filled = 0, skippedLocked = 0, unreadable = 0, outside = 0;
    const next = new Map(rows);
    lines.forEach((values, r) => values.forEach((raw, c) => {
      const id = visibleIds[startRow + r];
      const column = COLUMNS[startCol + c];
      const row = id === undefined ? undefined : next.get(id);
      if (!row || !column) return void outside++;
      if (locked.has(column.field)) return void skippedLocked++;
      const value = coerce(column.field, raw, categories);
      if (value === null) return void unreadable++;
      next.set(id, { ...row, cells: { ...row.cells, [column.field]: value } });
      filled++;
    }));
    setRows(next);
    const skipped = [
      skippedLocked && `${skippedLocked} in locked columns`,
      unreadable && `${unreadable} unreadable (unknown category or kind)`,
      outside && `${outside} past the edge of the table`,
    ].filter(Boolean);
    setNotice(`Pasted ${filled} cell${filled === 1 ? '' : 's'}.${skipped.length ? ` Skipped ${skipped.join(', ')}.` : ''}`);
  };

  // Enter moves down a column, like a spreadsheet.
  const onKeyDown = (event: React.KeyboardEvent<HTMLTableElement>) => {
    const target = event.target as HTMLElement;
    if (event.key !== 'Enter' || !target.dataset.field) return;
    event.preventDefault();
    const nextRow = Number(target.dataset.row) + (event.shiftKey ? -1 : 1);
    document.querySelector<HTMLElement>(`[data-row="${nextRow}"][data-field="${target.dataset.field}"]`)?.focus();
  };

  const copyTable = async () => {
    const byId = new Map(categories.map(c => [String(c.id), c.name]));
    const lines = [COLUMNS.map(c => c.label).join('\t')];
    visibleIds.forEach(id => {
      const cells = rows.get(id)!.cells;
      lines.push(COLUMNS.map(({ field }) =>
        field === 'category_id' ? byId.get(cells[field]) ?? ''
          : field === 'count_mode' ? MODE_LABEL[cells[field]]
          : cells[field]).join('\t'));
    });
    try {
      await navigator.clipboard.writeText(lines.join('\n'));
      setNotice(`Copied ${visibleIds.length} rows. Paste into Google Sheets, edit, then copy back and paste into the first Category cell.`);
    } catch {
      setNotice("Couldn't reach the clipboard. Try again from a normal browser window.");
    }
  };

  const save = useMutation({
    mutationFn: () => inventoryApi.bulkUpdateItems(summary.updates),
    onSuccess: async result => {
      const fresh = await refetch();
      if (fresh.data) load(fresh.data.items);
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setNotice(`Saved ${result.updated} item${result.updated === 1 ? '' : 's'}.${result.adjusted ? ` Stock changed on ${result.adjusted}, logged as adjustments.` : ''}`);
    },
  });

  const revertAll = () => {
    if (base) load(base);
    setNotice('Reverted every change.');
  };

  if (isLoading || !base) {
    return <div className="py-12 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading items…</div>;
  }

  const allShownSelected = visibleIds.length > 0 && visibleIds.every(id => selected.has(id));

  const saveActions = (
    <>
      <button type="button" onClick={revertAll} disabled={!dirty || save.isPending} className="btn-secondary inline-flex items-center gap-2 whitespace-nowrap">
        <ArrowCounterClockwise size={18} aria-hidden /> Revert all
      </button>
      <button
        type="button"
        onClick={() => save.mutate()}
        disabled={!dirty || summary.errors > 0 || save.isPending}
        className="btn-primary"
      >
        {save.isPending ? 'Saving…' : 'Save'}
      </button>
    </>
  );

  const grid = (
    // Full screen covers the sidebar and page header and keeps only the table's own controls.
    <div
      role={fullScreen ? 'dialog' : undefined}
      aria-modal={fullScreen || undefined}
      aria-label={fullScreen ? 'Edit all items, full screen' : undefined}
      className={fullScreen ? 'fixed inset-0 z-50 flex flex-col gap-3 p-3 md:p-4 bg-neutral-background' : 'space-y-3'}
    >
      {!fullScreen && (
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-heading text-2xl! text-neutral-text-dark">Edit all items</h2>
            <p className="mt-1 text-sm text-neutral-text-muted max-w-prose">
              Nothing is saved until you press Save. Paste from Google Sheets into any cell to fill from there.
            </p>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={() => (dirty ? setConfirmLeave(true) : onDone())} className="btn-ghost">Done</button>
            {saveActions}
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <label className="relative flex-1 min-w-0">
          <span className="sr-only">Search items</span>
          <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" size={18} aria-hidden />
          <input type="search" placeholder="Search items" value={search} onChange={e => setSearch(e.target.value)} className="input-field pl-10 min-h-12" />
        </label>
        <button
          type="button"
          onClick={() => setAtZeroOnly(!atZeroOnly)}
          aria-pressed={atZeroOnly}
          className={`btn-secondary whitespace-nowrap ${atZeroOnly ? 'border-warning text-warning' : ''}`}
        >
          Only items at zero
        </button>
        <button type="button" onClick={copyTable} className="btn-secondary inline-flex items-center gap-2 whitespace-nowrap">
          <Copy size={18} aria-hidden /> Copy as table
        </button>
        <button
          type="button"
          onClick={() => setFullScreen(!fullScreen)}
          aria-pressed={fullScreen}
          className="btn-secondary inline-flex items-center gap-2 whitespace-nowrap"
        >
          {fullScreen ? <ArrowsIn size={18} aria-hidden /> : <ArrowsOut size={18} aria-hidden />}
          {fullScreen ? 'Exit full screen' : 'Full screen'}
        </button>
        {fullScreen && saveActions}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm min-h-10" aria-live="polite">
        <span className="tabular-nums text-neutral-text-body">
          {dirty
            ? `${summary.cells} cell${summary.cells === 1 ? '' : 's'} changed across ${summary.items} item${summary.items === 1 ? '' : 's'}${summary.retired ? ` · ${summary.retired} to retire` : ''}`
            : `${visibleIds.length} of ${base.length} items · no changes`}
        </span>
        {summary.errors > 0 && (
          <span className="font-medium text-error">{summary.errors} cell{summary.errors === 1 ? '' : 's'} need fixing before Save</span>
        )}
        {save.isError && <span role="alert" className="font-medium text-error">Not saved. {describeApiError(save.error)}</span>}
        {notice && <span className="text-neutral-text-muted">{notice}</span>}
      </div>

      {selected.size > 0 && (
        <div className="card flex flex-wrap items-center gap-3 px-3 py-2 text-sm">
          <strong className="text-neutral-text-dark tabular-nums">{selected.size} ticked</strong>
          <label className="inline-flex items-center gap-2">
            Set counted as
            <select value="" onChange={e => e.target.value && setModeForSelected(e.target.value)} className="input-field h-10 w-auto py-0">
              <option value="">Choose…</option>
              <option value="number">Number</option>
              <option value="presence">Yes / no</option>
            </select>
          </label>
          <button type="button" onClick={() => setRetired(selected, true)} className="btn-secondary h-10 py-0">Retire ticked</button>
          <button type="button" onClick={() => setRetired(selected, false)} className="btn-ghost h-10 py-0">Keep ticked</button>
          <button type="button" onClick={() => setSelected(new Set())} className="btn-ghost h-10 py-0">Clear ticks</button>
        </div>
      )}

      <datalist id="grid-units">{UNITS.map(unit => <option key={unit} value={unit} />)}</datalist>

      <div className={`card overflow-auto ${fullScreen ? 'flex-1 min-h-0' : 'max-h-[calc(100dvh-18rem)]'}`}>
        {/* Fixed layout: the frozen columns' left offsets only line up if widths are exact.
            On a wide screen the table fills it and Name, whose width is left open, takes the extra. */}
        <table className="table-fixed w-full border-separate border-spacing-0 text-sm" style={{ minWidth: TICK_WIDTH + COLUMNS.reduce((sum, c) => sum + c.width, 0) + RETIRE_WIDTH }} onPaste={onPaste} onKeyDown={onKeyDown}>
          <thead>
            <tr>
              <th style={{ width: TICK_WIDTH }} className="sticky top-0 left-0 z-30 bg-off-white border-b border-r border-neutral-border">
                <input
                  type="checkbox"
                  aria-label="Tick all shown"
                  checked={allShownSelected}
                  onChange={() => setSelected(allShownSelected ? new Set() : new Set(visibleIds))}
                  className="size-4"
                />
              </th>
              {COLUMNS.map(column => {
                const isLocked = locked.has(column.field);
                return (
                  <th
                    key={column.field}
                    style={{ width: column.field === 'name' ? undefined : column.width, left: column.left }}
                    className={`sticky top-0 ${column.left !== undefined ? 'z-30' : 'z-20'} bg-off-white border-b border-r border-neutral-border px-2 py-1 text-left font-medium text-neutral-text-body whitespace-nowrap`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleLock(column.field)}
                      aria-pressed={isLocked}
                      aria-label={`${column.label}: ${isLocked ? 'locked, press to unlock' : 'unlocked, press to lock'}`}
                      className={`inline-flex items-center gap-1.5 h-9 px-1 -mx-1 rounded hover:bg-cream/60 ${column.numeric ? 'w-full justify-end' : ''}`}
                    >
                      {column.label}
                      {isLocked ? <Lock size={14} weight="fill" className="text-coffee-brown" aria-hidden /> : <LockOpen size={14} className="text-neutral-text-light" aria-hidden />}
                    </button>
                  </th>
                );
              })}
              <th style={{ width: RETIRE_WIDTH }} className="sticky top-0 z-20 bg-off-white border-b border-neutral-border" aria-label="Retire" />
            </tr>
          </thead>
          <tbody>
            {visibleIds.map((id, index) => (
              <GridRow
                key={id}
                id={id}
                index={index}
                original={originals.get(id)!}
                row={rows.get(id)!}
                selected={selected.has(id)}
                locked={locked}
                categories={categories}
                onCell={setCell}
                onSelect={toggleSelect}
                onRetire={toggleRetire}
              />
            ))}
          </tbody>
        </table>
        {visibleIds.length === 0 && <p className="p-8 text-center text-neutral-text-muted">No items match.</p>}
      </div>

      <ConfirmDialog
        isOpen={confirmLeave}
        onClose={() => setConfirmLeave(false)}
        onConfirm={onDone}
        title="Leave without saving?"
        message={`${summary.updates.length} changed item${summary.updates.length === 1 ? '' : 's'} will be lost.`}
        confirmText="Discard changes"
        cancelText="Keep editing"
        variant="danger"
      />
    </div>
  );

  // A portal, because an ancestor of the page makes `fixed` relative to the content column.
  return fullScreen ? createPortal(grid, document.body) : grid;
}

const GridRow = memo(function GridRow({ id, index, original, row, selected, locked, categories, onCell, onSelect, onRetire }: {
  id: number;
  index: number;
  original: Cells;
  row: RowState;
  selected: boolean;
  locked: Set<Field>;
  categories: InventoryCategory[];
  onCell: (id: number, field: Field, value: string) => void;
  onSelect: (id: number) => void;
  onRetire: (id: number) => void;
}) {
  const { cells, retired } = row;
  const categoryName = (value: string) => categories.find(c => String(c.id) === value)?.name ?? '—';

  return (
    <tr className={retired ? 'text-neutral-text-light' : ''}>
      <td className="sticky left-0 z-10 bg-off-white border-b border-r border-neutral-border text-center">
        <input type="checkbox" aria-label={`Tick ${cells.name}`} checked={selected} onChange={() => onSelect(id)} className="size-4" />
      </td>
      {COLUMNS.map(column => {
        const { field } = column;
        const changed = isDirty(field, original, cells);
        const error = !retired && cellError(field, cells);
        const sticky = column.left !== undefined;
        // Opaque tints: frozen cells must hide what scrolls beneath them.
        const tint = retired ? 'bg-[color-mix(in_oklab,var(--color-neutral-border)_45%,var(--color-off-white))]' : changed ? 'bg-cream' : sticky ? 'bg-off-white' : '';
        const label = `${cells.name} ${column.label}`;
        const common = {
          'data-row': index,
          'data-field': field,
          'aria-label': label,
          'aria-invalid': error ? true : undefined,
          title: error || undefined,
          className: `w-full h-10 px-2 rounded bg-transparent outline-none focus:ring-2 focus:ring-coffee-brown ${error ? 'ring-2 ring-error' : ''} ${retired ? 'line-through' : ''} ${column.numeric ? 'text-right tabular-nums' : ''}`,
          onKeyDown: (event: React.KeyboardEvent) => event.key === 'Escape' && onCell(id, field, original[field]),
        };

        let content: React.ReactNode;
        if (!applies(field, cells)) {
          content = <span className="block px-2 text-neutral-text-light">—</span>;
        } else if (locked.has(field)) {
          const text = field === 'category_id' ? categoryName(cells[field])
            : field === 'count_mode' ? MODE_LABEL[cells[field]]
            : column.numeric && cells[field] !== '' ? formatQty(cells[field]) : cells[field];
          content = <span className={`block px-2 truncate ${retired ? 'line-through' : ''} ${column.numeric ? 'text-right tabular-nums' : ''}`}>{text}</span>;
        } else if (field === 'category_id') {
          content = (
            <select {...common} value={cells[field]} onChange={e => onCell(id, field, e.target.value)}>
              <option value="">None</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          );
        } else if (field === 'count_mode') {
          content = (
            <select {...common} value={cells[field]} onChange={e => onCell(id, field, e.target.value)}>
              <option value="number">Number</option>
              <option value="presence">Yes / no</option>
            </select>
          );
        } else {
          content = (
            <input
              {...common}
              type="text"
              inputMode={column.numeric ? 'decimal' : undefined}
              list={field === 'unit' || field === 'pack_unit' ? 'grid-units' : undefined}
              value={cells[field]}
              onChange={e => onCell(id, field, e.target.value)}
            />
          );
        }

        return (
          <td
            key={field}
            style={{ left: column.left }}
            className={`${sticky ? 'sticky z-10' : ''} ${tint} border-b border-r border-neutral-border px-0.5 py-0.5 transition-colors`}
          >
            {content}
          </td>
        );
      })}
      <td className="border-b border-neutral-border px-1 text-right">
        <button
          type="button"
          onClick={() => onRetire(id)}
          aria-pressed={retired}
          className={`h-9 px-3 rounded-lg font-medium ${retired ? 'text-coffee-brown hover:bg-cream/60' : 'text-neutral-text-light hover:text-error hover:bg-error/10'}`}
        >
          {retired ? 'Undo' : 'Retire'}
        </button>
      </td>
    </tr>
  );
});
