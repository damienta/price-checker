// Shapes of the files the Python side writes to data/. Keep in sync with
// src/price_checker/{models,store,feed}.py.

export type Offer = {
  item_id: string
  source: string
  price: number
  url: string
  seller: string
  title: string
  in_stock: boolean | null
  condition: string
  currency: string
  kind: 'price' | 'deal'
  posted_at: string
  /** From data/shops.json. Older data has no value. */
  trust?: 'trusted' | 'unverified' | 'blocked'
}

export type CheckError = { item_id: string; source: string; reason: string; url: string }

export type WatchItem = {
  id: string
  name: string
  target_price: number | null
  condition: string
  keywords: string[]
  urls: string[]
  hotukdeals_tags: string[]
  added: string
  notes: string
}

export type LatestEntry = {
  name: string
  target_price: number | null
  checked_at: string
  best: Offer | null
  previous_best: Offer | null
  previous_checked_at: string | null
  offers: Offer[]
  errors: CheckError[]
}

export type Latest = { checked_at: string | null; items: Record<string, LatestEntry> }

export type HistoryRow = {
  checked_at: string
  item_id: string
  source: string
  seller: string
  price: number
  condition: string
  in_stock: string
  kind: string
  trust: string
}

export type FeedDeal = {
  id: string
  title: string
  url: string
  price: number | null
  merchant: string
  category: string
  image: string
  posted_at: string
  temperature: number | null
  score: number
  reasons: string[]
  feeds: string[]
  watchlist_item: string
}

export type Feed = {
  generated_at: string
  interests: { tags: string[]; categories: string[]; keywords: string[] }
  deals: FeedDeal[]
}
