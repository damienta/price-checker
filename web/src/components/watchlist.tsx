import { AlertTriangle, ArrowDownRight, ArrowUpRight, Target } from 'lucide-react'

import SpotlightCard from '@/components/SpotlightCard'
import { AddItemButton } from '@/components/add-item'
import { Reveal, RevealItem } from '@/components/motion/reveal'
import { AnimatedLink } from '@/components/skiper/animated-link'
import { Sparkline } from '@/components/sparkline'
import { priceSeries } from '@/lib/data'
import { money, shop, timeAgo, via } from '@/lib/format'
import type { HistoryRow, LatestEntry, WatchItem } from '@/lib/types'

export function Watchlist({
  items,
  latest,
  history,
}: {
  items: WatchItem[]
  latest: Record<string, LatestEntry>
  history: HistoryRow[]
}) {
  return (
    <section id="watchlist" className="py-16 sm:py-24">
      <div className="container-page">
        <SectionTitle eyebrow="Watchlist" title="Today's best prices" aside={<AddItemButton />} />
        {items.length === 0 ? (
          <Empty>Nothing tracked yet. Use "Add item", or ask Claude Code in the repo to track something.</Empty>
        ) : (
          <Reveal className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <RevealItem key={item.id} className="h-full">
                <ItemCard item={item} entry={latest[item.id]} history={history} />
              </RevealItem>
            ))}
          </Reveal>
        )}
      </div>
    </section>
  )
}

function ItemCard({ item, entry, history }: { item: WatchItem; entry?: LatestEntry; history: HistoryRow[] }) {
  const best = entry?.best ?? null
  const previous = entry?.previous_best ?? null
  const target = item.target_price
  const below = best != null && target != null && best.price <= target
  const change = best && previous ? best.price - previous.price : 0
  const offers = (entry?.offers ?? []).filter((o) => o.kind === 'price').slice(0, 6)
  const errors = entry?.errors ?? []
  const toGo = best && target != null && !below ? best.price - target : null

  return (
    <SpotlightCard
      className={`flex h-full flex-col gap-5 !rounded-2xl !p-6 ${below ? '!border-deal/40' : '!border-white/8'} !bg-card`}
      spotlightColor={below ? 'rgba(163, 230, 53, 0.14)' : 'rgba(103, 232, 249, 0.1)'}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold leading-snug">{item.name}</h3>
          {item.notes && <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{item.notes}</p>}
        </div>
        <Status below={below} change={change} hasBest={best != null} />
      </div>

      <div>
        <div className="price text-4xl font-semibold">{money(best?.price)}</div>
        {best ? (
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
            <AnimatedLink href={best.url} external className="font-medium">
              {shop(best.source, best.seller)}
            </AnimatedLink>
            <TrustBadge trust={best.trust} />
            {via(best.source, best.seller) && (
              <span className="text-xs text-muted-foreground">via {via(best.source, best.seller)}</span>
            )}
          </div>
        ) : (
          <p className="mt-1 text-sm text-muted-foreground">No price found yet</p>
        )}
      </div>

      {target != null && (
        <div className="flex items-center gap-2 text-sm">
          <Target className="size-4 text-muted-foreground" aria-hidden="true" />
          <span className="text-muted-foreground">Target</span>
          <span className="price">{money(target)}</span>
          {toGo != null && <span className="ml-auto price text-muted-foreground">{money(toGo)} to go</span>}
          {below && <span className="ml-auto text-deal">Buy window</span>}
        </div>
      )}

      <Sparkline points={priceSeries(history, item.id)} target={target} className="h-14 w-full" />

      {offers.length > 0 && (
        <ul className="space-y-1.5 border-t border-border pt-4 text-sm">
          {offers.map((o) => {
            const blocked = o.trust === 'blocked'
            const isBest = best != null && o.price === best.price && o.seller === best.seller && o.source === best.source
            return (
              <li
                key={`${o.source}-${o.seller}-${o.price}`}
                className={`flex items-center justify-between gap-3 ${blocked ? 'opacity-50' : ''}`}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <AnimatedLink
                    href={o.url}
                    external
                    className={`truncate text-muted-foreground hover:text-foreground ${blocked ? 'line-through' : ''}`}
                  >
                    {shop(o.source, o.seller)}
                  </AnimatedLink>
                  <TrustBadge trust={o.trust} compact />
                </span>
                <span className={`price shrink-0 ${isBest ? 'text-foreground' : 'text-muted-foreground'} ${blocked ? 'line-through' : ''}`}>
                  {money(o.price)}
                </span>
              </li>
            )
          })}
        </ul>
      )}

      <div className="mt-auto flex items-center justify-between gap-2 text-xs text-muted-foreground">
        <span>Checked {timeAgo(entry?.checked_at)}</span>
        {errors.length > 0 && (
          <span className="flex items-center gap-1 text-hot" title={errors.map((e) => `${e.source}: ${e.reason}`).join('\n')}>
            <AlertTriangle className="size-3.5" aria-hidden="true" />
            {errors.length} couldn't be checked
          </span>
        )}
      </div>
    </SpotlightCard>
  )
}

const TRUST_COPY = {
  blocked: { label: 'Blocked', title: 'On your blocked list in data/shops.json. Never counted as the best price.', cls: 'bg-destructive/10 text-destructive' },
  unverified: { label: 'Unverified', title: "Not on your trusted list. Check the seller's reviews before buying.", cls: 'bg-hot/10 text-hot' },
} as const

function TrustBadge({ trust, compact = false }: { trust?: string; compact?: boolean }) {
  if (trust !== 'blocked' && trust !== 'unverified') return null
  const copy = TRUST_COPY[trust]
  return (
    <span
      title={copy.title}
      className={`shrink-0 rounded-full font-medium ${copy.cls} ${compact ? 'px-1.5 text-[10px]' : 'px-2 py-0.5 text-[11px]'}`}
    >
      {copy.label}
    </span>
  )
}

function Status({ below, change, hasBest }: { below: boolean; change: number; hasBest: boolean }) {
  const base = 'flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium'
  if (below) return <span className={`${base} bg-deal/15 text-deal`}>Below target</span>
  if (change <= -0.01)
    return (
      <span className={`${base} bg-deal/10 text-deal`}>
        <ArrowDownRight className="size-3.5" aria-hidden="true" />
        <span className="price">{money(-change)}</span>
      </span>
    )
  if (change >= 0.01)
    return (
      <span className={`${base} bg-destructive/10 text-destructive`}>
        <ArrowUpRight className="size-3.5" aria-hidden="true" />
        <span className="price">{money(change)}</span>
      </span>
    )
  return <span className={`${base} bg-white/5 text-muted-foreground`}>{hasBest ? 'Watching' : 'New'}</span>
}

export function SectionTitle({ eyebrow, title, aside }: { eyebrow: string; title: string; aside?: React.ReactNode }) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-deal">{eyebrow}</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h2>
      </div>
      {aside}
    </div>
  )
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="glass rounded-2xl p-8 text-center text-muted-foreground">{children}</div>
}
