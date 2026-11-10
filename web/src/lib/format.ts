const gbp = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })

export function money(value: number | null | undefined): string {
  return value == null ? '—' : gbp.format(value)
}

export function timeAgo(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return 'never'
  const minutes = Math.round((now - new Date(iso).getTime()) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return days === 1 ? 'yesterday' : `${days} days ago`
}

/** The shop you'd buy from: the seller a comparison site names, otherwise the site itself. */
export function shop(source: string, seller: string): string {
  if (!seller || seller.startsWith('cheapest of')) return source
  return seller
}

/** "PriceSpy" when the shop came from a comparison site, otherwise null. */
export function via(source: string, seller: string): string | null {
  const name = shop(source, seller)
  return name.toLowerCase() === source.toLowerCase() ? null : source
}
