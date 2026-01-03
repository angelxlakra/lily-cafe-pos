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

const quickFilters: QuickFilter[] = [
  {
    label: 'Today',
    getRange: () => {
      const today = new Date().toISOString().split('T')[0]
      return { start: today, end: today }
    },
  },
  {
    label: 'Yesterday',
    getRange: () => {
      const date = new Date()
      date.setDate(date.getDate() - 1)
      const yesterday = date.toISOString().split('T')[0]
      return { start: yesterday, end: yesterday }
    },
  },
  {
    label: 'This Week',
    getRange: () => {
      const date = new Date()
      // Adjust to Monday
      const day = date.getDay()
      const diff = date.getDate() - day + (day === 0 ? -6 : 1)
      const start = new Date(date)
      start.setDate(diff)
      
      const today = new Date().toISOString().split('T')[0]
      return { 
        start: start.toISOString().split('T')[0], 
        end: today 
      }
    },
  },
  {
    label: 'This Month',
    getRange: () => {
      const date = new Date()
      const today = date.toISOString().split('T')[0]
      
      date.setDate(1)
      return { 
        start: date.toISOString().split('T')[0], 
        end: today 
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
  const handleQuickFilter = (filter: QuickFilter) => {
    const { start, end } = filter.getRange()
    onChange(start, end)
  }

  // Check if current selection matches a quick filter
  const activeFilterLabel = quickFilters.find(filter => {
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
              onChange={(e) => onChange(e.target.value, endDate < e.target.value ? e.target.value : endDate)}
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
              onChange={(e) => onChange(startDate > e.target.value ? e.target.value : startDate, e.target.value)}
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
