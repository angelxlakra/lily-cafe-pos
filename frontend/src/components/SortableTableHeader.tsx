import { CaretUp, CaretDown } from '@phosphor-icons/react'

interface SortableTableHeaderProps<T> {
  label: string
  sortKey: keyof T
  currentSortKey: keyof T | null
  sortDirection: 'asc' | 'desc' | null
  onSort: (key: keyof T) => void
  align?: 'left' | 'center' | 'right'
}

/**
 * Sortable table header component
 * Shows sort indicators and handles click events
 */
export default function SortableTableHeader<T>({
  label,
  sortKey,
  currentSortKey,
  sortDirection,
  onSort,
  align = 'left',
}: SortableTableHeaderProps<T>) {
  const isActive = currentSortKey === sortKey
  const alignmentClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }

  return (
    <th
      className={`
        px-4 py-3 ${alignmentClasses[align]}
        cursor-pointer select-none
        hover:bg-coffee-brown/5 dark:hover:bg-coffee-brown/10
        transition-colors
        group
      `}
      onClick={() => onSort(sortKey)}
    >
      <div className={`flex items-center gap-2 ${align === 'right' ? 'justify-end' : align === 'center' ? 'justify-center' : ''}`}>
        <span
          className={`
            font-semibold text-sm uppercase tracking-wider
            ${isActive ? 'text-coffee-brown dark:text-coffee-brown' : 'text-neutral-text-light dark:text-neutral-text'}
            group-hover:text-coffee-brown dark:group-hover:text-coffee-brown
            transition-colors
          `}
        >
          {label}
        </span>

        {/* Sort Indicators */}
        <div className="flex flex-col -space-y-1">
          <CaretUp
            size={12}
            weight="bold"
            className={`
              transition-colors
              ${isActive && sortDirection === 'asc' ? 'text-coffee-brown' : 'text-neutral-border opacity-30 group-hover:opacity-60'}
            `}
            aria-hidden="true"
          />
          <CaretDown
            size={12}
            weight="bold"
            className={`
              transition-colors
              ${isActive && sortDirection === 'desc' ? 'text-coffee-brown' : 'text-neutral-border opacity-30 group-hover:opacity-60'}
            `}
            aria-hidden="true"
          />
        </div>
      </div>
    </th>
  )
}
