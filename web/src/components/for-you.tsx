import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Flame, Star } from 'lucide-react'
import { useMemo, useState } from 'react'

import { AnimatedLink } from '@/components/skiper/animated-link'
import { Empty, SectionTitle } from '@/components/watchlist'
import { money, timeAgo } from '@/lib/format'
import type { Feed, FeedDeal } from '@/lib/types'

const ALL = 'All'
const WATCHLIST = 'Watchlist'

export function ForYou({ feed }: { feed: Feed | null }) {
  const [filter, setFilter] = useState(ALL)
  const deals = useMemo(() => feed?.deals ?? [], [feed])

  const filters = useMemo(() => {
    const counts = new Map<string, number>()
    for (const d of deals) if (d.category) counts.set(d.category, (counts.get(d.category) ?? 0) + 1)
    const categories = [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([c]) => c)
    return [ALL, ...(deals.some((d) => d.watchlist_item) ? [WATCHLIST] : []), ...categories]
  }, [deals])

  const shown = deals.filter(
    (d) => filter === ALL || (filter === WATCHLIST ? d.watchlist_item : d.category === filter),
  )

  return (
    <section id="for-you" className="py-16 sm:py-24">
      <div className="container-page">
        <SectionTitle
          eyebrow="For you"
          title="On HotUKDeals right now"
          aside={
            feed && (
              <p className="text-sm text-muted-foreground">
                Updated {timeAgo(feed.generated_at)} · following {feed.interests.tags.join(', ') || 'nothing yet'}
              </p>
            )
          }
        />
        {!feed ? (
          <Empty>The feed appears after the "For you feed" workflow first runs.</Empty>
        ) : (
          <>
            <div
              className="-mx-4 mb-8 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0"
              role="tablist"
              aria-label="Filter deals"
            >
              {filters.map((f) => (
                <button
                  key={f}
                  role="tab"
                  aria-selected={filter === f}
                  onClick={() => setFilter(f)}
                  className={`relative shrink-0 rounded-full px-3.5 py-1.5 text-sm whitespace-nowrap transition-colors ${
                    filter === f ? 'text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {filter === f && (
                    <motion.span
                      layoutId="filter-pill"
                      className="absolute inset-0 rounded-full bg-primary"
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.45 }}
                    />
                  )}
                  <span className="relative">{f}</span>
                </button>
              ))}
            </div>
            <motion.ul layout className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              <AnimatePresence mode="popLayout">
                {shown.map((deal, i) => (
                  <DealCard key={deal.id} deal={deal} index={i} />
                ))}
              </AnimatePresence>
            </motion.ul>
          </>
        )}
      </div>
    </section>
  )
}

function DealCard({ deal, index }: { deal: FeedDeal; index: number }) {
  const reduce = useReducedMotion()
  const hot = (deal.temperature ?? 0) >= 100
  return (
    <motion.li
      layout
      initial={reduce ? false : { opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.35, delay: reduce ? 0 : Math.min(index, 12) * 0.03 }}
      className="group glass flex flex-col overflow-hidden rounded-2xl transition-[border-color,transform] duration-300 hover:-translate-y-0.5 hover:border-white/20"
    >
      <a href={deal.url} target="_blank" rel="noopener noreferrer" className="relative block aspect-[4/3] overflow-hidden bg-white">
        {deal.image ? (
          <img
            src={deal.image}
            alt=""
            loading="lazy"
            className="size-full object-contain p-4 transition-transform duration-500 group-hover:scale-105"
          />
        ) : null}
        {deal.temperature != null && (
          <span
            className={`absolute top-3 left-3 flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold backdrop-blur ${
              hot ? 'bg-hot/90 text-black' : 'bg-black/70 text-white'
            }`}
          >
            <Flame className="size-3.5" aria-hidden="true" />
            {deal.temperature}°
          </span>
        )}
        {deal.watchlist_item && (
          <span className="absolute top-3 right-3 flex items-center gap-1 rounded-full bg-deal px-2 py-0.5 text-xs font-semibold text-black">
            <Star className="size-3" aria-hidden="true" /> Watchlist
          </span>
        )}
      </a>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="price text-xl font-semibold">{deal.price != null ? money(deal.price) : 'See deal'}</span>
          <span className="truncate text-xs text-muted-foreground">{deal.merchant}</span>
        </div>
        <AnimatedLink href={deal.url} external showArrow={false} className="line-clamp-2 text-sm leading-snug">
          {deal.title}
        </AnimatedLink>
        <div className="mt-auto flex flex-wrap gap-1.5 pt-1">
          {deal.reasons.slice(0, 2).map((r) => (
            <span key={r} className="rounded-full bg-white/5 px-2 py-0.5 text-[11px] text-muted-foreground">
              {r}
            </span>
          ))}
          <span className="ml-auto text-[11px] text-muted-foreground">{timeAgo(deal.posted_at)}</span>
        </div>
      </div>
    </motion.li>
  )
}
