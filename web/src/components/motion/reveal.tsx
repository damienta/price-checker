import { motion, useReducedMotion, type Variants } from 'framer-motion'
import type { ComponentProps, ReactNode } from 'react'

import { useInViewOnce } from '@/hooks/use-in-view-once'

const EASE = [0.22, 1, 0.36, 1] as const

/**
 * Stagger container: watches itself with IntersectionObserver and, on first
 * entry, cascades its <RevealItem> children in. Plays once per page load.
 */
export function Reveal({
  children,
  className,
  stagger = 0.08,
  delay = 0,
  as = 'div',
}: {
  children: ReactNode
  className?: string
  stagger?: number
  delay?: number
  as?: 'div' | 'ul' | 'ol'
}) {
  const { ref, inView } = useInViewOnce<HTMLDivElement>()
  const reduce = useReducedMotion()
  const MotionTag = motion[as] as typeof motion.div

  const variants: Variants = {
    hidden: {},
    show: {
      transition: reduce ? {} : { staggerChildren: stagger, delayChildren: delay },
    },
  }

  return (
    <MotionTag
      ref={ref}
      className={className}
      variants={variants}
      initial="hidden"
      animate={inView ? 'show' : 'hidden'}
    >
      {children}
    </MotionTag>
  )
}

type RevealItemProps = ComponentProps<typeof motion.div> & { y?: number }

/** Child of <Reveal>: fades and lifts into place. Reduced-motion users get a plain, quick fade. */
export function RevealItem({ y = 24, children, ...props }: RevealItemProps) {
  const reduce = useReducedMotion()
  const variants: Variants = reduce
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.2 } } }
    : { hidden: { opacity: 0, y }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } } }

  return (
    <motion.div variants={variants} {...props}>
      {children}
    </motion.div>
  )
}

export function RevealLi({ y = 24, children, ...props }: ComponentProps<typeof motion.li> & { y?: number }) {
  const reduce = useReducedMotion()
  const variants: Variants = reduce
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.2 } } }
    : { hidden: { opacity: 0, y }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } } }

  return (
    <motion.li variants={variants} {...props}>
      {children}
    </motion.li>
  )
}
