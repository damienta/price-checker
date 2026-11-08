import { Bot, MessageSquare, Search } from 'lucide-react'

import { Reveal, RevealItem } from '@/components/motion/reveal'
import { AnimatedLink } from '@/components/skiper/animated-link'
import { SectionTitle } from '@/components/watchlist'

const STEPS = [
  {
    time: '07:15',
    icon: Bot,
    title: 'Claude double-checks',
    body: 'Searches each item by name, including Amazon and Argos, confirms or disputes yesterday’s prices and adds new links the script can read.',
  },
  {
    time: '08:00',
    icon: Search,
    title: 'The script checks every source',
    body: 'Product pages, PriceSpy, PriceRunner, HotUKDeals, eBay and Google Shopping. Only new, in-stock, matching listings count.',
  },
  {
    time: '08:01',
    icon: MessageSquare,
    title: 'One message in Discord',
    body: 'Below target, cheaper than yesterday, new deals, Claude’s finds and anything that couldn’t be checked.',
  },
]

const SOURCES = [
  { name: 'PriceSpy UK', href: 'https://pricespy.co.uk' },
  { name: 'PriceRunner UK', href: 'https://www.pricerunner.com' },
  { name: 'HotUKDeals', href: 'https://www.hotukdeals.com' },
  { name: 'eBay UK', href: 'https://www.ebay.co.uk' },
  { name: 'Google Shopping', href: 'https://shopping.google.com' },
]

export function HowItWorks() {
  return (
    <section id="how" className="py-16 sm:py-24">
      <div className="container-page">
        <SectionTitle eyebrow="How it works" title="Every morning, on its own" />
        <Reveal className="grid gap-5 md:grid-cols-3">
          {STEPS.map(({ time, icon: Icon, title, body }) => (
            <RevealItem key={time} className="glass rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <span className="grid size-10 place-items-center rounded-xl bg-white/5 text-cool">
                  <Icon className="size-5" aria-hidden="true" />
                </span>
                <span className="price text-sm text-muted-foreground">{time}</span>
              </div>
              <h3 className="mt-5 font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
            </RevealItem>
          ))}
        </Reveal>
        <p className="mt-10 text-sm text-muted-foreground">
          Prices from{' '}
          {SOURCES.map((s, i) => (
            <span key={s.name}>
              <AnimatedLink href={s.href} external className="text-foreground">
                {s.name}
              </AnimatedLink>
              {i < SOURCES.length - 2 ? ', ' : i === SOURCES.length - 2 ? ' and ' : ''}
            </span>
          ))}
          , plus retailer pages. Always check the price in your basket before buying.
        </p>
      </div>
    </section>
  )
}
