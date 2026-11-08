import { motion, useReducedMotion } from 'framer-motion'

import { money } from '@/lib/format'

/** Best price per check over time, with the target as a dashed line. */
export function Sparkline({
  points,
  target,
  className,
}: {
  points: { at: string; price: number }[]
  target: number | null
  className?: string
}) {
  const reduce = useReducedMotion()
  const width = 240
  const height = 56
  const pad = 4

  if (points.length < 2) {
    return (
      <div className={`flex h-14 items-center text-xs text-muted-foreground ${className ?? ''}`}>
        A price chart appears after a few daily checks.
      </div>
    )
  }

  const prices = points.map((p) => p.price)
  const values = target != null ? [...prices, target] : prices
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const x = (i: number) => pad + (i / (points.length - 1)) * (width - pad * 2)
  const y = (v: number) => pad + (1 - (v - min) / span) * (height - pad * 2)
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join(' ')
  const area = `${line} L${x(points.length - 1)},${height} L${x(0)},${height} Z`
  const last = points[points.length - 1]
  const low = Math.min(...prices)

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label={`Price history: from ${money(points[0].price)} to ${money(last.price)}, lowest ${money(low)}`}
    >
      <defs>
        <linearGradient id="spark-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="var(--deal)" stopOpacity="0.25" />
          <stop offset="100%" stopColor="var(--deal)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {target != null && (
        <line
          x1={pad}
          x2={width - pad}
          y1={y(target)}
          y2={y(target)}
          stroke="var(--deal)"
          strokeOpacity="0.45"
          strokeDasharray="3 4"
        />
      )}
      <path d={area} fill="url(#spark-fill)" />
      <motion.path
        d={line}
        fill="none"
        stroke="var(--deal)"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={reduce ? false : { pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
      />
      <circle cx={x(points.length - 1)} cy={y(last.price)} r="3" fill="var(--deal)" />
    </svg>
  )
}
