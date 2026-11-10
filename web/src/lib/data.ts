import { useEffect, useState } from 'react'

import type { Feed, HistoryRow, Latest, WatchItem } from './types'

/**
 * In dev the Vite server serves ../data at /data. In production the site reads the files
 * straight from the repo on GitHub, so it's up to date as soon as a workflow commits,
 * without redeploying the site. GitHub caches raw files for about five minutes.
 */
const DATA_BASE = import.meta.env.DEV
  ? '/data'
  : 'https://raw.githubusercontent.com/damienta/price-checker/main/data'

async function get(file: string): Promise<Response | null> {
  const res = await fetch(`${DATA_BASE}/${file}`, { cache: 'no-cache' })
  return res.ok ? res : null
}

export type SiteData = {
  watchlist: WatchItem[]
  latest: Latest
  history: HistoryRow[]
  feed: Feed | null
}

export async function loadAll(): Promise<SiteData> {
  const [watchlist, latest, history, feed] = await Promise.all([
    get('watchlist.json').then((r) => (r ? r.json() : { items: [] })),
    get('latest.json').then((r) => (r ? r.json() : { checked_at: null, items: {} })),
    get('history.csv').then((r) => (r ? r.text() : '')),
    get('feed.json').then((r) => (r ? r.json() : null)),
  ])
  return { watchlist: watchlist.items, latest, history: parseHistory(history), feed }
}

export function useSiteData() {
  const [data, setData] = useState<SiteData | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    loadAll().then(setData, (e: unknown) => setError(String(e)))
  }, [])
  return { data, error }
}

/** CSV written by Python's csv module: fields may be quoted, with "" for a literal quote. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        field += '"'
        i++
      } else if (c === '"') {
        quoted = false
      } else {
        field += c
      }
    } else if (c === '"') {
      quoted = true
    } else if (c === ',') {
      row.push(field)
      field = ''
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++
      row.push(field)
      if (row.some((f) => f !== '')) rows.push(row)
      row = []
      field = ''
    } else {
      field += c
    }
  }
  if (field !== '' || row.length) {
    row.push(field)
    rows.push(row)
  }
  return rows
}

function parseHistory(text: string): HistoryRow[] {
  const [header, ...rows] = parseCsv(text)
  if (!header) return []
  const col = (name: string) => header.indexOf(name)
  const value = (r: string[], name: string) => (col(name) >= 0 ? (r[col(name)] ?? '') : '')
  return rows.map((r) => ({
    checked_at: value(r, 'checked_at'),
    item_id: value(r, 'item_id'),
    source: value(r, 'source'),
    seller: value(r, 'seller'),
    price: Number(value(r, 'price')),
    condition: value(r, 'condition'),
    in_stock: value(r, 'in_stock'),
    kind: value(r, 'kind'),
    trust: value(r, 'trust'),
  }))
}

/** Best acceptable price per check, oldest first, for the sparkline. */
export function priceSeries(history: HistoryRow[], itemId: string): { at: string; price: number }[] {
  const best = new Map<string, number>()
  for (const row of history) {
    if (row.item_id !== itemId || row.in_stock === 'false' || row.condition !== 'new') continue
    // Blocked shops never count. Older "lowest of N shops" rows hid which shop it was, so skip them.
    if (row.trust === 'blocked' || row.seller.startsWith('cheapest of')) continue
    if (!Number.isFinite(row.price)) continue
    const current = best.get(row.checked_at)
    if (current === undefined || row.price < current) best.set(row.checked_at, row.price)
  }
  return [...best.entries()].map(([at, price]) => ({ at, price })).sort((a, b) => a.at.localeCompare(b.at))
}
