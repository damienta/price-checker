import { motion, useReducedMotion } from 'framer-motion'
import { ArrowDown } from 'lucide-react'

import Aurora from '@/components/Aurora'
import BlurText from '@/components/BlurText'
import { Button } from '@/components/ui/button'
import { money } from '@/lib/format'

export type HeroStats = {
  tracking: number
  belowTarget: number
  saving: number | null
  deals: number
}

export function Hero({ stats }: { stats: HeroStats }) {
  const reduce = useReducedMotion()
  const tiles = [
    { label: 'Items tracked', value: String(stats.tracking) },
    { label: 'Below target', value: String(stats.belowTarget), accent: stats.belowTarget > 0 },
    { label: 'Saving vs full price', value: stats.saving ? money(stats.saving) : '—' },
    { label: 'Deals for you', value: String(stats.deals) },
  ]

  return (
    <section id="top" className="relative overflow-hidden pt-32 pb-16 sm:pt-40 sm:pb-24">
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-55 [mask-image:linear-gradient(to_bottom,black_30%,transparent)]">
        <Aurora colorStops={['#1a2e05', '#a3e635', '#0e7490']} amplitude={0.9} blend={0.6} speed={0.6} />
      </div>
      <div className="pointer-events-none absolute inset-0 -z-20 bg-dots [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />

      <div className="container-page">
        <p className="mb-4 text-sm font-medium tracking-wide text-deal">UK prices · checked every morning</p>
        <BlurText
          text="The best price, without the tabs."
          animateBy="words"
          delay={90}
          className="max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-6xl"
        />
        <motion.p
          className="mt-6 max-w-xl text-lg text-muted-foreground"
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          PriceSpy, PriceRunner, retailers and HotUKDeals, checked at 8am and double-checked by Claude.
          The result lands in Discord and here.
        </motion.p>
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75, duration: 0.5 }}
          className="mt-8"
        >
          <Button asChild size="lg" className="rounded-full">
            <a href="#watchlist">
              See today's prices <ArrowDown className="size-4" />
            </a>
          </Button>
        </motion.div>

        <dl className="mt-14 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {tiles.map((t, i) => (
            <motion.div
              key={t.label}
              className="glass rounded-2xl px-4 py-4"
              initial={reduce ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.85 + i * 0.07, duration: 0.5 }}
            >
              <dt className="text-xs text-muted-foreground">{t.label}</dt>
              <dd className={`price mt-1 text-2xl font-semibold ${t.accent ? 'text-deal' : ''}`}>{t.value}</dd>
            </motion.div>
          ))}
        </dl>
      </div>
    </section>
  )
}
