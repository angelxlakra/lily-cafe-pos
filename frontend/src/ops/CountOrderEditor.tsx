/**
 * CountOrderEditor (owner only, ops look)
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
import { ArrowDown, ArrowUp, DotsSixVertical } from '@phosphor-icons/react';
import { inventoryApi } from '../api/inventory';
import { describeApiError } from '../utils/apiError';

type Row = { id: number; name: string; detail?: string };

// Lists only move up and down.
const restrictToVerticalAxis: Modifier = ({ transform }) => ({ ...transform, x: 0 });

export default function CountOrderEditor({ onDone }: { onDone?: () => void }) {
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
    <div>
      {(openGroup || onDone) && (
        <div className="ops-actions" style={{ margin: '0 0 8px' }}>
          {openGroup && <button type="button" onClick={() => setOpenCategoryId(null)} className="btn ghost">All categories</button>}
          {onDone && <button type="button" onClick={onDone} className="btn ghost">Done</button>}
        </div>
      )}
      <p className="muted" style={{ margin: 0 }}>
        {openGroup
          ? `${openGroup.category?.name ?? 'Uncategorized'}: the order these items appear in during the nightly count.`
          : 'Match the walk through the storeroom. Drag by the handle or use the arrows. Changes save straight away.'}
      </p>

      {isLoading && <p className="muted">Loading…</p>}

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
                className="text-btn"
                aria-label={`Arrange items in ${row.name}`}
              >
                Items
              </button>
            )}
          />
          {uncategorized && (
            <ul className="su-list">
              <li>
                <div className="su-line" style={{ paddingLeft: 12 }}>
                  <div className="who">
                    <span className="nm">Uncategorized</span>
                    <span className="muted">Always counted last</span>
                  </div>
                  <button type="button" onClick={() => setOpenCategoryId(0)} className="text-btn" aria-label="Arrange uncategorized items">
                    Items
                  </button>
                </div>
              </li>
            </ul>
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
      <div className="su-saved" aria-live="polite">
        {mutation.isPending && <span className="muted">Saving…</span>}
        {mutation.isError && (
          <span className="bad">
            Order not saved. {describeApiError(mutation.error)}{' '}
            <button type="button" className="text-btn" onClick={() => mutation.mutate(order.map(row => row.id))}>
              Try again
            </button>
          </span>
        )}
        {mutation.isSuccess && <span className="muted">Saved</span>}
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} modifiers={[restrictToVerticalAxis]} onDragEnd={onDragEnd}>
        <SortableContext items={order.map(row => row.id)} strategy={verticalListSortingStrategy}>
          <ol className="su-list su-order" style={{ margin: 0 }} aria-label={`Count order of ${label}`}>
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
      className={isDragging ? 'drag' : undefined}
    >
      <button
        type="button"
        ref={setActivatorNodeRef}
        {...attributes}
        {...listeners}
        aria-label={`Move ${row.name}, position ${position}`}
        className="su-grip"
      >
        <DotsSixVertical size={20} weight="bold" aria-hidden />
      </button>
      <div className="who">
        <span className="nm">{row.name}</span>
        {row.detail && <span className="muted">{row.detail}</span>}
      </div>
      {trailing}
      <button type="button" onClick={onUp} disabled={isFirst} aria-label={`Move ${row.name} up`} className="su-move">
        <ArrowUp size={18} weight="bold" aria-hidden />
      </button>
      <button type="button" onClick={onDown} disabled={isLast} aria-label={`Move ${row.name} down`} className="su-move">
        <ArrowDown size={18} weight="bold" aria-hidden />
      </button>
    </li>
  );
}
