import { AnimatedLink } from '@/components/skiper/animated-link'
import { timeAgo } from '@/lib/format'

const NAV = [
  { href: '#watchlist', label: 'Watchlist' },
  { href: '#for-you', label: 'For you' },
  { href: '#how', label: 'How it works' },
]

export function Header({ checkedAt }: { checkedAt: string | null }) {
  const stale = !checkedAt || Date.now() - new Date(checkedAt).getTime() > 36 * 3600 * 1000
  return (
    <header className="glass fixed inset-x-0 top-0 z-40 border-x-0 border-t-0">
      <div className="container-page flex h-14 items-center justify-between gap-4">
        <a href="#top" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-7 place-items-center rounded-lg bg-deal/15 text-deal ring-1 ring-deal/30">
            <svg viewBox="0 0 32 32" className="size-4" aria-hidden="true">
              <path d="M7 17.5 14 24l11-15" stroke="currentColor" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          Price Checker
        </a>
        <nav aria-label="Sections" className="hidden items-center gap-6 text-sm text-muted-foreground sm:flex">
          {NAV.map((n) => (
            <AnimatedLink key={n.href} href={n.href} className="hover:text-foreground">
              {n.label}
            </AnimatedLink>
          ))}
        </nav>
        <span
          className="flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground"
          title={checkedAt ? new Date(checkedAt).toLocaleString('en-GB') : 'No check has run yet'}
        >
          <span className={`size-1.5 rounded-full ${stale ? 'bg-hot' : 'bg-deal'} shadow-[0_0_8px_currentColor]`} />
          Checked {timeAgo(checkedAt)}
        </span>
      </div>
    </header>
  )
}
