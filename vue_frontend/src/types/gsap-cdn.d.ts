/** Ambient types for CDN-loaded GSAP (no npm `gsap` dependency). */

declare module 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/index.js' {
  const gsap: GsapCdn.GsapCore
  export default gsap
  export { gsap }
}

declare module 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/ScrollTrigger.js' {
  export const ScrollTrigger: GsapCdn.ScrollTriggerStatic
  export default ScrollTrigger
}

declare module 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/SplitText.js' {
  export const SplitText: GsapCdn.SplitTextStatic
  export default SplitText
}

declare namespace GsapCdn {
  interface TweenVars {
    [key: string]: unknown
    duration?: number
    ease?: string
    stagger?: number
    onComplete?: () => void
    willChange?: string
    force3D?: boolean
    scrollTrigger?: {
      trigger?: Element
      start?: string
      once?: boolean
      fastScrollEnd?: boolean
      anticipatePin?: number
    }
  }

  interface Tween {
    kill: () => void
    pause: () => void
    resume: () => void
    paused: (value?: boolean) => boolean
  }

  interface GsapCore {
    registerPlugin: (...plugins: unknown[]) => void
    fromTo: (
      targets: Element | Element[] | unknown,
      from: Record<string, unknown>,
      to: TweenVars,
    ) => Tween
  }

  interface ScrollTriggerInstance {
    trigger?: Element | null
    kill: () => void
  }

  interface ScrollTriggerStatic {
    getAll: () => ScrollTriggerInstance[]
  }

  interface SplitTextInstance {
    chars: Element[]
    words: Element[]
    lines: Element[]
    revert: () => void
  }

  interface SplitTextConfig {
    type?: string
    smartWrap?: boolean
    autoSplit?: boolean
    linesClass?: string
    wordsClass?: string
    charsClass?: string
    reduceWhiteSpace?: boolean
    onSplit?: (self: SplitTextInstance) => Tween | void
  }

  interface SplitTextStatic {
    new (target: Element, config: SplitTextConfig): SplitTextInstance
  }

  interface GsapBundle {
    gsap: GsapCore
    ScrollTrigger: ScrollTriggerStatic
    SplitText: SplitTextStatic
  }
}
