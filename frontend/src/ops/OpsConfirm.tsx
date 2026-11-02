import { useRef } from 'react';
import { useDialogFocus } from '../hooks/useDialogFocus';

interface OpsConfirmProps {
  open: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  onConfirm: () => void;
  onClose: () => void;
}

/** A yes/no question in the ops look, the same sheet the count uses. */
export default function OpsConfirm(props: OpsConfirmProps) {
  return props.open ? <Sheet {...props} /> : null;
}

function Sheet({ title, message, confirmText, cancelText, onConfirm, onClose }: OpsConfirmProps) {
  const dialog = useRef<HTMLDivElement>(null);
  useDialogFocus(dialog, onClose);
  return (
    <div className="count-sheet-wrap">
      <div className="count-scrim" onClick={onClose} />
      <div ref={dialog} role="dialog" aria-modal="true" aria-labelledby="ops-confirm-title" className="count-sheet">
        <div className="count-sheet-body">
          <h2 id="ops-confirm-title">{title}</h2>
          <p className="muted">{message}</p>
        </div>
        <div className="count-actions">
          <button type="button" className="btn ghost" onClick={onClose}>{cancelText}</button>
          <button type="button" className="btn danger" onClick={onConfirm}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
}
