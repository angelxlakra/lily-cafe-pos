import { useEffect, useRef, type RefObject } from 'react';

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Modal focus behaviour: keeps Tab inside the dialog, closes on Escape
 * (unless `locked`), and returns focus to whatever opened it on close.
 */
export function useDialogFocus(dialog: RefObject<HTMLElement>, onClose: () => void, locked = false) {
  const opener = useRef<Element | null>(document.activeElement);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const lockedRef = useRef(locked);
  lockedRef.current = locked;

  useEffect(() => {
    const returnTo = opener.current;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !lockedRef.current) {
        onCloseRef.current();
        return;
      }
      if (event.key !== 'Tab' || !dialog.current) return;
      const focusable = [...dialog.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      if (returnTo instanceof HTMLElement && returnTo.isConnected) returnTo.focus({ preventScroll: true });
    };
  }, [dialog]);
}
