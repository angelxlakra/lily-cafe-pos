import type { ReactNode } from "react";
import Button from "./Button";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

/**
 * Enhanced EmptyState component
 * Provides engaging empty states with optional CTAs
 */
export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
}: EmptyStateProps) {
  return (
    <div className="bg-off-white border border-neutral-border/70 rounded-2xl p-12 text-center shadow-sm flex flex-col items-center gap-6 max-w-lg mx-auto animate-in fade-in duration-300">
      {/* Icon with subtle animation */}
      <div className="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-cream to-coffee-brown/10 text-coffee-brown text-5xl shadow-md animate-in zoom-in duration-500">
        {icon}
      </div>

      {/* Text content */}
      <div className="space-y-2">
        <h3 className="font-heading text-2xl font-bold text-coffee-brown">
          {title}
        </h3>
        <p className="text-base text-neutral-text-light max-w-md mx-auto leading-relaxed">
          {description}
        </p>
      </div>

      {/* Actions */}
      {(actionLabel || secondaryActionLabel) && (
        <div className="flex flex-col sm:flex-row gap-3 mt-2">
          {actionLabel && onAction && (
            <Button
              variant="primary"
              size="lg"
              onClick={onAction}
            >
              {actionLabel}
            </Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button
              variant="secondary"
              size="lg"
              onClick={onSecondaryAction}
            >
              {secondaryActionLabel}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
