import type { Order } from '../types';

interface MoveTableModalProps {
  order: Order;
  onClose: () => void;
}

export default function MoveTableModal({ order: _order, onClose }: MoveTableModalProps) {
  // TODO(Task 4): destructure and use `order` when implementing the real move flow

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-50" onClick={onClose} aria-hidden="true" />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xs bg-off-white rounded-2xl shadow-2xl z-60" role="dialog" aria-modal="true">
        <p className="p-6 text-neutral-text-muted text-sm">Move Table (coming soon)</p>
      </div>
    </>
  );
}
