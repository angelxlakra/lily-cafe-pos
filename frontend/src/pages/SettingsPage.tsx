// frontend/src/pages/SettingsPage.tsx
import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Gear } from '@phosphor-icons/react'
import { useSettings, useUpdateSettings } from '../api/settings'
import type { Settings } from '../api/settings'

// ============================================================================
// Constants
// ============================================================================

const TIMEZONES = [
  'Asia/Kolkata',
  'Asia/Dubai',
  'Asia/Singapore',
  'Asia/Tokyo',
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Australia/Sydney',
  'UTC',
]

// ============================================================================
// Small reusable components
// ============================================================================

interface FieldProps {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  step?: string
  placeholder?: string
  hint?: string
}

function Field({ label, value, onChange, type = 'text', step, placeholder, hint }: FieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-neutral-text-dark mb-1">{label}</label>
      <input
        type={type}
        step={step}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-neutral-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-coffee-brown/30 focus:border-coffee-brown bg-white"
      />
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </div>
  )
}

interface SaveButtonProps {
  onClick: () => void
  isPending: boolean
}

function SaveButton({ onClick, isPending }: SaveButtonProps) {
  return (
    <div className="pt-2">
      <button
        type="button"
        onClick={onClick}
        disabled={isPending}
        className="btn bg-coffee-brown text-white hover:bg-coffee-dark disabled:opacity-50 disabled:cursor-not-allowed px-6"
      >
        {isPending ? 'Saving…' : 'Save'}
      </button>
    </div>
  )
}

interface SectionProps {
  title: string
  children: React.ReactNode
}

function Section({ title, children }: SectionProps) {
  return (
    <section className="bg-white rounded-lg border border-neutral-border p-6 space-y-4">
      <h2 className="text-base font-semibold text-coffee-brown border-b border-neutral-border pb-2">
        {title}
      </h2>
      {children}
    </section>
  )
}

// ============================================================================
// Main page
// ============================================================================

export default function SettingsPage() {
  const { data: settings, isLoading, isError } = useSettings()
  const updateMutation = useUpdateSettings()

  // Section-level form state — each section saves independently
  const [restaurant, setRestaurant] = useState<Settings>({})
  const [appConfig, setAppConfig] = useState<Settings>({})
  const [receipt, setReceipt] = useState<Settings>({})
  const [smtp, setSmtp] = useState<Settings>({})

  // Initialise form state when settings load
  useEffect(() => {
    if (!settings) return
    setRestaurant({
      'restaurant.name': settings['restaurant.name'] ?? '',
      'restaurant.address_line1': settings['restaurant.address_line1'] ?? '',
      'restaurant.address_line2': settings['restaurant.address_line2'] ?? '',
      'restaurant.phone': settings['restaurant.phone'] ?? '',
      'restaurant.email': settings['restaurant.email'] ?? '',
      'restaurant.gstin': settings['restaurant.gstin'] ?? '',
      'restaurant.fssai': settings['restaurant.fssai'] ?? '',
    })
    setAppConfig({
      'app.max_tables': settings['app.max_tables'] ?? '15',
      'app.gst_rate': settings['app.gst_rate'] ?? '5.0',
      'app.timezone': settings['app.timezone'] ?? 'Asia/Kolkata',
      'app.token_expiry_hours': settings['app.token_expiry_hours'] ?? '24',
    })
    setReceipt({
      'receipt.paper_size': settings['receipt.paper_size'] ?? '80mm',
      'receipt.google_review_url': settings['receipt.google_review_url'] ?? '',
      'receipt.feedback_form_url': settings['receipt.feedback_form_url'] ?? '',
    })
    setSmtp({
      'smtp.enabled': settings['smtp.enabled'] ?? 'false',
      'smtp.host': settings['smtp.host'] ?? 'smtp.gmail.com',
      'smtp.port': settings['smtp.port'] ?? '587',
      'smtp.username': settings['smtp.username'] ?? '',
      'smtp.sender_email': settings['smtp.sender_email'] ?? '',
      'smtp.report_emails': settings['smtp.report_emails'] ?? '',
    })
  }, [settings])

  const save = async (sectionSettings: Settings, sectionName: string) => {
    try {
      await updateMutation.mutateAsync(sectionSettings)
      toast.success(`${sectionName} saved`)
    } catch {
      toast.error(`Failed to save ${sectionName}`)
    }
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <p className="text-muted">Loading settings…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-8">
        <p className="text-error">Failed to load settings. Please refresh.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <Gear size={28} weight="duotone" className="text-coffee-brown" />
        <h1 className="font-heading text-2xl text-coffee-brown">Settings</h1>
      </div>

      {/* Restaurant Info */}
      <Section title="Restaurant Info">
        <div className="space-y-3">
          <Field
            label="Restaurant Name"
            value={restaurant['restaurant.name'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.name': v }))}
          />
          <Field
            label="Address Line 1"
            value={restaurant['restaurant.address_line1'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.address_line1': v }))}
          />
          <Field
            label="Address Line 2"
            value={restaurant['restaurant.address_line2'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.address_line2': v }))}
          />
          <Field
            label="Phone"
            value={restaurant['restaurant.phone'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.phone': v }))}
          />
          <Field
            label="Email"
            value={restaurant['restaurant.email'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.email': v }))}
            type="email"
          />
          <Field
            label="GSTIN"
            value={restaurant['restaurant.gstin'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.gstin': v }))}
          />
          <Field
            label="FSSAI"
            value={restaurant['restaurant.fssai'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.fssai': v }))}
          />
        </div>
        <SaveButton onClick={() => save(restaurant, 'Restaurant Info')} isPending={updateMutation.isPending} />
      </Section>

      {/* App Config */}
      <Section title="App Config">
        <div className="space-y-3">
          <Field
            label="Max Tables"
            value={appConfig['app.max_tables'] ?? '15'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.max_tables': v }))}
            type="number"
          />
          <Field
            label="GST Rate (%)"
            value={appConfig['app.gst_rate'] ?? '5.0'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.gst_rate': v }))}
            type="number"
            step="0.5"
          />
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-1">Timezone</label>
            <select
              value={appConfig['app.timezone'] ?? 'Asia/Kolkata'}
              onChange={(e) => setAppConfig((s) => ({ ...s, 'app.timezone': e.target.value }))}
              className="w-full border border-neutral-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-coffee-brown/30 focus:border-coffee-brown bg-white"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Token Expiry (hours)"
            value={appConfig['app.token_expiry_hours'] ?? '24'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.token_expiry_hours': v }))}
            type="number"
            hint="How long login sessions last before requiring re-authentication"
          />
        </div>
        <SaveButton onClick={() => save(appConfig, 'App Config')} isPending={updateMutation.isPending} />
      </Section>

      {/* Receipt */}
      <Section title="Receipt">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-2">Paper Size</label>
            <div className="flex gap-2">
              {['58mm', '80mm'].map((size) => (
                <button
                  key={size}
                  type="button"
                  onClick={() => setReceipt((s) => ({ ...s, 'receipt.paper_size': size }))}
                  className={`px-5 py-2 rounded-md text-sm font-medium border transition-colors ${
                    receipt['receipt.paper_size'] === size
                      ? 'bg-coffee-brown text-white border-coffee-brown'
                      : 'bg-white text-neutral-text-dark border-neutral-border hover:border-coffee-brown'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
          <Field
            label="Google Review URL"
            value={receipt['receipt.google_review_url'] ?? ''}
            onChange={(v) => setReceipt((s) => ({ ...s, 'receipt.google_review_url': v }))}
            placeholder="https://g.page/r/your-business-review"
            hint="Printed as a QR code on receipts"
          />
          <Field
            label="Feedback Form URL"
            value={receipt['receipt.feedback_form_url'] ?? ''}
            onChange={(v) => setReceipt((s) => ({ ...s, 'receipt.feedback_form_url': v }))}
            placeholder="https://forms.gle/your-form-id"
            hint="Printed as a QR code on receipts"
          />
        </div>
        <SaveButton onClick={() => save(receipt, 'Receipt')} isPending={updateMutation.isPending} />
      </Section>

      {/* Email / SMTP */}
      <Section title="Email / SMTP">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="smtp-enabled"
              checked={smtp['smtp.enabled'] === 'true'}
              onChange={(e) =>
                setSmtp((s) => ({ ...s, 'smtp.enabled': e.target.checked ? 'true' : 'false' }))
              }
              className="w-4 h-4 accent-coffee-brown"
            />
            <label htmlFor="smtp-enabled" className="text-sm font-medium text-neutral-text-dark">
              Enable email sending (inventory reports)
            </label>
          </div>
          <Field
            label="SMTP Host"
            value={smtp['smtp.host'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.host': v }))}
            placeholder="smtp.gmail.com"
          />
          <Field
            label="SMTP Port"
            value={smtp['smtp.port'] ?? '587'}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.port': v }))}
            type="number"
          />
          <Field
            label="Username"
            value={smtp['smtp.username'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.username': v }))}
            placeholder="your@email.com"
          />
          <Field
            label="Sender Email"
            value={smtp['smtp.sender_email'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.sender_email': v }))}
            type="email"
            placeholder="noreply@lilycafe.com"
          />
          <Field
            label="Report Recipients"
            value={smtp['smtp.report_emails'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.report_emails': v }))}
            placeholder="owner@email.com,manager@email.com"
            hint="Comma-separated email addresses for inventory reports"
          />
          <p className="text-xs text-muted bg-neutral-background rounded p-2">
            SMTP password is set via the <code>SMTP_PASSWORD</code> environment variable on the server.
          </p>
        </div>
        <SaveButton onClick={() => save(smtp, 'Email / SMTP')} isPending={updateMutation.isPending} />
      </Section>
    </div>
  )
}
