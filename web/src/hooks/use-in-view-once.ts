import { useEffect, useRef, useState } from 'react'

/**
 * Native IntersectionObserver hook that flips to `true` the first time the
 * element enters the viewport, then disconnects so it never re-triggers.
 * A full page refresh resets it naturally.
 */
export function useInViewOnce<T extends Element>(options?: { threshold?: number; rootMargin?: string }) {
  const ref = useRef<T>(null)
  const [inView, setInView] = useState(false)
  const threshold = options?.threshold ?? 0.15
  const rootMargin = options?.rootMargin ?? '0px 0px -10% 0px'

  useEffect(() => {
    const el = ref.current
    if (!el || inView) return
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true)
      return
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          observer.disconnect()
        }
      },
      { threshold, rootMargin },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [inView, threshold, rootMargin])

  return { ref, inView }
}
