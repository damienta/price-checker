import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Plus, X } from 'lucide-react'
import { useEffect, useId, useRef, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const REPO = 'https://github.com/damienta/price-checker'

/**
 * The site is static, so it can't write to the watchlist itself. The form opens a pre-filled
 * GitHub issue instead; .github/workflows/track.yml adds the item, checks its price, replies on
 * the issue and closes it. Only issues opened by the repo owner are acted on.
 */
export function issueUrl(fields: { name: string; links: string; target: string; notes: string }) {
  const params = new URLSearchParams({
    template: 'track.yml',
    title: `Track: ${fields.name}`,
    name: fields.name,
  })
  if (fields.links.trim()) params.set('links', fields.links.trim())
  if (fields.target.trim()) params.set('target', fields.target.trim().replace(/^£/, ''))
  if (fields.notes.trim()) params.set('notes', fields.notes.trim())
  return `${REPO}/issues/new?${params}`
}

export function AddItemButton({ className, size = 'default' }: { className?: string; size?: 'default' | 'sm' }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button size={size} className={`rounded-full ${className ?? ''}`} onClick={() => setOpen(true)}>
        <Plus className="size-4" aria-hidden="true" /> Add item
      </Button>
      <AnimatePresence>{open && <AddItemDialog onClose={() => setOpen(false)} />}</AnimatePresence>
    </>
  )
}

function AddItemDialog({ onClose }: { onClose: () => void }) {
  const reduce = useReducedMotion()
  const titleId = useId()
  const firstField = useRef<HTMLInputElement>(null)
  const [fields, setFields] = useState({ name: '', links: '', target: '', notes: '' })
  const set = (key: keyof typeof fields) => (e: { target: { value: string } }) =>
    setFields((f) => ({ ...f, [key]: e.target.value }))

  useEffect(() => {
    firstField.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
    }
  }, [onClose])

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!fields.name.trim()) return
    window.open(issueUrl(fields), '_blank', 'noopener')
    onClose()
  }

  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="glass w-full max-w-md rounded-2xl bg-popover p-6"
        initial={reduce ? false : { opacity: 0, y: 16, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={reduce ? { opacity: 0 } : { opacity: 0, y: 8, scale: 0.98 }}
        transition={{ type: 'spring', bounce: 0.15, duration: 0.4 }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId} className="text-lg font-semibold">
              Track something new
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Opens a GitHub issue to confirm. It's added and price-checked within a minute or two.
            </p>
          </div>
          <button onClick={onClose} aria-label="Close" className="rounded-md p-1 text-muted-foreground hover:text-foreground">
            <X className="size-5" />
          </button>
        </div>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <Field label="Product" hint="Exact name, with the model number if it has one">
            <Input
              ref={firstField}
              required
              value={fields.name}
              onChange={set('name')}
              placeholder="Apple AirPods Pro 3"
              className="input-field"
            />
          </Field>
          <Field label="Links" hint="Optional. PriceSpy, PriceRunner or shop pages, one per line">
            <textarea
              value={fields.links}
              onChange={set('links')}
              rows={3}
              placeholder="https://pricespy.co.uk/product.php?p=..."
              className="input-field w-full rounded-md border px-3 py-2 text-sm"
            />
          </Field>
          <div className="grid grid-cols-[8rem_1fr] gap-3">
            <Field label="Target (£)">
              <Input inputMode="decimal" value={fields.target} onChange={set('target')} placeholder="160" className="input-field price" />
            </Field>
            <Field label="Notes">
              <Input value={fields.notes} onChange={set('notes')} placeholder="White, USB-C" className="input-field" />
            </Field>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!fields.name.trim()}>
              Continue on GitHub
            </Button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium">{label}</span>
      {children}
      {hint && <span className="block text-xs text-muted-foreground">{hint}</span>}
    </label>
  )
}
