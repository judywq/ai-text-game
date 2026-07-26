<script setup lang="ts">
/**
 * Vue port of React Bits SplitText (GSAP SplitText + fromTo stagger).
 * GSAP is loaded from CDN on first animate — not an npm dependency.
 */
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { loadGsapCdn } from '@/composables/loadGsapCdn'

type SplitType = 'chars' | 'words' | 'lines' | 'words, chars' | string
type GsapVars = Record<string, unknown>

const props = withDefaults(
  defineProps<{
    text?: string
    className?: string
    delay?: number
    duration?: number
    ease?: string
    splitType?: SplitType
    from?: GsapVars
    to?: GsapVars
    threshold?: number
    rootMargin?: string
    textAlign?: string
    tag?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p'
    /** When true, wait for scroll into view (React Bits default). When false, animate on mount. */
    scrollTrigger?: boolean
  }>(),
  {
    text: '',
    className: '',
    delay: 50,
    duration: 1.25,
    ease: 'power3.out',
    splitType: 'chars',
    from: () => ({ opacity: 0, y: 40 }),
    to: () => ({ opacity: 1, y: 0 }),
    threshold: 0.1,
    rootMargin: '-100px',
    textAlign: 'left',
    tag: 'p',
    scrollTrigger: false,
  },
)

const emit = defineEmits<{
  letterAnimationComplete: []
  loadStart: []
  loadError: [message: string]
}>()

const elRef = ref<HTMLElement | null>(null)
const fontsLoaded = ref(false)

type SplitHost = HTMLElement & { _rbsplitInstance?: GsapCdn.SplitTextInstance | null }

let cleanupFn: (() => void) | null = null
let animationCompleted = false
let runId = 0
let activeTween: GsapCdn.Tween | null = null
const isPaused = ref(false)

function killAnimation() {
  cleanupFn?.()
  cleanupFn = null
  animationCompleted = false
  activeTween = null
  isPaused.value = false
}

function pause() {
  if (!activeTween || animationCompleted) return
  activeTween.pause()
  isPaused.value = true
}

function resume() {
  if (!activeTween || animationCompleted) return
  activeTween.resume()
  isPaused.value = false
}

function togglePause() {
  if (isPaused.value) resume()
  else pause()
}

function buildScrollStart(): string {
  const startPct = (1 - props.threshold) * 100
  const marginMatch = /^(-?\d+(?:\.\d+)?)(px|em|rem|%)?$/.exec(props.rootMargin)
  const marginValue = marginMatch ? parseFloat(marginMatch[1]) : 0
  const marginUnit = marginMatch ? marginMatch[2] || 'px' : 'px'
  const sign =
    marginValue === 0
      ? ''
      : marginValue < 0
        ? `-=${Math.abs(marginValue)}${marginUnit}`
        : `+=${marginValue}${marginUnit}`
  return `top ${startPct}%${sign}`
}

function assignTargets(self: GsapCdn.SplitTextInstance): Element[] {
  let targets: Element[] | undefined
  if (props.splitType.includes('chars') && self.chars.length) targets = self.chars
  if (!targets && props.splitType.includes('words') && self.words.length) targets = self.words
  if (!targets && props.splitType.includes('lines') && self.lines.length) targets = self.lines
  if (!targets) targets = self.chars || self.words || self.lines
  return targets
}

async function runAnimation() {
  const thisRun = ++runId
  killAnimation()
  await nextTick()

  const el = elRef.value as SplitHost | null
  if (!el || !props.text || !fontsLoaded.value) return
  if (animationCompleted) return

  emit('loadStart')

  let bundle: GsapCdn.GsapBundle
  try {
    bundle = await loadGsapCdn()
  } catch (err) {
    if (thisRun !== runId) return
    const message = err instanceof Error ? err.message : 'Failed to load GSAP from CDN'
    emit('loadError', message)
    return
  }

  if (thisRun !== runId) return

  const { gsap, ScrollTrigger, SplitText: GSAPSplitText } = bundle

  if (el._rbsplitInstance) {
    try {
      el._rbsplitInstance.revert()
    } catch {
      /* noop */
    }
    el._rbsplitInstance = null
  }

  const start = buildScrollStart()

  const splitInstance = new GSAPSplitText(el, {
    type: props.splitType,
    smartWrap: true,
    autoSplit: props.splitType === 'lines',
    linesClass: 'split-line',
    wordsClass: 'split-word',
    charsClass: 'split-char',
    reduceWhiteSpace: false,
    onSplit: (self) => {
      const targets = assignTargets(self)
      const tweenVars: GsapCdn.TweenVars = {
        ...props.to,
        duration: props.duration,
        ease: props.ease,
        stagger: props.delay / 1000,
        onComplete: () => {
          animationCompleted = true
          activeTween = null
          isPaused.value = false
          emit('letterAnimationComplete')
        },
        willChange: 'transform, opacity',
        force3D: true,
      }

      if (props.scrollTrigger) {
        tweenVars.scrollTrigger = {
          trigger: el,
          start,
          once: true,
          fastScrollEnd: true,
          anticipatePin: 0.4,
        }
      }

      const tween = gsap.fromTo(targets, { ...props.from }, tweenVars)
      activeTween = tween
      isPaused.value = false
      return tween
    },
  })

  el._rbsplitInstance = splitInstance

  cleanupFn = () => {
    ScrollTrigger.getAll().forEach((st) => {
      if (st.trigger === el) st.kill()
    })
    try {
      splitInstance.revert()
    } catch {
      /* noop */
    }
    el._rbsplitInstance = null
  }
}

if (typeof document !== 'undefined') {
  if (document.fonts.status === 'loaded') {
    fontsLoaded.value = true
  } else {
    document.fonts.ready.then(() => {
      fontsLoaded.value = true
    })
  }
}

watch(
  () =>
    [
      props.text,
      props.delay,
      props.duration,
      props.ease,
      props.splitType,
      JSON.stringify(props.from),
      JSON.stringify(props.to),
      props.threshold,
      props.rootMargin,
      props.scrollTrigger,
      fontsLoaded.value,
    ] as const,
  () => {
    void runAnimation()
  },
  { immediate: true },
)

onUnmounted(() => {
  runId += 1
  killAnimation()
})

const tagStyle = computed(() => ({
  textAlign: props.textAlign as 'left' | 'center' | 'right' | 'justify',
  overflow: 'hidden',
  display: 'inline-block',
  whiteSpace: 'normal' as const,
  wordWrap: 'break-word' as const,
  willChange: 'transform, opacity',
}))

defineExpose({
  replay: runAnimation,
  kill: killAnimation,
  pause,
  resume,
  togglePause,
  isPaused,
})
</script>

<template>
  <component
    :is="tag"
    ref="elRef"
    class="split-parent"
    :class="className"
    :style="tagStyle"
  >
    {{ text }}
  </component>
</template>
