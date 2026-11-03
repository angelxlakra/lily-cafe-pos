import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { rupees } from '../utils/costing';
import { useDishHistory } from './api';
import type { HistoryEntry } from './api';

const CAUSE: Record<HistoryEntry['cause'], string> = {
  recipe: 'Recipe saved',
  menu_price: 'Menu price changed',
  purchase: 'Purchase price',
  typed_price: 'Ingredient price changed',
  default_charges: 'Café-wide charges changed',
  baseline: 'History starts here',
};

const when = (iso: string) =>
  new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' });

/** "Cost per portion ₹48.82 → ₹49.30", or just the figure on the first row. */
function costLine(e: HistoryEntry, label: string) {
  const now = rupees(e.cost_per_unit);
  if (e.prev_cost_per_unit == null || Number(e.prev_cost_per_unit) === Number(e.cost_per_unit)) return `${label} ${now}`;
  return `${label} ${rupees(e.prev_cost_per_unit)} → ${now}`;
}

export default function PriceHistory({ kind, subjectId }: { kind: 'dish' | 'made'; subjectId: number }) {
  const history = useDishHistory(kind, subjectId);
  const label = kind === 'dish' ? 'Cost per portion' : 'Cost per unit';
  const entries = history.data?.entries ?? [];
  // Oldest first for the chart; the price is a step, so each point holds until the next.
  const points = [...entries].reverse().map(e => ({
    at: new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(e.created_at) ? e.created_at : `${e.created_at}Z`).getTime(),
    cost: Number(e.cost_per_unit),
    price: e.menu_price == null ? null : Number(e.menu_price),
  }));

  // Under three days of history, label by time of day: every tick would read the same date.
  const short = points.length > 1 && points[points.length - 1].at - points[0].at < 3 * 86400000;

  return (
    <section className="r-history" aria-labelledby="hist-h">
      <h2 id="hist-h">Price history</h2>
      {history.isLoading && <p className="muted">Loading…</p>}
      {history.isError && <p className="err">Couldn&apos;t load the history.</p>}
      {history.data && entries.length === 0 && <p className="muted">Nothing recorded yet. A row is added whenever the price, cost or recipe changes.</p>}
      {points.length > 1 && (
        <div className="r-hist-chart" role="img" aria-label={`${label} over time${kind === 'dish' ? ', against the menu price' : ''}`}>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={points} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--ops-rule)" vertical={false} />
              <XAxis dataKey="at" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={t => new Date(t).toLocaleString('en-IN', short ? { hour: 'numeric', minute: '2-digit' } : { day: 'numeric', month: 'short' })} fontSize={12} />
              <YAxis width={44} fontSize={12} tickFormatter={v => `₹${v}`} domain={['auto', 'auto']} />
              <Tooltip labelFormatter={t => when(new Date(Number(t)).toISOString())} formatter={(v, name) => [rupees(v as number), name]} />
              <Line type="stepAfter" dataKey="cost" name={label} stroke="var(--ops-tone-warn)" dot={false} strokeWidth={2} isAnimationActive={false} />
              {kind === 'dish' && <Line type="stepAfter" dataKey="price" name="Menu price" stroke="var(--ops-tone-ok)" dot={false} strokeWidth={2} connectNulls isAnimationActive={false} />}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <ol className="r-hist-list">
        {entries.map(e => (
          <li key={e.id}>
            <div className="r-hist-head">
              <strong>{CAUSE[e.cause]}</strong>
              <span className="muted">{when(e.created_at)}{e.actor ? ` · ${e.actor}` : ''}</span>
            </div>
            {e.detail && e.cause !== 'baseline' && e.detail !== CAUSE[e.cause] && !(e.cause === 'recipe' && e.detail.startsWith('Recipe ')) && <div className="muted">{e.detail}</div>}
            {e.moves.length > 0 && <ul className="r-hist-moves">{e.moves.map(m => <li key={m}>{m}</li>)}</ul>}
            <div className="r-hist-cost">
              {costLine(e, label)}
              {kind === 'dish' && e.menu_price != null && <span className="muted"> · menu {rupees(e.menu_price)}{e.margin_percent != null && ` · margin ${Number(e.margin_percent)}%`}</span>}
              {!e.is_complete && <span className="muted"> · some ingredients unpriced</span>}
            </div>
            {e.note && <div className="r-hist-note">“{e.note}”</div>}
            <details className="r-hist-recipe">
              <summary>Recipe at that moment</summary>
              <ul>
                {e.recipe.map(r => <li key={r.item_id}>{r.name}: {Number(r.quantity)} {r.unit} at {rupees(r.unit_price)}/{r.stock_unit}</li>)}
                {e.charges.map(c => <li key={c.kind} className="muted">{c.kind}: {rupees(c.amount)}</li>)}
                <li className="muted">Batch makes {Number(e.yield_units)}; raw material {rupees(e.raw_cost)}</li>
              </ul>
            </details>
          </li>
        ))}
      </ol>
    </section>
  );
}
