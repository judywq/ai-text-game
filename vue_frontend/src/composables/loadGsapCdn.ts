/**
 * Lazy-load GSAP (+ ScrollTrigger, SplitText) from a pinned CDN.
 * Cached so Replay does not re-fetch. Not an npm dependency.
 */

const GSAP_VERSION = '3.15.0'
const GSAP_CORE_URL = `https://cdn.jsdelivr.net/npm/gsap@${GSAP_VERSION}/index.js`
const GSAP_SCROLL_URL = `https://cdn.jsdelivr.net/npm/gsap@${GSAP_VERSION}/ScrollTrigger.js`
const GSAP_SPLIT_URL = `https://cdn.jsdelivr.net/npm/gsap@${GSAP_VERSION}/SplitText.js`

let loadPromise: Promise<GsapCdn.GsapBundle> | null = null

export function loadGsapCdn(): Promise<GsapCdn.GsapBundle> {
  if (!loadPromise) {
    loadPromise = (async () => {
      const [coreMod, scrollMod, splitMod] = await Promise.all([
        import(/* @vite-ignore */ GSAP_CORE_URL),
        import(/* @vite-ignore */ GSAP_SCROLL_URL),
        import(/* @vite-ignore */ GSAP_SPLIT_URL),
      ])

      const gsap = (coreMod.gsap ?? coreMod.default) as GsapCdn.GsapCore
      const ScrollTrigger = (scrollMod.ScrollTrigger ??
        scrollMod.default) as GsapCdn.ScrollTriggerStatic
      const SplitText = (splitMod.SplitText ?? splitMod.default) as GsapCdn.SplitTextStatic

      gsap.registerPlugin(ScrollTrigger, SplitText)

      return { gsap, ScrollTrigger, SplitText }
    })().catch((err) => {
      // Allow retry on next Play after a failed fetch
      loadPromise = null
      throw err
    })
  }

  return loadPromise
}

export function resetGsapCdnCacheForTests() {
  loadPromise = null
}
