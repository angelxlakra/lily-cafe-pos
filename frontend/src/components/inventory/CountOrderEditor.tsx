/**
 * CountOrderEditor (owner only)
 *
 * Sets the order the nightly count walks through: categories first, then
 * the items inside each. Drag by the handle, or use the arrows (keyboard
 * and screen readers). Every move saves straight away.
 */

import { useEffect, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type Modifier,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ArrowDown, ArrowLeft, ArrowUp, CaretRight, DotsSixVertical } from '@phosphor-icons/react';
import { inventoryApi } from '../../api/inventory';
import LoadingSpinner from '../LoadingSpinner';
import { describeApiError } from '../../utils/apiError';

type Row = { id: number; name: string; detail?: string };

// Lists only move up and down.
const restrictToVerticalAxis: Modifier = ({ transform }) => ({ ...transform, x: 0 });

export default function CountOrderEditor({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient();
  const { data: groups, isLoading } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });
  const [openCategoryId, setOpenCategoryId] = useState<number | null>(null);

  const categoryGroups = groups?.filter(group => group.category) ?? [];
  const uncategorized = groups?.find(group => !group.category);
  const openGroup =
    openCategoryId === 0 ? uncategorized : categoryGroups.find(group => group.category!.id === openCategoryId);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['inventory'] });

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          {openGroup ? (
            <button
              type="button"
              onClick={() => setOpenCategoryId(null)}
              className="-ml-2 h-12 px-2 inline-flex items-center gap-1.5 rounded-lg font-medium text-coffee-brown hover:bg-cream/60"
            >
              <ArrowLeft size={18} weight="bold" aria-hidden /> All categories
            </button>
          ) : null}
          <h2 className="font-heading text-2xl! text-neutral-text-dark">
            {openGroup ? openGroup.category?.name ?? 'Uncategorized' : 'Count order'}
          </h2>
          <p className="mt-1 text-sm text-neutral-text-muted">
            {openGroup
              ? 'The order these items appear in during the nightly count.'
              : 'Match the walk through the storeroom. Drag by the handle or use the arrows. Changes save straight away.'}
          </p>
        </div>
        <button type="button" onClick={onDone} className="btn-secondary shrink-0">Done</button>
      </div>

      {isLoading && (
        <div className="py-10 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading…</div>
      )}

      {groups && !openGroup && (
        <>
          <SortableList
            key="categories"
            label="categories"
            rows={categoryGroups.map(group => ({
              id: group.category!.id,
              name: group.category!.name,
              detail: `${group.items.length} item${group.items.length === 1 ? '' : 's'}`,
            }))}
            save={inventoryApi.reorderCategories}
            onSaved={refresh}
            trailing={row => (
              <button
                type="button"
                onClick={() => setOpenCategoryId(row.id)}
                className="h-12 px-3 inline-flex items-center gap-1 rounded-lg text-sm font-medium text-coffee-brown hover:bg-cream/60"
                aria-label={`Arrange items in ${row.name}`}
              >
                Items <CaretRight size={14} weight="bold" aria-hidden />
              </button>
            )}
          />
          {uncategorized && (
            <div className="card px-4 py-3 flex items-center justify-between gap-3">
              <div>
                <div className="font-medium text-neutral-text-dark">Uncategorized</div>
                <div className="text-xs text-neutral-text-muted">Always counted last</div>
              </div>
              <button
                type="button"
                onClick={() => setOpenCategoryId(0)}
                className="h-12 px-3 inline-flex items-center gap-1 rounded-lg text-sm font-medium text-coffee-brown hover:bg-cream/60"
              >
                Items <CaretRight size={14} weight="bold" aria-hidden />
              </button>
            </div>
          )}
        </>
      )}

      {openGroup && (
        <SortableList
          key={`items-${openCategoryId}`}
          label="items"
          rows={openGroup.items.map(item => ({ id: item.id, name: item.name, detail: item.unit }))}
          save={inventoryApi.reorderItems}
          onSaved={refresh}
        />
      )}
    </div>
  );
}

function SortableList({
  label, rows, save, onSaved, trailing,
}: {
  label: string;
  rows: Row[];
  save: (ids: number[]) => Promise<void>;
  onSaved: () => void;
  trailing?: (row: Row) => ReactNode;
}) {
  const [order, setOrder] = useState(rows);
  // Adopt fresh server data when the rows themselves change.
  const rowKey = rows.map(row => row.id).join(',');
  useEffect(() => setOrder(rows), [rowKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Saves run one at a time, so quick taps can't land out of order and
  // leave an older arrangement on the server.
  const mutation = useMutation({ mutationFn: save, onSuccess: onSaved, scope: { id: `count-order-${label}` } });
  const move = (from: number, to: number) => {
    if (to < 0 || to >= order.length || from === to) return;
    const next = arrayMove(order, from, to);
    setOrder(next);
    mutation.mutate(next.map(row => row.id));
  };

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over) return;
    move(order.findIndex(row => row.id === active.id), order.findIndex(row => row.id === over.id));
  };

  return (
    <div>
      <div className="h-6 text-sm" aria-live="polite">
        {mutation.isPending && <span className="text-neutral-text-muted">Saving…</span>}
        {mutation.isError && (
          <span className="text-error">
            Order not saved. {describeApiError(mutation.error)}{' '}
            <button type="button" className="underline font-medium" onClick={() => mutation.mutate(order.map(row => row.id))}>
              Try again
            </button>
          </span>
        )}
        {mutation.isSuccess && <span className="text-neutral-text-muted">Saved</span>}
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} modifiers={[restrictToVerticalAxis]} onDragEnd={onDragEnd}>
        <SortableContext items={order.map(row => row.id)} strategy={verticalListSortingStrategy}>
          <ol className="card divide-y divide-neutral-border overflow-hidden" aria-label={`Count order of ${label}`}>
            {order.map((row, index) => (
              <SortableRow
                key={row.id}
                row={row}
                position={index + 1}
                isFirst={index === 0}
                isLast={index === order.length - 1}
                onUp={() => move(index, index - 1)}
                onDown={() => move(index, index + 1)}
                trailing={trailing?.(row)}
              />
            ))}
          </ol>
        </SortableContext>
      </DndContext>
    </div>
  );
}

function SortableRow({
  row, position, isFirst, isLast, onUp, onDown, trailing,
}: {
  row: Row;
  position: number;
  isFirst: boolean;
  isLast: boolean;
  onUp: () => void;
  onDown: () => void;
  trailing?: ReactNode;
}) {
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } =
    useSortable({ id: row.id });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={`relative flex items-center gap-1 pr-2 bg-off-white ${isDragging ? 'z-10 shadow-medium' : ''}`}
    >
      <button
        type="button"
        ref={setActivatorNodeRef}
        {...attributes}
        {...listeners}
        aria-label={`Move ${row.name}, position ${position}`}
        className="size-12 shrink-0 grid place-items-center text-neutral-text-muted cursor-grab active:cursor-grabbing touch-none"
      >
        <DotsSixVertical size={20} weight="bold" aria-hidden />
      </button>
      <div className="flex-1 min-w-0 py-2">
        <div className="font-medium leading-snug text-neutral-text-dark line-clamp-2 break-words">{row.name}</div>
        {row.detail && <div className="text-xs text-neutral-text-muted">{row.detail}</div>}
      </div>
      {trailing}
      <button
        type="button"
        onClick={onUp}
        disabled={isFirst}
        aria-label={`Move ${row.name} up`}
        className="size-12 shrink-0 grid place-items-center rounded-lg text-coffee-brown hover:bg-cream/60 disabled:opacity-30 disabled:hover:bg-transparent"
      >
        <ArrowUp size={18} weight="bold" aria-hidden />
      </button>
      <button
        type="button"
        onClick={onDown}
        disabled={isLast}
        aria-label={`Move ${row.name} down`}
        className="size-12 shrink-0 grid place-items-center rounded-lg text-coffee-brown hover:bg-cream/60 disabled:opacity-30 disabled:hover:bg-transparent"
      >
        <ArrowDown size={18} weight="bold" aria-hidden />
      </button>
    </li>
  );
}
