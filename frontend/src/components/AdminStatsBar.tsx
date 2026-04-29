// frontend/src/components/AdminStatsBar.tsx

interface StatItem {
  label: string;
  value: string;
  clickable?: boolean;
  onClick?: () => void;
  hint?: string;
}

interface AdminStatsBarProps {
  stats: StatItem[];
}

export default function AdminStatsBar({ stats }: AdminStatsBarProps) {
  return (
    <div className="flex border-b border-neutral-border bg-off-white relative z-10">
      {stats.map((stat, index) => {
        const isLast = index === stats.length - 1;
        const cellClass = `
          flex-1 px-4 py-3 text-left
          ${!isLast ? 'border-r border-neutral-border' : ''}
          ${stat.clickable ? 'cursor-pointer hover:bg-cream/50 transition-colors' : ''}
        `;

        // Use explicit conditional rendering to avoid TypeScript polymorphic-tag issues
        const content = (
          <>
            <p className="text-lg font-bold text-coffee-brown leading-tight">
              {stat.value}
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-neutral-text-light mt-0.5">
              {stat.label}
            </p>
            {stat.hint && (
              <p className="text-xs text-coffee-light mt-0.5">{stat.hint}</p>
            )}
          </>
        );

        return stat.clickable ? (
          <button key={stat.label} className={cellClass} onClick={stat.onClick}>
            {content}
          </button>
        ) : (
          <div key={stat.label} className={cellClass}>
            {content}
          </div>
        );
      })}
    </div>
  );
}
