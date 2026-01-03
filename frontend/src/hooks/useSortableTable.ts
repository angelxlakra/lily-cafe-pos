import { useState, useMemo } from 'react'

export type SortDirection = 'asc' | 'desc' | null

export interface SortConfig<T> {
  key: keyof T | null
  direction: SortDirection
}

/**
 * Hook for sortable tables
 * Provides sorting logic and state management
 *
 * @example
 * const { sortedData, sortConfig, requestSort, getSortIndicator } = useSortableTable(orders);
 */
export function useSortableTable<T>(
  data: T[],
  defaultSortKey?: keyof T,
  defaultSortDirection: SortDirection = 'desc'
) {
  const [sortConfig, setSortConfig] = useState<SortConfig<T>>({
    key: defaultSortKey || null,
    direction: defaultSortDirection,
  })

  const sortedData = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) {
      return data
    }

    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortConfig.key!]
      const bValue = b[sortConfig.key!]

      // Handle null/undefined values
      if (aValue == null) return 1
      if (bValue == null) return -1

      // Compare values
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })

    return sorted
  }, [data, sortConfig])

  const requestSort = (key: keyof T) => {
    let direction: SortDirection = 'asc'

    // If clicking the same column, cycle through: asc -> desc -> null
    if (sortConfig.key === key) {
      if (sortConfig.direction === 'asc') {
        direction = 'desc'
      } else if (sortConfig.direction === 'desc') {
        direction = null
      }
    }

    setSortConfig({ key, direction })
  }

  const getSortIndicator = (key: keyof T): '↑' | '↓' | '' => {
    if (sortConfig.key !== key) return ''
    if (sortConfig.direction === 'asc') return '↑'
    if (sortConfig.direction === 'desc') return '↓'
    return ''
  }

  const isSorted = (key: keyof T): boolean => {
    return sortConfig.key === key && sortConfig.direction !== null
  }

  return {
    sortedData,
    sortConfig,
    requestSort,
    getSortIndicator,
    isSorted,
  }
}
