import type { CostStatus } from '../../utils/costing';

const TONE: Record<CostStatus['kind'], string> = {
  ok: 'bg-success/10 text-success border-success/20',
  gaps: 'bg-warning/10 text-warning border-warning/30',
  below: 'bg-error/10 text-error border-error/30',
  none: 'bg-off-white text-neutral-text-muted border-neutral-border',
};

/** A dish's margin on the Menu page. Tapping it opens the recipe. */
export default function CostChip({ status, dishName, onOpen }: { status: CostStatus; dishName: string; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className={`inline-flex min-h-9 items-center whitespace-nowrap rounded-full border px-3 text-sm font-semibold tabular-nums transition-colors hover:brightness-95 ${TONE[status.kind]}`}
      aria-label={`${dishName}: ${status.kind === 'none' ? 'add a recipe' : `margin ${status.label}, open recipe`}`}
    >
      {status.kind === 'none' ? '+ Recipe' : status.label}
    </button>
  );
}
