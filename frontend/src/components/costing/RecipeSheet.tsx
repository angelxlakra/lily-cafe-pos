/**
 * One dish's recipe and what it really costs to make. Owner only.
 *
 * The cost recalculates as the recipe is typed (POST /costing/preview). An
 * ingredient that can't be costed says why and what to do, and while any line
 * has a gap the cost reads "at least" and the margin "at most": never a
 * confident total built on ₹0 lines. See docs/INVENTORY_PLAN.md, step 5.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash, Warning, X } from '@phosphor-icons/react';
import LoadingSpinner from '../LoadingSpinner';
import { useDialogFocus } from '../../hooks/useDialogFocus';
import {
  costingKeys, useApplySuggestedPrice, useCostingDefaults, useCostingPreview, useMenuItemCosting, useSaveCosting,
} from '../../hooks/useCosting';
import { inventoryApi } from '../../api/inventory';
import { describeApiError } from '../../utils/apiError';
import { formatCurrency } from '../../utils/formatCurrency';
import { pickItems } from '../../utils/purchaseSheet';
import { toast } from '../../utils/toast';
import {
  COSTING_DRAFT_PREFIX, describeGap, describeSource, isStalePrice, parseQuantity, rupees, unitOptions,
} from '../../utils/costing';
import type { MenuItem } from '../../types';
import type { InventoryItem } from '../../types/inventory';
import type {
  CostBreakdown, DishCosting, DishCostingIn, IngredientLine, OverheadKind, OverheadMode, OverheadOverride,
} from '../../types/costing';

interface RecipeSheetProps {
  menuItem: MenuItem;
  /** From the dish list: false skips asking the server for a recipe that isn't there. */
  hasRecipe: boolean;
  onClose: () => void;
}

interface DraftLine {
  key: string;
  itemId: number;
  quantity: string;
  unit: string;
}

interface DraftOverhead {
  mode: OverheadMode;
  value: string;
}

interface Draft {
  yieldUnits: string;
  lines: DraftLine[];
  /** null = this dish uses the cafe-wide default. */
  overheads: Record<OverheadKind, DraftOverhead | null>;
  /** '' = the cafe-wide target. */
  targetMargin: string;
}

const KINDS: OverheadKind[] = ['labour', 'fixed', 'wastage', 'packaging'];
const KIND_LABEL: Record<OverheadKind, string> = {
  labour: 'Labour', fixed: 'Fixed costs', wastage: 'Wastage', packaging: 'Packaging',
};

const field =
  'h-11 rounded-lg border border-neutral-border bg-off-white px-3 text-base text-neutral-text-dark tabular-nums placeholder:text-neutral-text-muted focus:outline-none focus:border-lily-ink focus:bg-white dark:focus:bg-neutral-background';

let keySeed = 0;
const newKey = () => `line-${++keySeed}`;

const draftStorageKey = (menuItemId: number) => `${COSTING_DRAFT_PREFIX}${menuItemId}`;

function readStoredDraft(menuItemId: number): Draft | null {
  try {
    const raw = localStorage.getItem(draftStorageKey(menuItemId));
    return raw ? (JSON.parse(raw) as Draft) : null;
  } catch {
    return null;
  }
}

function writeStoredDraft(menuItemId: number, draft: Draft | null) {
  try {
    if (draft) localStorage.setItem(draftStorageKey(menuItemId), JSON.stringify(draft));
    else localStorage.removeItem(draftStorageKey(menuItemId));
  } catch {
    // Storage off (private window): the recipe still works, it just isn't kept on close.
  }
}

function overheadFromSaved(saved: OverheadOverride): DraftOverhead | null {
  return saved.mode && saved.value != null ? { mode: saved.mode, value: String(Number(saved.value)) } : null;
}

function draftFromSaved(saved: DishCosting | null): Draft {
  return {
    yieldUnits: saved ? String(Number(saved.yield_units)) : '1',
    lines: (saved?.ingredients ?? []).map(line => ({
      key: newKey(), itemId: line.inventory_item_id, quantity: String(Number(line.quantity)), unit: line.unit,
    })),
    overheads: {
      labour: saved ? overheadFromSaved(saved.labour) : null,
      fixed: saved ? overheadFromSaved(saved.fixed) : null,
      wastage: saved ? overheadFromSaved(saved.wastage) : null,
      packaging: saved ? overheadFromSaved(saved.packaging) : null,
    },
    targetMargin: saved?.target_margin_percent != null ? String(Number(saved.target_margin_percent)) : '',
  };
}

/** The request a draft makes: only lines with a real quantity, so half-typed rows don't cost as errors. */
function toRequest(draft: Draft, menuItemId: number): DishCostingIn {
  const override = (o: DraftOverhead | null): OverheadOverride => {
    const value = o ? Number(o.value) : NaN;
    return o && o.value.trim() !== '' && value >= 0 ? { mode: o.mode, value } : { mode: null, value: null };
  };
  const target = draft.targetMargin.trim() === '' ? null : Number(draft.targetMargin);
  return {
    menu_item_id: menuItemId,
    yield_units: parseQuantity(draft.yieldUnits) ?? 1,
    target_margin_percent: target != null && target >= 0 && target < 100 ? target : null,
    ingredients: draft.lines.flatMap(line => {
      const quantity = parseQuantity(line.quantity);
      return quantity ? [{ inventory_item_id: line.itemId, quantity, unit: line.unit }] : [];
    }),
    labour: override(draft.overheads.labour),
    fixed: override(draft.overheads.fixed),
    wastage: override(draft.overheads.wastage),
    packaging: override(draft.overheads.packaging),
  };
}

/** The value after `delay` ms without a change, so typing "250" costs once, not three times. */
function useSettled<T>(value: T, delay: number): T {
  const [settled, setSettled] = useState(value);
  const serialized = JSON.stringify(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setSettled(value), delay);
    return () => window.clearTimeout(timer);
  }, [serialized, delay]); // eslint-disable-line react-hooks/exhaustive-deps
  return settled;
}

export default function RecipeSheet({ menuItem, hasRecipe, onClose }: RecipeSheetProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocus(dialogRef, onClose);

  const costing = useMenuItemCosting(menuItem.id, hasRecipe);
  const saved = costing.data !== undefined ? costing.data : hasRecipe ? undefined : null;
  const savedLoading = saved === undefined && costing.isLoading;
  const savedError = costing.error;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50 animate-fade-in" onClick={onClose} aria-hidden />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="recipe-sheet-title"
        className="relative flex h-full w-full flex-col bg-neutral-background shadow-strong md:max-w-2xl"
      >
        <header className="flex items-start gap-3 border-b border-neutral-border bg-off-white px-4 py-4 sm:px-6">
          <div className="min-w-0 flex-1">
            <h2 id="recipe-sheet-title" className="font-heading text-2xl! text-neutral-text-dark text-balance">
              {menuItem.name}
            </h2>
            <p className="text-sm text-neutral-text-muted">Menu price {formatCurrency(menuItem.price)} · recipe and cost</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-neutral-text-body hover:bg-cream"
            aria-label="Close recipe"
          >
            <X size={22} aria-hidden />
          </button>
        </header>

        {savedLoading && (
          <div className="flex flex-1 items-center justify-center"><LoadingSpinner /></div>
        )}
        {savedError && (
          <p role="alert" className="m-6 text-sm font-medium text-error">{describeApiError(savedError)}</p>
        )}
        {!savedLoading && !savedError && saved !== undefined && (
          <RecipeEditor menuItem={menuItem} saved={saved} onClose={onClose} />
        )}
      </div>
    </div>
  );
}

function RecipeEditor({ menuItem, saved, onClose }: { menuItem: MenuItem; saved: DishCosting | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const savedDraft = useMemo(() => draftFromSaved(saved), [saved]);
  const [restored, setRestored] = useState(() => readStoredDraft(menuItem.id) !== null);
  const [draft, setDraft] = useState<Draft>(() => readStoredDraft(menuItem.id) ?? savedDraft);
  const [showOverheads, setShowOverheads] = useState(false);
  const [confirmingPrice, setConfirmingPrice] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const quantityRefs = useRef(new Map<string, HTMLInputElement>());
  const [focusKey, setFocusKey] = useState<string | null>(null);

  const { data: itemsResponse } = useQuery({
    queryKey: ['inventory', 'items', { is_active: true }],
    queryFn: () => inventoryApi.getItems({ is_active: true }),
  });
  const { data: frequent = [] } = useQuery({
    queryKey: ['inventory', 'purchases', 'frequent'],
    queryFn: inventoryApi.getFrequentPurchases,
  });
  const { data: defaults } = useCostingDefaults();
  const items = useMemo(() => itemsResponse?.items ?? [], [itemsResponse]);
  const itemsById = useMemo(() => new Map(items.map(item => [item.id, item])), [items]);

  const request = useMemo(() => toRequest(draft, menuItem.id), [draft, menuItem.id]);
  const savedRequest = useMemo(() => toRequest(savedDraft, menuItem.id), [savedDraft, menuItem.id]);
  const dirty = JSON.stringify(request) !== JSON.stringify(savedRequest);
  const settledRequest = useSettled(request, 350);
  const preview = useCostingPreview(settledRequest);
  const breakdown: CostBreakdown | undefined = preview.data ?? saved?.breakdown;
  const linesById = useMemo(
    () => new Map((breakdown?.ingredients ?? []).map(line => [line.inventory_item_id, line])),
    [breakdown],
  );

  const save = useSaveCosting();
  const applyPrice = useApplySuggestedPrice();

  // Keep unsaved work on this device, so closing the panel by accident loses nothing.
  useEffect(() => {
    writeStoredDraft(menuItem.id, dirty ? draft : null);
  }, [draft, dirty, menuItem.id]);

  useEffect(() => {
    if (focusKey) {
      quantityRefs.current.get(focusKey)?.focus();
      setFocusKey(null);
    }
  }, [focusKey]);

  const updateLine = (key: string, patch: Partial<DraftLine>) =>
    setDraft(d => ({ ...d, lines: d.lines.map(line => (line.key === key ? { ...line, ...patch } : line)) }));
  const removeLine = (key: string) => setDraft(d => ({ ...d, lines: d.lines.filter(line => line.key !== key) }));
  const addItem = (item: InventoryItem) => {
    const key = newKey();
    setDraft(d => ({ ...d, lines: [...d.lines, { key, itemId: item.id, quantity: '', unit: unitOptions(item)[0] }] }));
    setFocusKey(key);
  };

  const discardRestored = () => {
    writeStoredDraft(menuItem.id, null);
    setDraft(savedDraft);
    setRestored(false);
  };

  const handleSave = async () => {
    setSaveError(null);
    try {
      await save.mutateAsync({ id: saved?.id ?? null, data: request });
      writeStoredDraft(menuItem.id, null);
      setRestored(false);
      toast.success(saved ? 'Recipe saved' : 'Recipe added');
    } catch (error) {
      setSaveError(describeApiError(error));
    }
  };

  const handleApplyPrice = async () => {
    if (!saved || breakdown?.suggested_price == null) return;
    try {
      await applyPrice.mutateAsync({ costingId: saved.id, price: Number(breakdown.suggested_price) });
      setConfirmingPrice(false);
      toast.success('Menu price changed');
    } catch (error) {
      toast.error('Menu price not changed', { description: describeApiError(error) });
    }
  };

  const savePackSize = async (item: InventoryItem | undefined, line: IngredientLine, size: number) => {
    if (!item) return;
    try {
      await inventoryApi.updateItem(item.id, { pack_size: size, pack_unit: line.unit });
      await queryClient.invalidateQueries({ queryKey: ['inventory', 'items'] });
      await queryClient.invalidateQueries({ queryKey: costingKeys.all });
      toast.success(`Saved: 1 ${item.unit} = ${size} ${line.unit}`);
    } catch (error) {
      toast.error('Pack size not saved', { description: describeApiError(error) });
    }
  };

  const gaps = (breakdown?.ingredients ?? []).filter(line => line.reason);
  const usedIds = new Set(draft.lines.map(line => line.itemId));
  const pending = draft.lines.length - request.ingredients.length;
  const menuPrice = menuItem.price / 100;

  return (
    <>
      <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
        <div className="mx-auto flex max-w-xl flex-col gap-6">
          {restored && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-neutral-border bg-cream/60 px-4 py-3 text-sm text-neutral-text-body">
              <span>Restored your unsaved changes from this device.</span>
              <button type="button" onClick={discardRestored} className="font-semibold text-coffee-brown underline underline-offset-2">
                Discard them
              </button>
            </div>
          )}

          <label className="flex items-center gap-3 text-neutral-text-body">
            <span>Makes</span>
            <input
              id="recipe-yield"
              inputMode="decimal"
              value={draft.yieldUnits}
              onChange={event => setDraft(d => ({ ...d, yieldUnits: event.target.value }))}
              className={`${field} w-20 text-center`}
              aria-describedby="recipe-yield-hint"
            />
            <span>{parseQuantity(draft.yieldUnits) === 1 ? 'portion' : 'portions'}</span>
          </label>
          <p id="recipe-yield-hint" className="-mt-4 text-sm text-neutral-text-muted">
            For a batch, enter the whole batch and how many plates it makes.
          </p>

          <section aria-labelledby="recipe-ingredients" className="flex flex-col gap-3">
            <h3 id="recipe-ingredients" className="font-sans! text-sm! font-semibold uppercase tracking-wide! text-neutral-text-muted">
              Ingredients
            </h3>
            {draft.lines.length === 0 && (
              <p className="rounded-lg border border-dashed border-neutral-border px-4 py-6 text-center text-neutral-text-muted">
                No ingredients yet. Add the first one below.
              </p>
            )}
            <ul className="flex flex-col gap-2">
              {draft.lines.map(line => (
                <RecipeLine
                  key={line.key}
                  line={line}
                  item={itemsById.get(line.itemId)}
                  costed={linesById.get(line.itemId)}
                  quantityRef={el => { if (el) quantityRefs.current.set(line.key, el); else quantityRefs.current.delete(line.key); }}
                  onChange={patch => updateLine(line.key, patch)}
                  onRemove={() => removeLine(line.key)}
                  onSavePackSize={savePackSize}
                />
              ))}
            </ul>
            <IngredientPicker items={items.filter(item => !usedIds.has(item.id))} frequent={frequent} onPick={addItem} />
          </section>

          {breakdown && (
            <Readout
              breakdown={breakdown}
              gapCount={gaps.length}
              pending={pending}
              menuPrice={menuPrice}
              updating={preview.isFetching}
            />
          )}

          <section aria-labelledby="recipe-overheads" className="flex flex-col gap-3">
            <button
              type="button"
              id="recipe-overheads"
              onClick={() => setShowOverheads(open => !open)}
              aria-expanded={showOverheads}
              className="self-start text-sm font-semibold text-coffee-brown underline underline-offset-2"
            >
              {showOverheads ? 'Hide overheads and target' : 'Change overheads or target for this dish'}
            </button>
            {showOverheads && (
              <OverheadEditor
                draft={draft}
                defaults={defaults}
                onChange={(kind, value) => setDraft(d => ({ ...d, overheads: { ...d.overheads, [kind]: value } }))}
                onTargetChange={value => setDraft(d => ({ ...d, targetMargin: value }))}
              />
            )}
          </section>

          {breakdown && (
            <SuggestedPrice
              breakdown={breakdown}
              menuPrice={menuPrice}
              canApply={Boolean(saved) && !dirty}
              confirming={confirmingPrice}
              applying={applyPrice.isPending}
              onAsk={() => setConfirmingPrice(true)}
              onCancel={() => setConfirmingPrice(false)}
              onApply={handleApplyPrice}
            />
          )}
        </div>
      </div>

      <footer className="border-t border-neutral-border bg-off-white px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-xl flex-wrap items-center justify-end gap-3">
          {saveError && <p role="alert" className="mr-auto text-sm font-medium text-error">{saveError}</p>}
          {!saveError && dirty && (
            <p className="mr-auto text-sm text-neutral-text-muted">Unsaved changes are kept on this device.</p>
          )}
          <button type="button" onClick={onClose} className="btn-secondary">Close</button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || save.isPending || request.ingredients.length === 0}
            className="btn-primary"
          >
            {save.isPending ? 'Saving…' : saved ? 'Save recipe' : 'Add recipe'}
          </button>
        </div>
      </footer>
    </>
  );
}

interface RecipeLineProps {
  line: DraftLine;
  item: InventoryItem | undefined;
  costed: IngredientLine | undefined;
  quantityRef: (el: HTMLInputElement | null) => void;
  onChange: (patch: Partial<DraftLine>) => void;
  onRemove: () => void;
  onSavePackSize: (item: InventoryItem | undefined, line: IngredientLine, size: number) => Promise<void>;
}

function RecipeLine({ line, item, costed, quantityRef, onChange, onRemove, onSavePackSize }: RecipeLineProps) {
  const name = item?.name ?? costed?.name ?? 'Retired item';
  const options = item ? unitOptions(item) : [];
  if (!options.includes(line.unit)) options.push(line.unit);
  const gap = costed?.reason ? describeGap(costed.reason, costed) : null;
  const source = costed ? describeSource(costed) : null;
  const stale = costed ? isStalePrice(costed) : false;
  const quantityId = `qty-${line.key}`;

  return (
    <li className={`rounded-lg border px-3 py-3 ${gap ? 'border-warning/50 bg-warning/5' : 'border-neutral-border bg-off-white'}`}>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-x-3 gap-y-2">
        <div className="min-w-0">
          <label htmlFor={quantityId} className="font-medium text-neutral-text-dark">{name}</label>
          <p className="text-sm text-neutral-text-muted">
            {costed?.is_presence
              ? 'Yes/no item · covered by overheads'
              : costed && !costed.reason
                ? <>{rupees(costed.unit_price)} / {costed.stock_unit}{source && <> · <span className={stale ? 'font-medium text-warning' : undefined}>{source}{stale && ', over a month ago'}</span></>}</>
                : item
                  ? `counted in ${item.unit}`
                  : null}
          </p>
        </div>
        <p className="text-right font-semibold tabular-nums text-neutral-text-dark">
          {!costed ? '' : costed.is_presence ? '—' : costed.reason ? <span className="text-sm font-medium text-warning">not costed</span> : rupees(costed.line_cost)}
        </p>
        <div className="col-span-2 flex flex-wrap items-center gap-2">
          <input
            id={quantityId}
            ref={quantityRef}
            inputMode="decimal"
            value={line.quantity}
            onChange={event => onChange({ quantity: event.target.value })}
            placeholder="Qty"
            className={`${field} w-24 text-right`}
          />
          <select
            value={line.unit}
            onChange={event => onChange({ unit: event.target.value })}
            className={`${field} w-28`}
            aria-label={`Unit for ${name}`}
          >
            {options.map(unit => <option key={unit} value={unit}>{unit}</option>)}
          </select>
          <button
            type="button"
            onClick={onRemove}
            className="ml-auto flex h-11 w-11 items-center justify-center rounded-lg text-neutral-text-muted hover:bg-error/10 hover:text-error"
            aria-label={`Remove ${name}`}
          >
            <Trash size={20} aria-hidden />
          </button>
        </div>
      </div>
      {gap && costed && (
        <div className="mt-2 flex flex-col gap-2 text-sm">
          <p className="flex items-start gap-1.5 font-semibold text-warning">
            <Warning size={16} className="mt-0.5 shrink-0" aria-hidden />
            <span>{gap.title}. <span className="font-normal text-neutral-text-body">{gap.fix}</span></span>
          </p>
          {costed.reason === 'needs_pack_size' && (
            <PackSizeAsk item={item} line={costed} onSave={size => onSavePackSize(item, costed, size)} />
          )}
        </div>
      )}
    </li>
  );
}

function PackSizeAsk({ item, line, onSave }: { item: InventoryItem | undefined; line: IngredientLine; onSave: (size: number) => Promise<void> }) {
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const size = parseQuantity(value);
  const current = item?.pack_size && item.pack_unit ? `Now 1 ${item.unit} = ${Number(item.pack_size)} ${item.pack_unit}, which can't reach ${line.unit}.` : null;
  const inputId = `pack-${line.inventory_item_id}`;

  return (
    <form
      className="flex flex-wrap items-center gap-2"
      onSubmit={async event => {
        event.preventDefault();
        if (!size) return;
        setSaving(true);
        await onSave(size);
        setSaving(false);
      }}
    >
      <label htmlFor={inputId} className="text-neutral-text-dark">1 {line.stock_unit} =</label>
      <input
        id={inputId}
        inputMode="decimal"
        value={value}
        onChange={event => setValue(event.target.value)}
        className={`${field} h-10 w-24 text-right`}
      />
      <span className="text-neutral-text-dark">{line.unit}</span>
      <button type="submit" disabled={!size || saving || !item} className="btn-primary min-h-10! py-1!">
        {saving ? 'Saving…' : 'Save'}
      </button>
      {current && <p className="w-full text-neutral-text-muted">{current}</p>}
    </form>
  );
}

function IngredientPicker({ items, frequent, onPick }: { items: InventoryItem[]; frequent: number[]; onPick: (item: InventoryItem) => void }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const options = pickItems(items, query, frequent, 8);
  const pick = (item: InventoryItem) => {
    onPick(item);
    setQuery('');
    setOpen(false);
    setActive(0);
  };

  return (
    <div className="relative">
      <label htmlFor="recipe-add" className="sr-only">Add an ingredient</label>
      <div className="relative">
        <Plus size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" aria-hidden />
        <input
          id="recipe-add"
          role="combobox"
          aria-expanded={open && options.length > 0}
          aria-controls="recipe-add-options"
          aria-activedescendant={open && options[active] ? `recipe-add-${options[active].id}` : undefined}
          autoComplete="off"
          value={query}
          placeholder="Add an ingredient"
          onFocus={() => setOpen(true)}
          onBlur={() => window.setTimeout(() => setOpen(false), 120)}
          onChange={event => { setQuery(event.target.value); setOpen(true); setActive(0); }}
          onKeyDown={event => {
            if (event.key === 'ArrowDown') { event.preventDefault(); setActive(i => Math.min(i + 1, options.length - 1)); }
            else if (event.key === 'ArrowUp') { event.preventDefault(); setActive(i => Math.max(i - 1, 0)); }
            else if (event.key === 'Enter' && options[active]) { event.preventDefault(); pick(options[active]); }
            else if (event.key === 'Escape' && open) { event.stopPropagation(); setOpen(false); }
          }}
          className={`${field} w-full pl-9`}
        />
      </div>
      {open && options.length > 0 && (
        <ul
          id="recipe-add-options"
          role="listbox"
          className="absolute z-10 mt-1 max-h-72 w-full overflow-y-auto rounded-lg border border-neutral-border bg-off-white shadow-strong"
        >
          {options.map((item, index) => (
            <li
              key={item.id}
              id={`recipe-add-${item.id}`}
              role="option"
              aria-selected={index === active}
              onMouseDown={event => { event.preventDefault(); pick(item); }}
              onMouseEnter={() => setActive(index)}
              className={`flex cursor-pointer justify-between gap-3 px-3 py-2.5 ${index === active ? 'bg-cream' : ''}`}
            >
              <span className="text-neutral-text-dark">{item.name}</span>
              <span className="text-sm text-neutral-text-muted">{item.unit}</span>
            </li>
          ))}
        </ul>
      )}
      {open && query.trim() !== '' && options.length === 0 && (
        <p className="mt-1 text-sm text-neutral-text-muted">
          No inventory item called "{query.trim()}". Add it from the purchase sheet or Inventory → Items first.
        </p>
      )}
    </div>
  );
}

function Readout({ breakdown, gapCount, pending, menuPrice, updating }: {
  breakdown: CostBreakdown; gapCount: number; pending: number; menuPrice: number; updating: boolean;
}) {
  const hasGaps = gapCount > 0;
  const portions = Number(breakdown.yield_units);
  // With nothing costed yet, "at most 100%" says nothing: show no margin until something is.
  const nothingCosted = Number(breakdown.cost_per_unit) <= 0;
  const margin = breakdown.margin_percent == null || nothingCosted ? null : Math.round(Number(breakdown.margin_percent));
  const target = breakdown.target_margin_percent == null ? null : Math.round(Number(breakdown.target_margin_percent));
  const food = breakdown.food_cost_percent == null || nothingCosted ? null : Math.round(Number(breakdown.food_cost_percent));
  const overheads = breakdown.overheads
    .filter(o => Number(o.amount) > 0)
    .map(o => `${KIND_LABEL[o.kind].toLowerCase()} ${o.mode === 'percent' ? `${Number(o.value)}%` : rupees(o.value)}`)
    .join(' · ');
  const row = 'flex items-baseline justify-between gap-4';
  const below = !hasGaps && margin != null && target != null && margin < target;

  return (
    <section
      aria-labelledby="recipe-cost"
      aria-busy={updating}
      className={`flex flex-col gap-2 rounded-xl border border-neutral-border bg-off-white px-4 py-4 tabular-nums transition-opacity ${updating ? 'opacity-70' : ''}`}
    >
      <h3 id="recipe-cost" className="font-sans! text-sm! font-semibold uppercase tracking-wide! text-neutral-text-muted">
        Cost{portions !== 1 && ` (whole batch of ${portions})`}
      </h3>
      <div className={row}>
        <span>Ingredients</span>
        <span>{rupees(breakdown.raw_material_cost)}{hasGaps && ` + ${gapCount} not costed`}</span>
      </div>
      <div className={row}>
        <span className="min-w-0">Overheads{overheads && <span className="text-sm text-neutral-text-muted"> · {overheads}</span>}</span>
        <span>{rupees(breakdown.overhead_cost)}</span>
      </div>
      <div className={`${row} border-t border-neutral-border pt-2 text-lg font-semibold text-neutral-text-dark`}>
        <span>Cost per portion</span>
        <span>{hasGaps && 'at least '}{rupees(breakdown.cost_per_unit)}</span>
      </div>
      <div className={row}>
        <span>Menu price</span>
        <span>{rupees(menuPrice)}</span>
      </div>
      {margin != null && (
        <div className={`${row} text-lg font-semibold ${below ? 'text-error' : 'text-neutral-text-dark'}`}>
          <span>Margin</span>
          <span>{hasGaps && 'at most '}{margin}%{target != null && <span className="text-sm font-normal text-neutral-text-muted"> · target {target}%</span>}</span>
        </div>
      )}
      {food != null && (
        <div className={`${row} text-sm text-neutral-text-muted`}>
          <span>Food cost</span>
          <span>{hasGaps && 'at least '}{food}% of the price</span>
        </div>
      )}
      {hasGaps && (
        <p className="mt-1 text-sm font-medium text-warning">
          {gapCount === 1 ? '1 ingredient isn’t' : `${gapCount} ingredients aren’t`} costed, so the real cost is higher than this.
        </p>
      )}
      {pending > 0 && (
        <p className="text-sm text-neutral-text-muted">
          {pending === 1 ? '1 ingredient has' : `${pending} ingredients have`} no quantity yet and {pending === 1 ? 'isn’t' : 'aren’t'} counted.
        </p>
      )}
    </section>
  );
}

function OverheadEditor({ draft, defaults, onChange, onTargetChange }: {
  draft: Draft;
  defaults: ReturnType<typeof useCostingDefaults>['data'];
  onChange: (kind: OverheadKind, value: DraftOverhead | null) => void;
  onTargetChange: (value: string) => void;
}) {
  const describeDefault = (o: OverheadOverride | undefined) =>
    !o || o.value == null ? '' : o.mode === 'percent' ? `${Number(o.value)}% of ingredients` : rupees(o.value);

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-neutral-border px-4 py-4">
      <p className="text-sm text-neutral-text-muted">
        Leave a row on the cafe default unless this dish really differs. Defaults are set in Settings.
      </p>
      {KINDS.map(kind => {
        const own = draft.overheads[kind];
        return (
          <div key={kind} className="flex flex-wrap items-center gap-2">
            <span className="w-28 font-medium text-neutral-text-dark">{KIND_LABEL[kind]}</span>
            {own ? (
              <>
                <input
                  id={`overhead-${kind}`}
                  inputMode="decimal"
                  value={own.value}
                  onChange={event => onChange(kind, { ...own, value: event.target.value })}
                  className={`${field} h-10 w-24 text-right`}
                  aria-label={`${KIND_LABEL[kind]} for this dish`}
                />
                <select
                  value={own.mode}
                  onChange={event => onChange(kind, { ...own, mode: event.target.value as OverheadMode })}
                  className={`${field} h-10 w-40`}
                  aria-label={`${KIND_LABEL[kind]}: percent or rupees`}
                >
                  <option value="percent">% of ingredients</option>
                  <option value="amount">₹ per batch</option>
                </select>
                <button type="button" onClick={() => onChange(kind, null)} className="text-sm text-coffee-brown underline underline-offset-2">
                  Use default
                </button>
              </>
            ) : (
              <>
                <span className="text-neutral-text-body">Default · {describeDefault(defaults?.[kind]) || '…'}</span>
                <button
                  type="button"
                  onClick={() => onChange(kind, {
                    mode: defaults?.[kind]?.mode ?? 'percent',
                    value: defaults?.[kind]?.value != null ? String(Number(defaults[kind].value)) : '0',
                  })}
                  className="text-sm text-coffee-brown underline underline-offset-2"
                >
                  Change for this dish
                </button>
              </>
            )}
          </div>
        );
      })}
      <label className="flex flex-wrap items-center gap-2">
        <span className="w-28 font-medium text-neutral-text-dark">Target margin</span>
        <input
          id="recipe-target"
          inputMode="decimal"
          value={draft.targetMargin}
          onChange={event => onTargetChange(event.target.value)}
          placeholder={defaults ? String(Number(defaults.target_margin_percent)) : ''}
          className={`${field} h-10 w-24 text-right`}
        />
        <span className="text-neutral-text-body">% {draft.targetMargin.trim() === '' && '(cafe default)'}</span>
      </label>
    </div>
  );
}

function SuggestedPrice({ breakdown, menuPrice, canApply, confirming, applying, onAsk, onCancel, onApply }: {
  breakdown: CostBreakdown; menuPrice: number; canApply: boolean; confirming: boolean; applying: boolean;
  onAsk: () => void; onCancel: () => void; onApply: () => void;
}) {
  const confirmRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (confirming) confirmRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [confirming]);
  if (!breakdown.is_complete || breakdown.suggested_price == null) {
    return (
      <p className="text-sm text-neutral-text-muted">
        A suggested price appears once every ingredient is costed.
      </p>
    );
  }
  const suggested = Number(breakdown.suggested_price);
  const target = Math.round(Number(breakdown.target_margin_percent));
  if (suggested <= menuPrice) {
    return <p className="text-sm text-neutral-text-muted">The menu price already meets the {target}% target.</p>;
  }

  return (
    <section aria-labelledby="recipe-suggested" className="flex flex-col gap-3 rounded-xl border border-neutral-border bg-cream/40 px-4 py-4">
      <p id="recipe-suggested" className="text-neutral-text-dark">
        For a {target}% margin, price it at <strong className="tabular-nums">{rupees(suggested)}</strong>
        <span className="text-neutral-text-muted"> (now {rupees(menuPrice)})</span>
      </p>
      {!canApply ? (
        <p className="text-sm text-neutral-text-muted">Save the recipe to use this price.</p>
      ) : confirming ? (
        <div ref={confirmRef} className="flex flex-wrap items-center gap-2">
          <p className="w-full text-neutral-text-body">
            Change the menu price from {rupees(menuPrice)} to {rupees(suggested)}? New orders use it straight away.
          </p>
          <button type="button" onClick={onApply} disabled={applying} className="btn-primary">
            {applying ? 'Changing…' : `Change to ${rupees(suggested)}`}
          </button>
          <button type="button" onClick={onCancel} className="btn-secondary">Keep {rupees(menuPrice)}</button>
        </div>
      ) : (
        <button type="button" onClick={onAsk} className="btn-secondary self-start">Use {rupees(suggested)} as the menu price</button>
      )}
    </section>
  );
}
