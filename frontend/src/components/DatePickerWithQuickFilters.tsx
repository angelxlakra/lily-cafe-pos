import { useState } from 'react'
import { Calendar, ArrowRight } from '@phosphor-icons/react'

interface DatePickerWithQuickFiltersProps {
  startDate: string
  endDate: string
  onChange: (start: string, end: string) => void
  max?: string
}

type QuickFilter = {
  label: string
  getRange: () => { start: string; end: string }
}

const getLocalYYYYMMDD = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const quickFilters: QuickFilter[] = [
  {
    label: 'Today',
    getRange: () => {
      const today = new Date()
      const dateStr = getLocalYYYYMMDD(today)
      return { start: dateStr, end: dateStr }
    },
  },
  {
    label: 'Yesterday',
    getRange: () => {
      const date = new Date()
      date.setDate(date.getDate() - 1)
      const yesterday = getLocalYYYYMMDD(date)
      return { start: yesterday, end: yesterday }
    },
  },
  {
    label: 'This Week',
    getRange: () => {
      const today = new Date()
      const dayOfWeek = today.getDay()

      // Calculate days to subtract to get to Monday
      // If Sunday (0), go back 6 days; otherwise go back (dayOfWeek - 1) days
      const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1

      const start = new Date(today)
      start.setDate(today.getDate() - daysToSubtract)

      return {
        start: getLocalYYYYMMDD(start),
        end: getLocalYYYYMMDD(today)
      }
    },
  },
  {
    label: 'This Month',
    getRange: () => {
      const date = new Date()
      const end = getLocalYYYYMMDD(date)
      
      date.setDate(1)
      return { 
        start: getLocalYYYYMMDD(date), 
        end: end
      }
    },
  },
  {
    label: 'All Time',
    getRange: () => {
      const end = new Date()
      const start = new Date(end)
      // Default to last 3 months as per requirement ("whichever is lower")
      start.setMonth(start.getMonth() - 3)
      
      return { 
        start: getLocalYYYYMMDD(start), 
        end: getLocalYYYYMMDD(end)
      }
    },
  },
]

/**
 * Date picker with quick filter buttons
 * Provides easy access to common date selections including ranges
 */
export default function DatePickerWithQuickFilters({
  startDate,
  endDate,
  onChange,
  max,
}: DatePickerWithQuickFiltersProps) {
  const [activeFilter, setActiveFilter] = useState<string | null>(null)

  const handleQuickFilter = (filter: QuickFilter) => {
    const { start, end } = filter.getRange()
    setActiveFilter(filter.label)
    onChange(start, end)
  }

  const handleManualDateChange = (start: string, end: string) => {
    setActiveFilter(null)
    onChange(start, end)
  }

  // Check if current selection matches a quick filter (only if no active filter is set)
  const activeFilterLabel = activeFilter || quickFilters.find(filter => {
    const { start, end } = filter.getRange()
    return start === startDate && end === endDate
  })?.label

  return (
    <div className="space-y-3">
      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        {quickFilters.map((filter) => (
          <button
            key={filter.label}
            onClick={() => handleQuickFilter(filter)}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200
              ${
                activeFilterLabel === filter.label
                  ? 'bg-coffee-brown text-cream shadow-md'
                  : 'bg-white dark:bg-neutral-800 text-neutral-text-dark dark:text-neutral-text-light border border-neutral-border dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-700'
              }
            `}
            type="button"
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Date Inputs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-sm font-medium text-neutral-text-dark dark:text-neutral-text-light whitespace-nowrap min-w-[3rem]">
            From:
          </span>
          <div className="relative flex-1 sm:max-w-[160px]">
            <Calendar
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-light pointer-events-none"
              aria-hidden="true"
            />
            <input
              type="date"
              value={startDate}
              onChange={(e) => handleManualDateChange(e.target.value, endDate < e.target.value ? e.target.value : endDate)}
              max={max}
              className="
                w-full pl-9 pr-3 py-2
                border border-neutral-border dark:border-neutral-700
                rounded-lg
                bg-white dark:bg-neutral-800
                text-neutral-text-dark dark:text-neutral-text-light
                text-sm
                focus:outline-none focus:ring-2 focus:ring-coffee-brown
                transition-all
              "
              aria-label="Start Date"
            />
          </div>
        </div>

        <div className="hidden sm:block text-neutral-text-light">
          <ArrowRight size={16} />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-sm font-medium text-neutral-text-dark dark:text-neutral-text-light whitespace-nowrap min-w-[3rem] sm:hidden">
            To:
          </span>
          <div className="relative flex-1 sm:max-w-[160px]">
             <Calendar
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-light pointer-events-none"
              aria-hidden="true"
            />
            <input
              type="date"
              value={endDate}
              onChange={(e) => handleManualDateChange(startDate > e.target.value ? e.target.value : startDate, e.target.value)}
              max={max}
              min={startDate}
              className="
                w-full pl-9 pr-3 py-2
                border border-neutral-border dark:border-neutral-700
                rounded-lg
                bg-white dark:bg-neutral-800
                text-neutral-text-dark dark:text-neutral-text-light
                text-sm
                focus:outline-none focus:ring-2 focus:ring-coffee-brown
                transition-all
              "
              aria-label="End Date"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
