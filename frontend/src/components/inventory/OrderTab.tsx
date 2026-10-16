/**
 * Tonight's orders: what's low, grouped by each item's usual vendor, as one
 * paste-ready message per vendor with a Copy button. Copy-paste on purpose:
 * it works on whichever app the vendor uses, and the message can still be
 * edited before sending. Items with no vendor collect under Unassigned, so
 * vendor setup never hides an alert. See docs/INVENTORY_PLAN.md, step 7.
 */

import { useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, Copy, Phone, Storefront } from '@phosphor-icons/react';
import LoadingSpinner from '../LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';
import { inventoryApi } from '../../api/inventory';
import { describeApiError } from '../../utils/apiError';
import { formatQty } from '../../utils/countQuantity';
import { toast } from '../../utils/toast';
import {
  groupOrders, parseOrderQuantity, renderMessage, suggestQuantity, unitFor, type OrderGroup, type OrderLine,
} from '../../utils/orderMessage';
import type { InventoryItem, Vendor } from '../../types/inventory';

const field =
  'h-11 rounded-lg border border-neutral-border bg-off-white px-3 text-base text-neutral-text-dark tabular-nums focus:outline-none focus:border-lily-ink focus:bg-white dark:focus:bg-neutral-background';

export default function OrderTab({ onSetUpVendors }: { onSetUpVendors?: () => void }) {
  const { isOwner } = useAuth();
  const { data: itemsResponse, isLoading, error } = useQuery({
    queryKey: ['inventory', 'items', { is_active: true }],
    queryFn: () => inventoryApi.getItems({ is_active: true }),
  });
  const { data: vendors = [] } = useQuery({ queryKey: ['inventory', 'vendors'], queryFn: inventoryApi.getVendors });
  const groups = useMemo(() => groupOrders(itemsResponse?.items ?? [], vendors), [itemsResponse, vendors]);

  // What the owner changed: a quantity typed over the suggestion, or a line left out.
  const [quantities, setQuantities] = useState<Record<number, string>>({});
  const [left, setLeft] = useState<Set<number>>(new Set());

  if (isLoading) {
    return <div className="py-12 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading…</div>;
  }
  if (error) return <p role="alert" className="text-sm font-medium text-error">{describeApiError(error)}</p>;

  const lowCount = groups.reduce((sum, group) => sum + group.items.length, 0);

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-5 pb-16">
      <div>
        <h2 className="font-heading text-2xl! text-neutral-text-dark">Tonight's orders</h2>
        <p className="mt-1 text-neutral-text-body">
          {lowCount === 0
            ? 'Nothing is low. Every item is above its alert level.'
            : `${lowCount} ${lowCount === 1 ? 'item is' : 'items are'} below the alert level. Check each message, copy it, and paste it into WhatsApp or Telegram.`}
        </p>
        {lowCount > 0 && (
          <p className="mt-1 text-sm text-neutral-text-muted">Quantities are suggestions to bring stock back to twice the alert level. Change any of them.</p>
        )}
      </div>

      {groups.map(group => (
        <VendorOrder
          key={group.vendor?.id ?? 'unassigned'}
          group={group}
          isOwner={isOwner}
          quantities={quantities}
          left={left}
          onQuantity={(id, text) => setQuantities(q => ({ ...q, [id]: text }))}
          onToggle={id => setLeft(current => {
            const next = new Set(current);
            if (next.has(id)) next.delete(id); else next.add(id);
            return next;
          })}
          onSetUpVendors={onSetUpVendors}
        />
      ))}
    </div>
  );
}

interface VendorOrderProps {
  group: OrderGroup<InventoryItem>;
  isOwner: boolean;
  quantities: Record<number, string>;
  left: Set<number>;
  onQuantity: (id: number, text: string) => void;
  onToggle: (id: number) => void;
  onSetUpVendors?: () => void;
}

function VendorOrder({ group, isOwner, quantities, left, onQuantity, onToggle, onSetUpVendors }: VendorOrderProps) {
  const [copied, setCopied] = useState(false);
  const messageRef = useRef<HTMLPreElement>(null);
  const { vendor } = group;
  const headingId = `order-${vendor?.id ?? 'unassigned'}`;

  const quantityText = (item: InventoryItem) => {
    if (item.id in quantities) return quantities[item.id];
    const suggested = suggestQuantity(item);
    return suggested == null ? '' : String(suggested);
  };
  const lines: OrderLine[] = group.items
    .filter(item => !left.has(item.id))
    .map(item => ({
      name: item.name,
      unit: item.unit,
      quantity: item.count_mode === 'presence' ? null : parseOrderQuantity(quantityText(item)),
    }));
  const message = renderMessage(lines, new Date().getHours());

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // No clipboard (an old browser or an app view): select it so a long-press copies it.
      const range = document.createRange();
      if (messageRef.current) {
        range.selectNodeContents(messageRef.current);
        window.getSelection()?.removeAllRanges();
        window.getSelection()?.addRange(range);
      }
      toast.error("Couldn't copy automatically", { description: 'The message is selected. Copy it from there.' });
    }
  };

  return (
    <section aria-labelledby={headingId} className="card flex flex-col gap-4 p-4 sm:p-5">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 id={headingId} className="font-sans! text-lg! font-semibold tracking-normal! text-neutral-text-dark">
            {vendor ? vendor.name : 'Unassigned'}
          </h3>
          {vendor ? (
            <VendorPhone vendor={vendor} canEdit={isOwner} />
          ) : (
            <p className="text-sm text-neutral-text-muted">
              No usual vendor set.{' '}
              {isOwner && onSetUpVendors && (
                <button type="button" onClick={onSetUpVendors} className="font-medium text-coffee-brown underline underline-offset-2">
                  Set vendors in Items
                </button>
              )}
            </p>
          )}
        </div>
        <span className="text-sm text-neutral-text-muted tabular-nums">
          {lines.length} of {group.items.length} {group.items.length === 1 ? 'item' : 'items'}
        </span>
      </header>

      <ul className="flex flex-col divide-y divide-neutral-border/70">
        {group.items.map(item => {
          const included = !left.has(item.id);
          const presence = item.count_mode === 'presence';
          const checkboxId = `order-include-${item.id}`;
          return (
            <li key={item.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2">
              <input
                id={checkboxId}
                type="checkbox"
                checked={included}
                onChange={() => onToggle(item.id)}
                className="size-5 accent-coffee-brown"
              />
              <label htmlFor={checkboxId} className={`min-w-0 flex-1 ${included ? 'text-neutral-text-dark' : 'text-neutral-text-light line-through'}`}>
                <span className="font-medium">{item.name}</span>
                <span className="block text-sm text-neutral-text-muted no-underline">
                  {presence ? 'Out' : `${formatQty(item.current_quantity)} ${unitFor(item.unit, Number(item.current_quantity))} left · alert below ${formatQty(item.min_threshold)}`}
                </span>
              </label>
              {!presence && (
                <span className="flex items-center gap-2">
                  <input
                    inputMode="decimal"
                    value={quantityText(item)}
                    disabled={!included}
                    onChange={event => onQuantity(item.id, event.target.value)}
                    className={`${field} w-20 text-right disabled:opacity-50`}
                    aria-label={`How much ${item.name} to order`}
                  />
                  <span className="w-16 text-sm text-neutral-text-muted">
                    {unitFor(item.unit, parseOrderQuantity(quantityText(item)) ?? 2)}
                  </span>
                </span>
              )}
            </li>
          );
        })}
      </ul>

      <div className="flex flex-col gap-3">
        <pre
          ref={messageRef}
          className="whitespace-pre-wrap rounded-lg border border-neutral-border bg-neutral-background px-4 py-3 font-sans text-sm text-neutral-text-body"
          aria-label={`Message to ${vendor?.name ?? 'an unassigned vendor'}`}
        >
          {message}
        </pre>
        <button
          type="button"
          onClick={copy}
          disabled={lines.length === 0}
          className="btn-primary inline-flex items-center justify-center gap-2 self-stretch sm:self-start"
        >
          {copied ? <Check size={20} weight="bold" aria-hidden /> : <Copy size={20} aria-hidden />}
          {copied ? 'Copied' : vendor ? `Copy message for ${vendor.name}` : 'Copy message'}
        </button>
        <span className="sr-only" aria-live="polite">{copied ? 'Message copied' : ''}</span>
      </div>
    </section>
  );
}

/** The vendor's number, shown so the owner knows who to paste to. The owner can add or fix it here. */
function VendorPhone({ vendor, canEdit }: { vendor: Vendor; canEdit: boolean }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(vendor.phone ?? '');
  const [saving, setSaving] = useState(false);
  const inputId = `vendor-phone-${vendor.id}`;

  const save = async () => {
    setSaving(true);
    try {
      await inventoryApi.updateVendor(vendor.id, { phone: value.trim() || null });
      await queryClient.invalidateQueries({ queryKey: ['inventory', 'vendors'] });
      setEditing(false);
    } catch (error) {
      toast.error('Phone not saved', { description: describeApiError(error) });
    } finally {
      setSaving(false);
    }
  };

  if (editing) {
    return (
      <form className="mt-1 flex flex-wrap items-center gap-2" onSubmit={event => { event.preventDefault(); save(); }}>
        <label htmlFor={inputId} className="sr-only">Phone for {vendor.name}</label>
        <input id={inputId} type="tel" value={value} onChange={event => setValue(event.target.value)} className={`${field} h-10 w-44`} autoFocus />
        <button type="submit" disabled={saving} className="btn-primary min-h-10! py-1!">{saving ? 'Saving…' : 'Save'}</button>
        <button type="button" onClick={() => setEditing(false)} className="text-sm text-coffee-brown underline underline-offset-2">Cancel</button>
      </form>
    );
  }
  return (
    <p className="flex items-center gap-1.5 text-sm text-neutral-text-muted">
      {vendor.phone ? (
        <><Phone size={14} aria-hidden /><span className="select-all tabular-nums">{vendor.phone}</span></>
      ) : (
        <><Storefront size={14} aria-hidden />No phone saved</>
      )}
      {canEdit && (
        <button type="button" onClick={() => setEditing(true)} className="ml-1 font-medium text-coffee-brown underline underline-offset-2">
          {vendor.phone ? 'Change' : 'Add phone'}
        </button>
      )}
    </p>
  );
}
