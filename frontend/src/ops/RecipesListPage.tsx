import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { describeApiError } from '../utils/apiError';
import { perUnitCost, rupees } from '../utils/costing';
import { useOverview } from './api';
import type { OverviewRow } from './api';

type Filter = 'all' | 'attention' | 'made' | 'none';
const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'attention', label: 'Needs attention' },
  { id: 'made', label: 'Made here' },
  { id: 'none', label: 'No recipe' },
];

const matches = (row: OverviewRow, filter: Filter) =>
  filter === 'all'
  || (filter === 'attention' && (row.status === 'below_target' || row.status === 'missing_prices'))
  || (filter === 'made' && row.kind === 'made')
  || (filter === 'none' && row.status === 'no_recipe');

export const rowPath = (row: OverviewRow) =>
  row.kind === 'dish' ? `/admin/ops/recipes/dish/${row.menu_item_id}` : `/admin/ops/recipes/made/${row.inventory_item_id}`;

const num = (v: number | string | null | undefined) => (v == null || !Number.isFinite(Number(v)) ? null : Number(v));
const incomplete = (row: OverviewRow) => row.missing_count > 0;

function costText(row: OverviewRow): string {
  const cost = num(row.cost_per_unit);
  if (row.status === 'no_recipe' || cost == null) return '—';
  const shown = row.kind === 'made' && row.unit ? perUnitCost(cost, row.unit) : { cost, unit: null };
  return `${incomplete(row) ? '≥ ' : ''}${rupees(shown.cost)}${shown.unit ? ` / ${shown.unit}` : ''}`;
}

const percentText = (n: number) => `${Math.round(n) < 0 ? '−' : ''}${Math.abs(Math.round(n))}%`;

function marginText(row: OverviewRow): string {
  if (incomplete(row)) {
    const ceiling = num(row.margin_ceiling);
    return ceiling == null ? '—' : `≤ ${percentText(ceiling)}`;
  }
  const margin = num(row.margin_percent);
  return margin == null ? '—' : percentText(margin);
}

/** Change in cost since last week. */
function weekChange(row: OverviewRow): { text: string; tone?: 'up' | 'down' } {
  const now = num(row.cost_per_unit);
  const before = num(row.cost_last_week);
  if (now == null || before == null) return { text: '—' };
  // A made item's cost is per g or ml; the change reads per kg or L, scaled before it is rounded.
  const raw = now - before;
  const diff = Math.round((row.kind === 'made' ? perUnitCost(raw, row.unit).cost : raw) * 100) / 100;
  if (diff === 0) return { text: '—' };
  return { text: `${diff > 0 ? '+' : '−'}${rupees(Math.abs(diff))}`, tone: diff > 0 ? 'up' : 'down' };
}

function Status({ row }: { row: OverviewRow }) {
  switch (row.status) {
    case 'below_target':
      return <span className="pill bad">{num(row.target_margin_percent) == null ? 'below target' : `below ${Math.round(Number(row.target_margin_percent))}%`}</span>;
    case 'missing_prices':
      return <span className="pill warn">{row.missing_count === 1 ? '1 price missing' : `${row.missing_count} prices missing`}</span>;
    case 'no_recipe':
      return <span className="pill">no recipe</span>;
    case 'on_target':
      return <span className="pill ok">on target</span>;
    default:
      return <span className="pill ok">costed</span>;
  }
}

function NewRecipeMenu({ rows }: { rows: OverviewRow[] }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState<'closed' | 'menu' | 'dish'>('closed');
  const [q, setQ] = useState('');
  const box = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (open === 'closed') return;
    const away = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen('closed'); };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') { setOpen('closed'); trigger.current?.focus(); } };
    document.addEventListener('mousedown', away);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', away); document.removeEventListener('keydown', esc); };
  }, [open]);
  const dishes = rows.filter(r => r.kind === 'dish' && r.status === 'no_recipe' && r.name.toLowerCase().includes(q.trim().toLowerCase()));
  return (
    <div className="ops-new" ref={box}>
      <button ref={trigger} type="button" className="btn" aria-expanded={open !== 'closed'} onClick={() => setOpen(open === 'closed' ? 'menu' : 'closed')}>
        + New recipe
      </button>
      {open === 'menu' && (
        <ul className="ops-menu">
          <li><button type="button" onClick={() => setOpen('dish')}>Dish from the menu…</button></li>
          <li><button type="button" onClick={() => navigate('/admin/ops/recipes/made/new')}>Made in the kitchen</button></li>
        </ul>
      )}
      {open === 'dish' && (
        <div className="ops-menu">
          <input autoFocus placeholder="Search dishes without a recipe" aria-label="Search dishes without a recipe" value={q} onChange={e => setQ(e.target.value)} />
          <ul>
            {dishes.map(d => (
              <li key={d.menu_item_id}>
                <button type="button" onClick={() => navigate(rowPath(d))}>{d.name}<span className="muted">{d.category}</span></button>
              </li>
            ))}
            {dishes.length === 0 && <li className="muted pad">No dishes without a recipe.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function RecipesListPage() {
  const overview = useOverview();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>('all');

  const rows = overview.data?.rows;
  const shown = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (rows ?? []).filter(r => matches(r, filter) && r.name.toLowerCase().includes(needle));
  }, [rows, search, filter]);

  if (overview.isError) return <p className="err">{describeApiError(overview.error)}</p>;
  if (!overview.data) return <p className="muted">Loading…</p>;

  const { totals } = overview.data;
  const dishCount = overview.data.rows.filter(r => r.kind === 'dish').length;
  const madeCount = overview.data.rows.length - dishCount;
  const avg = num(totals.average_margin);

  return (
    <>
      <h1>Recipes</h1>
      <p className="muted">{dishCount} dishes · {madeCount} made in the kitchen</p>
      <div className="ops-stats">
        <div className="ops-stat"><span>Below target</span><b>{totals.below_target}</b></div>
        <div className="ops-stat"><span>Missing a price</span><b>{totals.missing_prices}</b></div>
        <div className="ops-stat"><span>No recipe yet</span><b>{totals.no_recipe}</b></div>
        <div className="ops-stat"><span>Average margin</span><b>{avg == null ? '—' : `${Math.round(avg)}%`}</b></div>
      </div>
      <div className="ops-filters">
        <input
          type="search" className="grow" placeholder="Search dishes and made items" aria-label="Search recipes"
          value={search} onChange={e => setSearch(e.target.value)}
        />
        <div className="chips" role="group" aria-label="Filter">
          {FILTERS.map(f => (
            <button key={f.id} type="button" className={`chip${filter === f.id ? ' on' : ''}`} aria-pressed={filter === f.id} onClick={() => setFilter(f.id)}>
              {f.label}
            </button>
          ))}
        </div>
        <NewRecipeMenu rows={overview.data.rows} />
      </div>
      <div className="ops-wrap">
        <table className="ops-t ops-list">
          <thead>
            <tr>
              <th>Name</th><th>Type</th><th className="n">Cost / portion</th><th className="n">Menu price</th>
              <th className="n">Margin</th><th className="n">vs last week</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {shown.map(row => {
              const change = weekChange(row);
              return (
                <tr key={`${row.kind}-${row.menu_item_id ?? row.inventory_item_id}`} className="click" onClick={() => navigate(rowPath(row))}>
                  <td className="name"><Link to={rowPath(row)} onClick={e => e.stopPropagation()}>{row.name}</Link></td>
                  <td className="type">{row.kind === 'made' ? <span className="pill made">Made</span> : 'Dish'}</td>
                  <td className="n cost" data-l="Cost">{costText(row)}</td>
                  <td className="n price" data-l="Price">{row.kind === 'made' ? '—' : rupees(row.selling_price)}</td>
                  <td className="n margin" data-l="Margin">{marginText(row)}</td>
                  <td className={`n week ${change.tone ?? ''}`} data-l="Vs last week">{change.text}</td>
                  <td className="status"><Status row={row} /></td>
                </tr>
              );
            })}
            {shown.length === 0 && <tr><td colSpan={7} className="muted">Nothing matches.</td></tr>}
          </tbody>
        </table>
      </div>
      <p className="muted">"vs last week" is the change in cost per portion from approved price changes. Made items show cost per kg or per piece and feed every dish that uses them.</p>
    </>
  );
}
