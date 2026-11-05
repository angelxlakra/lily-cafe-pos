import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { inventoryKeys, useInventoryItems, useUpdateItem } from '../hooks/useInventory';
import { inventoryApi } from '../api/inventory';
import { useUpdateMenuItem } from '../hooks/useMenu';
import { costingKeys } from '../hooks/useCosting';
import { toast } from '../utils/toast';
import { describeApiError } from '../utils/apiError';
import { baseUnitOf, describeSource, isMeasure, parseQuantity, percent, perUnitCost, rupees, sameFamily, unitOptions } from '../utils/costing';
import type { CostBreakdown, DishCostingIn, IngredientLine, OverheadKind, OverheadMode, OverheadOverride } from '../types/costing';
import type { InventoryItem } from '../types/inventory';
import {
  useCostingDefaults, useDeleteRecipe, useDishRecipe, useMadeRecipe, useOverview, useRecipePreview, useSaveRecipe, useSetBrand, useSetPackPrice,
} from './api';
import OpsConfirm from './OpsConfirm';
import PriceHistory from './PriceHistory';
import type { OverviewRow, Recipe } from './api';
import { formatPackPrice, parsePackPrice, usesPackForm } from './packPrice';

const OVERHEADS: { kind: OverheadKind; label: string }[] = [
  { kind: 'packaging', label: 'Packaging' },
  { kind: 'labour', label: 'Labour' },
  { kind: 'fixed', label: 'Fixed cost' },
  { kind: 'wastage', label: 'Wastage' },
];

interface Line { key: string; itemId: number; quantity: string; unit: string }
interface OverheadDraft { mode: OverheadMode; value: string }
const MODE_LABEL: Record<OverheadMode, string> = { percent: 'percent of raw material', amount: 'rupees for the batch', each: 'rupees per portion' };

let keyCounter = 0;
const newKey = () => `l${++keyCounter}`;

const isPresence = (item?: InventoryItem) => item?.count_mode === 'presence';

/** A non-negative number as typed (0 is fine for an overhead), or null. */
function parseAmount(text: string): number | null {
  const cleaned = text.trim().replace(/,/g, '.');
  return /^\d*\.?\d+$/.test(cleaned) ? Number(cleaned) : null;
}

/** The item's price the way the owners write it: "₹99 / 10 g", or "₹40 / kg". */
function priceText(item: InventoryItem | undefined, line: IngredientLine | undefined): string | null {
  if (line?.price_source === 'recipe') return line.price_missing ? null : formatPackPrice(Number(line.unit_price), 1, line.stock_unit);
  if (!item || item.current_price == null) return null;
  return usesPackForm(item) && item.pack_unit
    ? formatPackPrice(Number(item.current_price), Number(item.pack_size), item.pack_unit)
    : formatPackPrice(Number(item.current_price), 1, item.unit);
}

export default function RecipePage({ kind }: { kind: 'dish' | 'made' }) {
  const params = useParams();
  const subjectId = Number(kind === 'dish' ? params.menuItemId : params.itemId);
  const dish = useDishRecipe(subjectId, kind === 'dish');
  const made = useMadeRecipe(subjectId, kind === 'made');
  const recipeQuery = kind === 'dish' ? dish : made;
  const overview = useOverview();
  // is_active=false means "don't filter": a saved recipe can still hold a retired item.
  const items = useInventoryItems({ is_active: false });
  const defaults = useCostingDefaults();

  if (!Number.isFinite(subjectId)) return <p>That recipe doesn't exist.</p>;
  if (recipeQuery.isError || overview.isError || items.isError) return <p className="err">{describeApiError(recipeQuery.error ?? overview.error ?? items.error)}</p>;
  if (recipeQuery.isLoading || !overview.data || !items.data || !defaults.data) return <p className="muted">Loading the recipe…</p>;

  const row = overview.data.rows.find(r => (kind === 'dish' ? r.menu_item_id : r.inventory_item_id) === subjectId && r.kind === kind);
  const item = kind === 'made' ? items.data.items.find(i => i.id === subjectId) : undefined;
  const name = recipeQuery.data?.name || row?.name || item?.name;
  if (!name) return <p>That {kind === 'dish' ? 'dish' : 'item'} doesn't exist.</p>;

  return (
    <Editor
      key={`${kind}-${subjectId}`}
      kind={kind}
      subjectId={subjectId}
      name={name}
      recipe={recipeQuery.data ?? null}
      sellingPrice={row?.selling_price ?? recipeQuery.data?.breakdown.selling_price ?? null}
      items={items.data.items}
      overviewRows={overview.data.rows}
      defaults={defaults.data}
    />
  );
}

interface EditorProps {
  kind: 'dish' | 'made';
  subjectId: number;
  name: string;
  recipe: Recipe | null;
  /** The menu price in rupees; dishes only. */
  sellingPrice: number | string | null;
  items: InventoryItem[];
  overviewRows: OverviewRow[];
  defaults: Record<OverheadKind, OverheadOverride>;
}

function Editor({ kind, subjectId, name, recipe, sellingPrice, items, overviewRows, defaults }: EditorProps) {
  const isMade = kind === 'made';
  const byId = useMemo(() => new Map(items.map(i => [i.id, i])), [items]);
  const madeIds = useMemo(() => new Set(overviewRows.filter(r => r.kind === 'made').map(r => r.inventory_item_id)), [overviewRows]);
  const ownItem = byId.get(subjectId);

  const [lines, setLines] = useState<Line[]>(() =>
    (recipe?.ingredients ?? []).map(i => ({ key: newKey(), itemId: i.inventory_item_id, quantity: String(Number(i.quantity)), unit: i.unit })));
  const [yieldText, setYieldText] = useState(() => {
    if (!recipe) return isMade ? '' : '1';
    const saved = Number(recipe.yield_units);
    if (!isMade) return String(saved);
    // A made item's yield is the sum of its lines (in its own unit, worked out by the server) unless someone typed one.
    const auto = recipe.auto_yield == null ? null : Number(recipe.auto_yield);
    return auto !== null && Math.abs(auto - saved) < 1e-6 ? '' : String(saved);
  });
  const [overheads, setOverheads] = useState<Record<OverheadKind, OverheadDraft>>(() => {
    const start = {} as Record<OverheadKind, OverheadDraft>;
    for (const { kind: k } of OVERHEADS) {
      const saved = recipe?.[k];
      start[k] = saved?.mode && saved.value != null
        ? { mode: saved.mode, value: String(Number(saved.value)) }
        : { mode: defaults[k].mode ?? 'percent', value: '' };
    }
    return start;
  });
  const [savedId, setSavedId] = useState<number | null>(recipe?.id ?? null);
  const [priceInput, setPriceInput] = useState(sellingPrice == null ? '' : String(Number(sellingPrice)));
  const [priceDirty, setPriceDirty] = useState(false);
  const typedPrice = parseAmount(priceInput);
  const updateMenu = useUpdateMenuItem();
  const queryClient = useQueryClient();
  const commitPrice = () => {
    if (typedPrice === null || typedPrice <= 0) return;
    const paise = Math.round(typedPrice * 100);
    if (paise === Math.round(Number(sellingPrice ?? breakdown?.selling_price ?? 0) * 100)) return;
    updateMenu.mutate(
      { id: subjectId, data: { price: paise } },
      {
        // Clear the flag only once the refetched price is in, or the old one flashes back.
        onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: costingKeys.all }); setPriceDirty(false); },
        onError: error => toast.error(describeApiError(error)),
      },
    );
  };
  const [focusKey, setFocusKey] = useState<string | null>(null);
  const pickerRef = useRef<HTMLInputElement>(null);

  // Focus once the row has rendered with its item, so what is typed lands in a bound, controlled input.
  useEffect(() => {
    if (!focusKey) return;
    const line = lines.find(l => l.key === focusKey);
    if (line && !byId.has(line.itemId)) return;
    (document.getElementById(`amt-${focusKey}`) ?? pickerRef.current)?.focus();
    setFocusKey(null);
  }, [focusKey, lines, byId]);
  const linesRef = useRef(lines);
  linesRef.current = lines;
  const [pickNote, setPickNote] = useState<string | null>(null);

  // What the server is asked to cost (and to save). Rows with no usable amount are left out of the preview.
  const usable = lines.filter(l => byId.has(l.itemId) && (isPresence(byId.get(l.itemId)) || parseQuantity(l.quantity) !== null));
  const incomplete = lines.length - usable.length;
  const payload = useMemo((): DishCostingIn | null => {
    const yieldUnits = parseQuantity(yieldText);
    if (!isMade && yieldUnits === null) return null;
    const data: DishCostingIn = {
      ...(isMade ? { inventory_item_id: subjectId } : { menu_item_id: subjectId }),
      yield_units: yieldUnits,
      // Not edited here, but a save replaces them: carry the recipe's own through.
      target_margin_percent: recipe?.target_margin_percent ?? null,
      notes: recipe?.notes ?? null,
      ingredients: usable.map(l => {
        const item = byId.get(l.itemId)!;
        return isPresence(item)
          ? { inventory_item_id: l.itemId, quantity: 1, unit: item.unit }
          : { inventory_item_id: l.itemId, quantity: parseQuantity(l.quantity)!, unit: l.unit };
      }),
    };
    if (!isMade) {
      for (const { kind: k } of OVERHEADS) {
        const value = parseAmount(overheads[k].value);
        data[k] = value === null ? { mode: null, value: null } : { mode: overheads[k].mode, value };
      }
    }
    return data;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines, yieldText, overheads, byId, isMade, subjectId, recipe?.target_margin_percent, recipe?.notes]);

  const payloadKey = JSON.stringify(payload);
  const [settled, setSettled] = useState(payloadKey);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(payloadKey), 300);
    return () => clearTimeout(timer);
  }, [payloadKey]);
  const preview = useRecipePreview(payload ? (JSON.parse(settled) as DishCostingIn | null) : null);
  const breakdown: CostBreakdown | undefined = preview.data ?? recipe?.breakdown;

  const save = useSaveRecipe();
  const [historyNote, setHistoryNote] = useState('');
  const setBrand = useSetBrand();
  const setPackPrice = useSetPackPrice();
  const updateItem = useUpdateItem();
  const [packErrors, setPackErrors] = useState<Record<string, string | null>>({});

  /** Post a typed pack price. A fresh item (no stock, no price) quick-added in g takes the pack's measure family first. */
  const commitPack = async (item: InventoryItem, line: Line, pack: { price: number; quantity: number; unit: string }) => {
    setPackErrors(c => ({ ...c, [line.key]: null }));
    try {
      const base = baseUnitOf(pack.unit);
      // Only a just-quick-added item (not yet set up in the grid) may change family; anything older could be in other recipes.
      const fresh = item.needs_setup === true && Number(item.current_quantity) === 0 && item.current_price == null;
      if (fresh && base && isMeasure(item.unit) && !sameFamily(item.unit, pack.unit)) {
        await updateItem.mutateAsync({ id: item.id, data: { unit: base } });
        // The typed amount was meant in the new family: 5 g → 5 ml, 0.25 kg → 0.25 L.
        patchLine(line.key, { unit: ({ g: 'ml', kg: 'L', ml: 'g', L: 'kg' } as Record<string, string>)[line.unit] ?? base });
      }
      await setPackPrice.mutateAsync({ id: item.id, price: pack.price, pack_quantity: pack.quantity, pack_unit: pack.unit });
    } catch (error) {
      setPackErrors(c => ({ ...c, [line.key]: describeApiError(error) }));
    }
  };

  const pickable = items.filter(i => i.is_active && !(isMade && i.id === subjectId) && !lines.some(l => l.itemId === i.id));
  const addLine = (item: InventoryItem) => {
    const key = newKey();
    setLines(current => [...current, { key, itemId: item.id, quantity: '', unit: unitOptions(item)[0] }]);
    setFocusKey(key);
  };
  /** Quick-add an item that isn't in inventory yet ("oregano", or "oregano kg"; unit defaults to g), then add it as a line. */
  const addNew = async (text: string) => {
    setPickNote(null);
    const m = text.trim().match(/^(.*\S)\s+(kg|g|l|ml|pcs|pkt)$/i);
    const name = m ? m[1] : text.trim();
    const unit = m ? (m[2].toLowerCase() === 'l' ? 'L' : m[2].toLowerCase()) : 'g';
    try {
      const item = await inventoryApi.quickAddItem(name, unit);
      await queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
      if (isMade && item.id === subjectId) { setPickNote("A recipe can't use itself"); return; }
      const existing = linesRef.current.find(l => l.itemId === item.id);
      if (existing) setFocusKey(existing.key);
      else addLine(item);
    } catch (e) {
      toast.error(describeApiError(e));
    }
  };
  const patchLine = (key: string, patch: Partial<Line>) => setLines(current => current.map(l => (l.key === key ? { ...l, ...patch } : l)));

  const onSave = () => {
    if (!payload) return;
    save.mutate(
      { id: savedId, data: { ...payload, history_note: historyNote.trim() || null } },
      { onSuccess: saved => { setSavedId(saved.id); setHistoryNote(''); toast.success('Saved'); }, onError: error => toast.error(describeApiError(error)) },
    );
  };

  const remove = useDeleteRecipe();
  const navigate = useNavigate();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const onDelete = () => {
    if (savedId === null) return;
    remove.mutate(savedId, {
      onSuccess: () => { toast.success('Recipe deleted'); navigate('/admin/ops/recipes'); },
      onError: error => { setConfirmDelete(false); toast.error(describeApiError(error)); },
    });
  };

  // Matched by item, not position: the preview can be a debounce behind the rows.
  const costed = (itemId: number): IngredientLine | undefined => breakdown?.ingredients.find(l => l.inventory_item_id === itemId);

  // The saved price can arrive after first render; follow it until the user types their own.
  const savedPrice = sellingPrice ?? breakdown?.selling_price ?? null;
  useEffect(() => {
    if (!priceDirty) setPriceInput(savedPrice == null ? '' : String(Number(savedPrice)));
  }, [savedPrice, priceDirty]);

  const lower = breakdown ? !breakdown.is_complete : false;
  const money = (value: number | string | null | undefined) => (value == null ? '—' : `${lower ? '≥ ' : ''}${rupees(value)}`);
  const unitLabel = isMade ? (recipe?.unit ?? ownItem?.unit ?? '') : 'portion';
  // The typed menu price counts at once; the server's margin catches up once it is saved.
  const price = isMade ? null : typedPrice !== null && typedPrice > 0 ? typedPrice : breakdown?.selling_price == null ? null : Number(breakdown.selling_price);
  const perUnit = breakdown ? Number(breakdown.cost_per_unit) : 0;
  // A made item's cost is per g or ml; it reads per kg or L.
  const shown = isMade && breakdown ? perUnitCost(perUnit, unitLabel) : null;
  const costLabel = isMade ? `Cost per ${shown?.unit ?? unitLabel}` : 'Cost per portion';
  const costText = !breakdown ? '—' : shown ? `${lower ? '≥ ' : ''}${rupees(shown.cost)}` : money(breakdown.cost_per_unit);
  const margin = price && Number(breakdown?.raw_material_cost ?? 0) > 0 ? ((price - perUnit) / price) * 100 : null;
  const target = breakdown?.target_margin_percent == null ? null : Number(breakdown.target_margin_percent);
  const usedIn = recipe?.used_in ?? [];

  return (
    <div>
      <p className="muted"><Link to="/admin/ops/recipes">← Recipes</Link></p>
      <h1>{name} {isMade && <span className="pill made">made here</span>}</h1>

      {/* Wide screens: ingredients on the left, summary and charges on the right. Narrow: summary, ingredients, charges. */}
      <div className="recipe-grid">
      <section className="r-sum" aria-labelledby="sum-h">
      <h2 id="sum-h">Summary</h2>
      <div className="ops-stats">
        <div className="ops-stat">
          <span><label htmlFor="yield">Batch makes{unitLabel && ` (${unitLabel})`}</label></span>
          <input
            id="yield"
            inputMode="decimal"
            value={yieldText}
            placeholder={isMade && breakdown ? String(Number(breakdown.yield_units)) : undefined}
            onChange={event => setYieldText(event.target.value)}
          />
        </div>
        <div className="ops-stat"><span>Raw material / batch</span><b>{breakdown ? money(breakdown.raw_material_cost) : '—'}</b></div>
        <div className="ops-stat key"><span>{costLabel}</span><b>{costText}</b></div>
        {!isMade && (
          <>
            <div className="ops-stat"><span>Menu price</span><input
                id="menu-price"
                inputMode="decimal"
                aria-label="Menu price in rupees"
                placeholder="₹"
                value={priceInput}
                onChange={event => { setPriceInput(event.target.value); setPriceDirty(true); }}
                onBlur={commitPrice}
                onKeyDown={event => { if (event.key === 'Enter') event.currentTarget.blur(); }}
              /></div>
            <div className="ops-stat">
              <span>Margin</span>
              <b>
                {margin === null ? '—' : `${lower ? '≤ ' : ''}${percent(margin)}`}{' '}
                {margin !== null && target !== null && margin < target && <span className="pill warn">below {percent(target)}</span>}
              </b>
            </div>
          </>
        )}
      </div>

      {isMade && usedIn.length > 0 && (
        <p className="ops-used muted">
          Used in:{' '}
          {usedIn.map(u => {
            const linkTarget = overviewRows.find(r => r.costing_id === u.costing_id);
            const to = u.kind === 'dish' ? `/admin/ops/recipes/dish/${linkTarget?.menu_item_id}` : `/admin/ops/recipes/made/${linkTarget?.inventory_item_id}`;
            return linkTarget ? <Link key={u.costing_id} to={to}>{u.name}</Link> : <span key={u.costing_id}>{u.name} </span>;
          })}
        </p>
      )}
      </section>

      <div className="r-table">
      <div className="ops-wrap">
        <table className="ops-t">
          <thead>
            <tr>
              <th>Ingredient</th><th className="grow">Brand</th><th className="n">Amount used</th><th className="n">Price per pack</th>
              <th className="n">Cost in recipe</th><th className="n">% of food cost</th><th className="x"><span className="sr-only">Remove</span></th>
            </tr>
          </thead>
          <tbody>
            {lines.map(line => {
              const item = byId.get(line.itemId);
              const presence = isPresence(item);
              const ok = presence || parseQuantity(line.quantity) !== null;
              const bl = ok && item ? costed(line.itemId) : undefined;
              const lineIsMade = madeIds.has(line.itemId);
              const options = item ? unitOptions(item) : [line.unit];
              if (!options.includes(line.unit)) options.push(line.unit);
              const text = priceText(item, bl);
              const source = bl?.price_source ?? item?.price_source ?? null;
              return (
                <tr key={line.key}>
                  <td>
                    {item?.name ?? bl?.name ?? 'Unknown item'}
                    {lineIsMade && <> <span className="pill made">made</span></>}
                    {item && !item.is_active && <> <span className="pill bad">retired</span></>}
                  </td>
                  <td>
                    {item && !lineIsMade ? (
                      <input
                        key={item.brand ?? ''}
                        className="cell-in"
                        aria-label={`Brand for ${item.name}`}
                        defaultValue={item.brand ?? ''}
                        placeholder="—"
                        onBlur={event => {
                          const brand = event.target.value.trim();
                          if (brand !== (item.brand ?? '')) {
                            setBrand.mutate({ id: item.id, brand: brand || null }, { onError: error => toast.error(describeApiError(error)) });
                          }
                        }}
                      />
                    ) : '—'}
                  </td>
                  <td className="n">
                    {presence ? <span className="muted">covered by overheads</span> : (
                      <span className="amount">
                        <input
                          id={`amt-${line.key}`}
                          inputMode="decimal"
                          aria-label={`Amount of ${item?.name ?? 'ingredient'}`}
                          value={line.quantity}
                          onChange={event => patchLine(line.key, { quantity: event.target.value })}
                          onKeyDown={event => { if (event.key === 'Enter') pickerRef.current?.focus(); }}
                        />
                        <select aria-label={`Unit for ${item?.name ?? 'ingredient'}`} value={line.unit} onChange={event => patchLine(line.key, { unit: event.target.value })}>
                          {options.map(u => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </span>
                    )}
                    {!ok && <span className="err">Enter an amount</span>}
                  </td>
                  <td className="n">
                    {presence ? '—' : (
                      <PriceCell
                        key={text ?? 'none'}
                        item={item}
                        text={text}
                        editable={!!item && !lineIsMade && source !== 'purchase'}
                        note={bl ? describeSource(bl) : null}
                        serverError={packErrors[line.key] ?? null}
                        onCommit={pack => item && commitPack(item, line, pack)}
                      />
                    )}
                  </td>
                  <td className="n">
                    {presence ? '—' : !bl ? (ok ? '…' : '') : bl.price_missing || bl.reason ? <span className="gap">no price yet</span> : rupees(bl.line_cost)}
                  </td>
                  <td className="n">{bl?.share_percent != null ? `${Number(bl.share_percent).toFixed(1)}%` : ''}</td>
                  <td className="x">
                    <button type="button" className="icon-btn" aria-label={`Remove ${item?.name ?? 'ingredient'}`} onClick={() => setLines(c => c.filter(l => l.key !== line.key))}>×</button>
                  </td>
                </tr>
              );
            })}
            <tr>
              <td colSpan={7}>
                <Picker items={pickable} madeIds={madeIds} inputRef={pickerRef} onPick={item => { setPickNote(null); addLine(item); }} onAddNew={addNew} note={pickNote} />
              </td>
            </tr>

            <tr className="tot">
              <td colSpan={4}>Raw material (batch of {breakdown ? Number(breakdown.yield_units).toLocaleString('en-IN') : '…'}){lower && ' — some prices missing'}</td>
              <td className="n">{breakdown ? money(breakdown.raw_material_cost) : '—'}</td>
              <td className="n">{breakdown && Number(breakdown.raw_material_cost) > 0 ? '100%' : ''}</td>
              <td />
            </tr>
            {isMade && (
              <tr className="tot">
                <td colSpan={4}>{costLabel}</td>
                <td className="n">{costText}</td>
                <td colSpan={2} />
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="muted">Boxes with a blue outline are typed. Everything else is worked out. A made item&apos;s cost per {isMade ? unitLabel : 'unit'} comes from its own recipe.</p>
      </div>

      <div className="r-side">
      {!isMade && breakdown && (
        <section className="r-charges" aria-labelledby="charges-h">
          <h2 id="charges-h">Additional charges</h2>
          {/* Charges are for the whole batch (a % is of the batch's raw material), so the sum is shown per batch, then split. */}
          <p className="muted r-note">Added on top of raw material, for the whole batch.</p>
          <table className="ops-t">
            <tbody>
              <tr>
                <td>Raw material</td>
                <td />
                <td className="n">{money(breakdown.raw_material_cost)}</td>
              </tr>
              {OVERHEADS.map(({ kind: k, label }) => {
                const inherited = breakdown.overheads.find(o => o.kind === k);
                const draft = overheads[k];
                const fallback = defaults[k];
                const placeholder = fallback.value != null ? String(Number(fallback.value)) : '0';
                const setMode = (kind: OverheadKind, mode: OverheadMode) => setOverheads(c => ({ ...c, [kind]: { ...c[kind], mode } }));
                return (
                  <tr key={k}>
                    <td>+ {label}</td>
                    <td className="n">
                      <span className="amount">
                        <input
                          inputMode="decimal"
                          aria-label={`${label} (${MODE_LABEL[draft.mode]})`}
                          value={draft.value}
                          placeholder={placeholder}
                          onChange={event => setOverheads(c => ({ ...c, [k]: { ...c[k], value: event.target.value } }))}
                        />
                        <button
                          type="button"
                          className="mode"
                          aria-label={`${label}: switch to ${draft.mode === 'percent' ? 'rupees' : 'percent of raw material'}`}
                          onClick={() => setMode(k, draft.mode === 'percent' ? 'amount' : 'percent')}
                        >{draft.mode === 'percent' ? '%' : '₹'}</button>
                      </span>
                      {draft.mode !== 'percent' && (
                        <span className="per" role="group" aria-label={`${label} rupees are`}>
                          <button type="button" aria-pressed={draft.mode === 'amount'} onClick={() => setMode(k, 'amount')}>per batch</button>
                          <button type="button" aria-pressed={draft.mode === 'each'} onClick={() => setMode(k, 'each')}>per {unitLabel}</button>
                        </span>
                      )}
                    </td>
                    <td className="n">{inherited ? rupees(inherited.amount) : '—'}</td>
                  </tr>
                );
              })}
              <tr className="tot">
                <td colSpan={2}>Batch total</td>
                <td className="n">{money(breakdown.total_cost)}</td>
              </tr>
              <tr className="key">
                <td colSpan={2}>
                  {costLabel}
                  <span className="src">{money(breakdown.total_cost)} ÷ {Number(breakdown.yield_units)}</span>
                </td>
                <td className="n">{costText}</td>
              </tr>
            </tbody>
          </table>
        </section>
      )}

      <div className="ops-actions">
        <input
          className="r-note-input" type="text" maxLength={300} value={historyNote} onChange={e => setHistoryNote(e.target.value)}
          placeholder="Why? (optional, shown in the price history)" aria-label="Note for the price history"
        />
        <button type="button" className="btn" onClick={onSave} disabled={!payload || incomplete > 0 || save.isPending || preview.isError}>
          {save.isPending ? 'Saving…' : 'Save recipe'}
        </button>
        {incomplete > 0 && <span className="muted">Some rows need an amount first.</span>}
        {preview.isError && lines.length > 0 && <span className="err">Can&apos;t cost this yet: {describeApiError(preview.error)}</span>}
        {!payload && <span className="muted">Say how many portions a batch makes.</span>}
        {savedId !== null && (
          <button type="button" className="text-btn bad push-end" onClick={() => setConfirmDelete(true)} disabled={remove.isPending}>
            Delete recipe
          </button>
        )}
      </div>
      </div>
      </div>
      {savedId !== null && <PriceHistory kind={kind} subjectId={subjectId} />}
      <OpsConfirm
        open={confirmDelete}
        title={`Delete the recipe for ${name}?`}
        message={isMade && usedIn.length > 0
          ? `${name} stays in stock. The ${usedIn.length === 1 ? 'recipe that uses it' : `${usedIn.length} recipes that use it`} will need a price for it instead.`
          : isMade ? `${name} stays in stock; only how it's made goes.` : `${name} stays on the menu; only its costing goes.`}
        confirmText="Delete recipe"
        cancelText="Keep it"
        onClose={() => setConfirmDelete(false)}
        onConfirm={onDelete}
      />
    </div>
  );
}

/** Price per pack: plain when a purchase set it, typed ("₹99 / 10 g") when it didn't. */
function PriceCell({ item, text, editable, note, serverError, onCommit }: {
  item?: InventoryItem;
  text: string | null;
  editable: boolean;
  note: string | null;
  serverError?: string | null;
  onCommit: (pack: { price: number; quantity: number; unit: string }) => void;
}) {
  const [value, setValue] = useState(text ?? '');
  const [error, setError] = useState(false);
  if (!editable) {
    return (
      <>
        {text ?? <span className="gap">no price yet</span>}
        {note && <span className="src">{note}</span>}
      </>
    );
  }
  const commit = () => {
    const typed = value.trim();
    if (typed === '' || typed === text) { setError(false); return; }
    const pack = parsePackPrice(typed);
    setError(!pack);
    if (pack) onCommit(pack);
  };
  return (
    <>
      <input
        className="cell-in num"
        aria-label={`Price per pack for ${item?.name ?? 'ingredient'}`}
        aria-invalid={error}
        value={value}
        placeholder="no price yet"
        onChange={event => setValue(event.target.value)}
        onBlur={commit}
        onKeyDown={event => { if (event.key === 'Enter') event.currentTarget.blur(); }}
      />
      {error ? <span className="err">Type it like ₹99 / 10 g</span> : serverError ? <span className="err" role="alert">{serverError}</span> : note && <span className="src">{note}</span>}
    </>
  );
}

/** Search over active inventory items; Enter takes the first match. */
function Picker({ items, madeIds, inputRef, onPick, onAddNew, note }: {
  items: InventoryItem[];
  madeIds: Set<number | null>;
  inputRef: React.RefObject<HTMLInputElement>;
  onPick: (item: InventoryItem) => void;
  onAddNew: (text: string) => void;
  note: string | null;
}) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const matches = items.filter(i => i.name.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 8);
  const pick = (item: InventoryItem) => { onPick(item); setQuery(''); setOpen(false); };
  const typed = query.trim();
  const addNew = () => { onAddNew(typed); setQuery(''); setOpen(false); };
  return (
    <div className="ops-pick">
      <input
        ref={inputRef}
        role="combobox"
        aria-label="Add ingredient"
        aria-expanded={open && (matches.length > 0 || typed.length > 0)}
        aria-controls="ops-pick-list"
        className="cell-in"
        style={{ maxWidth: 280 }}
        placeholder="+ Add ingredient"
        value={query}
        onChange={event => { setQuery(event.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={event => {
          if (event.key === 'Enter') {
            event.preventDefault();
            const exact = items.find(i => i.name.toLowerCase() === typed.toLowerCase());
            if (exact || matches[0]) pick(exact ?? matches[0]);
            else if (typed) addNew();
          }
          if (event.key === 'Escape') setOpen(false);
        }}
      />
      {open && (matches.length > 0 || typed.length > 0) && (
        <ul id="ops-pick-list" role="listbox" aria-label="Ingredients">
          {matches.map(item => (
            <li key={item.id} role="presentation">
              <button type="button" role="option" aria-selected="false" onMouseDown={event => event.preventDefault()} onClick={() => pick(item)}>
                <span>{item.name}{item.brand ? ` · ${item.brand}` : ''}</span>
                {madeIds.has(item.id) ? <span className="pill made">made</span> : <span className="muted">{item.unit}</span>}
              </button>
            </li>
          ))}
          {typed && (
            <li role="presentation">
              <button type="button" role="option" aria-selected="false" onMouseDown={event => event.preventDefault()} onClick={addNew}>
                + Add “{typed}” as a new ingredient
              </button>
            </li>
          )}
        </ul>
      )}
      {note && <span className="err" role="alert">{note}</span>}
    </div>
  );
}
