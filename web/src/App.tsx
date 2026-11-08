import { ForYou } from '@/components/for-you'
import { Header } from '@/components/header'
import { Hero, type HeroStats } from '@/components/hero'
import { HowItWorks } from '@/components/how-it-works'
import { ProgressiveBlur } from '@/components/skiper/progressive-blur'
import { AnimatedLink } from '@/components/skiper/animated-link'
import { Watchlist } from '@/components/watchlist'
import { useSiteData, type SiteData } from '@/lib/data'

export default function App() {
  const { data, error } = useSiteData()

  if (error) {
    return (
      <main className="grid min-h-dvh place-items-center p-6 text-center text-muted-foreground">
        Couldn't load the price data. {error}
      </main>
    )
  }
  if (!data) {
    return (
      <main className="grid min-h-dvh place-items-center" aria-busy="true">
        <span className="size-8 animate-spin rounded-full border-2 border-white/10 border-t-deal" />
      </main>
    )
  }

  return (
    <>
      <Header checkedAt={data.latest.checked_at} />
      <main>
        <Hero stats={stats(data)} />
        <Watchlist items={data.watchlist} latest={data.latest.items} history={data.history} />
        <ForYou feed={data.feed} />
        <HowItWorks />
      </main>
      <footer className="border-t border-border py-10 text-sm text-muted-foreground">
        <div className="container-page flex flex-wrap items-center justify-between gap-4">
          <span>Personal project. Prices can change after a check.</span>
          <span className="flex gap-5">
            <AnimatedLink href="https://github.com/damienta/price-checker" external>
              Source on GitHub
            </AnimatedLink>
            <AnimatedLink href="https://skiper-ui.com" external>
              UI pieces from Skiper UI
            </AnimatedLink>
          </span>
        </div>
      </footer>
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 h-24">
        <ProgressiveBlur position="bottom" height="96px" backgroundColor="#06080a" />
      </div>
    </>
  )
}

function stats({ watchlist, latest, feed }: SiteData): HeroStats {
  let belowTarget = 0
  let saving = 0
  for (const item of watchlist) {
    const entry = latest.items[item.id]
    const best = entry?.best
    if (!best) continue
    if (item.target_price != null && best.price <= item.target_price) belowTarget++
    // "Full price" = the dearest new, in-stock listing seen in the same check.
    const dearest = Math.max(...entry.offers.filter((o) => o.kind === 'price' && o.in_stock !== false).map((o) => o.price))
    if (Number.isFinite(dearest) && dearest > best.price) saving += dearest - best.price
  }
  return { tracking: watchlist.length, belowTarget, saving: saving || null, deals: feed?.deals.length ?? 0 }
}
