import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="bg-off-white border border-neutral-border/70 rounded-2xl p-8 text-center shadow-sm flex flex-col items-center gap-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-cream text-coffee-brown text-3xl">
        {icon}
      </div>
      <div>
        <h3 className="font-heading heading-sub text-coffee-brown mb-1">
          {title}
        </h3>
        <p className="text-sm text-muted max-w-sm mx-auto">{description}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="btn-primary px-6"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
