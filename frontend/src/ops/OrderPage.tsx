/**
 * Tonight's orders: what's low, grouped by each item's usual vendor, as one
 * paste-ready message per vendor with a Copy button. Copy-paste on purpose:
 * it works on whichever app the vendor uses, and the message can still be
 * edited before sending. Items with no vendor collect under Unassigned, so
 * vendor setup never hides an alert. See docs/INVENTORY_PLAN.md, step 7.
 */

import { useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import LoadingSpinner from '../components/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';
import { inventoryApi } from '../api/inventory';
import { describeApiError } from '../utils/apiError';
import { formatQty } from '../utils/countQuantity';
import { toast } from '../utils/toast';
import {
  groupOrders, parseOrderQuantity, renderMessage, suggestQuantity, unitFor, type OrderGroup, type OrderLine,
} from '../utils/orderMessage';
import type { InventoryItem, Vendor } from '../types/inventory';

export default function OrderPage() {
  const { isOwner } = useAuth();
  const navigate = useNavigate();
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
    return <p className="muted"><LoadingSpinner /> Loading…</p>;
  }
  if (error) return <p role="alert" className="err">{describeApiError(error)}</p>;

  const lowCount = groups.reduce((sum, group) => sum + group.items.length, 0);

  return (
    <div className="ops-order">
      <div>
        <h1>Tonight's orders</h1>
        <p>
          {lowCount === 0
            ? 'Nothing is low. Every item is above its alert level.'
            : `${lowCount} ${lowCount === 1 ? 'item is' : 'items are'} below the alert level. Check each message, copy it, and paste it into WhatsApp or Telegram.`}
        </p>
        {lowCount > 0 && (
          <p className="muted">Quantities are suggestions to bring stock back to twice the alert level. Change any of them.</p>
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
          onSetUpVendors={() => navigate('/admin/ops/setup')}
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
  onSetUpVendors: () => void;
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
    <section aria-labelledby={headingId} className="ops-approve">
      <div className="chg">
        <div className="top">
          <div>
            <h2 id={headingId}>{vendor ? vendor.name : 'Unassigned'}</h2>
            {vendor ? (
              <VendorPhone vendor={vendor} canEdit={isOwner} />
            ) : (
              <p className="muted">
                No usual vendor set.{' '}
                {isOwner && (
                  <button type="button" onClick={onSetUpVendors} className="linkish">Set vendors in Setup</button>
                )}
              </p>
            )}
          </div>
          <span className="muted">
            {lines.length} of {group.items.length} {group.items.length === 1 ? 'item' : 'items'}
          </span>
        </div>

        <ul className="ops-order-lines">
          {group.items.map(item => {
            const included = !left.has(item.id);
            const presence = item.count_mode === 'presence';
            const checkboxId = `order-include-${item.id}`;
            return (
              <li key={item.id}>
                <input id={checkboxId} type="checkbox" checked={included} onChange={() => onToggle(item.id)} />
                <label htmlFor={checkboxId} className={included ? undefined : 'left-out'}>
                  <span className="nm">{item.name}</span>
                  <span className="muted">
                    {presence ? 'Out' : `${formatQty(item.current_quantity)} ${unitFor(item.unit, Number(item.current_quantity))} left · alert below ${formatQty(item.min_threshold)}`}
                  </span>
                </label>
                {!presence && (
                  <span className="qty">
                    <input
                      inputMode="decimal"
                      value={quantityText(item)}
                      disabled={!included}
                      onChange={event => onQuantity(item.id, event.target.value)}
                      aria-label={`How much ${item.name} to order`}
                    />
                    <span className="muted">{unitFor(item.unit, parseOrderQuantity(quantityText(item)) ?? 2)}</span>
                  </span>
                )}
              </li>
            );
          })}
        </ul>

        <div className="ops-msg">
          <pre ref={messageRef} aria-label={`Message to ${vendor?.name ?? 'an unassigned vendor'}`}>{message}</pre>
          <button type="button" className="btn ghost" onClick={copy} disabled={lines.length === 0}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
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
      <form className="ops-actions" onSubmit={event => { event.preventDefault(); save(); }}>
        <label htmlFor={inputId} className="sr-only">Phone for {vendor.name}</label>
        <input id={inputId} type="tel" value={value} onChange={event => setValue(event.target.value)} autoFocus />
        <button type="submit" className="btn" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
        <button type="button" className="btn ghost" onClick={() => setEditing(false)}>Cancel</button>
      </form>
    );
  }
  return (
    <p className="muted">
      {vendor.phone ? <span className="phone">{vendor.phone}</span> : 'No phone saved'}
      {canEdit && (
        <>{' '}<button type="button" onClick={() => setEditing(true)} className="linkish">
          {vendor.phone ? 'Change' : 'Add phone'}
        </button></>
      )}
    </p>
  );
}
