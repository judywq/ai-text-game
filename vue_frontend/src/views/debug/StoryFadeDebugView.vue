<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import SplitText from '@/components/debug/SplitText.vue'
import { loadGsapCdn } from '@/composables/loadGsapCdn'
import { useSimulatedTextStream } from '@/composables/useSimulatedTextStream'

const SAMPLE_TEXT =
  "Because Mia climbed onto Luma's back and trusted the small dragon to carry him across, the bond between them flared brighter than the moon. Luma crouched on the broken edge of the bridge, claws scraping stone, then leapt into the empty air. Wind tore at Mia's sleeves as the river glittered far below. For a heartbeat he was sure they would fall — then the dragon's wings caught, and the night opened like a path."

const INTERVAL_MS = 50

const prefersReducedMotion = ref(false)

/** A · Word fade */
const wordSpeed = ref(50)
const wordFadeMs = ref(280)
const wordAnimOn = ref(true)
const wordFadeDuration = computed(() => `${wordFadeMs.value}ms`)

/** B · Chunk fade */
const chunkSpeed = ref(50)
const chunkFadeMs = ref(280)
const chunkAnimOn = ref(true)
const chunkFadeDuration = computed(() => `${chunkFadeMs.value}ms`)

/** C · Soft trailing fade */
const trailSpeed = ref(50)
const trailChars = ref(24)
const trailStartOpacity = ref(35)
const trailSoftOn = ref(true)
const trailStartOpacityCss = computed(() => `${trailStartOpacity.value}%`)

/** E · Blur to focus */
const blurSpeed = ref(50)
const blurMs = ref(420)
const blurPx = ref(8)
const blurStartOpacity = ref(35)
const blurAnimOn = ref(true)
const blurDuration = computed(() => `${blurMs.value}ms`)
const blurAmount = computed(() => `${blurPx.value}px`)
const blurOpacityCss = computed(() => blurStartOpacity.value / 100)

/** D · GSAP SplitText */
const splitDelayMs = ref(40)
const splitDurationSec = ref(0.6)
const splitY = ref(24)
const splitType = ref<'chars' | 'words'>('chars')
const splitAnimOn = ref(true)
const splitFrom = computed(() =>
  splitAnimOn.value
    ? { opacity: 0, y: splitY.value }
    : { opacity: 1, y: 0 },
)

const {
  revealed: wordRevealed,
  isPlaying: wordPlaying,
  isPaused: wordPaused,
  play: playWord,
  pause: pauseWord,
  resume: resumeWord,
  togglePause: togglePauseWord,
  reset: resetWord,
} = useSimulatedTextStream(SAMPLE_TEXT, { charsPerSecond: wordSpeed })

const {
  revealed: chunkRevealed,
  isPlaying: chunkPlaying,
  isPaused: chunkPaused,
  play: playChunkStream,
  pause: pauseChunk,
  resume: resumeChunk,
  togglePause: togglePauseChunk,
  reset: resetChunkStream,
} = useSimulatedTextStream(SAMPLE_TEXT, { charsPerSecond: chunkSpeed })

const {
  revealed: trailRevealed,
  isPlaying: trailPlaying,
  isPaused: trailPaused,
  play: playTrail,
  pause: pauseTrail,
  resume: resumeTrail,
  togglePause: togglePauseTrail,
  reset: resetTrail,
} = useSimulatedTextStream(SAMPLE_TEXT, { charsPerSecond: trailSpeed })

const {
  revealed: blurRevealed,
  isPlaying: blurPlaying,
  isPaused: blurPaused,
  play: playBlur,
  pause: pauseBlur,
  resume: resumeBlur,
  togglePause: togglePauseBlur,
  reset: resetBlur,
} = useSimulatedTextStream(SAMPLE_TEXT, { charsPerSecond: blurSpeed })

/** Chunk fade: list of flushed pieces that have appeared */
const chunkSpans = ref<{ id: number; text: string }[]>([])
let chunkId = 0
let lastChunkLen = 0

function resetChunkState() {
  chunkSpans.value = []
  chunkId = 0
  lastChunkLen = 0
}

function playChunk() {
  resetChunkState()
  playChunkStream()
}

function resetChunk() {
  resetChunkState()
  resetChunkStream()
}

watch(chunkRevealed, (text) => {
  if (text.length > lastChunkLen) {
    const piece = text.slice(lastChunkLen)
    lastChunkLen = text.length
    if (piece) {
      chunkSpans.value.push({ id: ++chunkId, text: piece })
    }
  } else if (text.length < lastChunkLen) {
    lastChunkLen = text.length
  }
})

/** Soft trail: split into stable prefix + fading tail */
const trailParts = computed(() => {
  const text = trailRevealed.value
  if (!text) return { head: '', tail: '' }
  if (prefersReducedMotion.value || !trailSoftOn.value || text.length <= trailChars.value) {
    return { head: '', tail: text }
  }
  const cut = text.length - trailChars.value
  return { head: text.slice(0, cut), tail: text.slice(cut) }
})

function tokenizeWords(text: string) {
  if (!text) return [] as { id: number; text: string; isSpace: boolean }[]
  const parts = text.split(/(\s+)/)
  const tokens: { id: number; text: string; isSpace: boolean }[] = []
  let offset = 0
  for (const part of parts) {
    if (!part) continue
    tokens.push({
      id: offset,
      text: part,
      isSpace: /^\s+$/.test(part),
    })
    offset += part.length
  }
  return tokens
}

const wordTokens = computed(() => tokenizeWords(wordRevealed.value))
const blurTokens = computed(() => tokenizeWords(blurRevealed.value))

const splitActive = ref(false)
const splitPlayKey = ref(0)
const splitPlaying = ref(false)
const splitLoading = ref(false)
const splitError = ref('')
const splitPaused = ref(false)
const splitTextRef = ref<{
  pause: () => void
  resume: () => void
  togglePause: () => void
  isPaused: { value: boolean }
} | null>(null)

async function playSplit() {
  splitError.value = ''
  splitPlaying.value = true
  splitPaused.value = false
  splitLoading.value = true

  try {
    await loadGsapCdn()
  } catch (err) {
    splitLoading.value = false
    splitPlaying.value = false
    splitActive.value = false
    splitError.value =
      err instanceof Error ? err.message : 'Failed to load GSAP from CDN. Check your network.'
    return
  }

  splitLoading.value = false
  splitActive.value = true
  splitPlayKey.value += 1
}

function resetSplit() {
  splitPlaying.value = false
  splitActive.value = false
  splitLoading.value = false
  splitError.value = ''
  splitPaused.value = false
}

function togglePauseSplit() {
  if (!splitPlaying.value || !splitActive.value) return
  if (splitPaused.value) {
    splitTextRef.value?.resume()
    splitPaused.value = false
  } else {
    splitTextRef.value?.pause()
    splitPaused.value = true
  }
}

function onSplitComplete() {
  splitPlaying.value = false
  splitPaused.value = false
}

function onSplitLoadError(message: string) {
  splitLoading.value = false
  splitPlaying.value = false
  splitActive.value = false
  splitPaused.value = false
  splitError.value = message
}

const anyPlaying = computed(
  () =>
    wordPlaying.value ||
    chunkPlaying.value ||
    trailPlaying.value ||
    blurPlaying.value ||
    splitPlaying.value ||
    splitLoading.value,
)

const anyPaused = computed(
  () =>
    (wordPlaying.value && wordPaused.value) ||
    (chunkPlaying.value && chunkPaused.value) ||
    (trailPlaying.value && trailPaused.value) ||
    (blurPlaying.value && blurPaused.value) ||
    (splitPlaying.value && splitPaused.value),
)

const canPauseAll = computed(() => anyPlaying.value && !splitLoading.value)

function playAll() {
  playWord()
  playChunk()
  playTrail()
  playBlur()
  void playSplit()
}

function pauseAll() {
  if (anyPaused.value) {
    if (wordPaused.value) resumeWord()
    if (chunkPaused.value) resumeChunk()
    if (trailPaused.value) resumeTrail()
    if (blurPaused.value) resumeBlur()
    if (splitPaused.value) {
      splitTextRef.value?.resume()
      splitPaused.value = false
    }
    return
  }

  if (wordPlaying.value && !wordPaused.value) pauseWord()
  if (chunkPlaying.value && !chunkPaused.value) pauseChunk()
  if (trailPlaying.value && !trailPaused.value) pauseTrail()
  if (blurPlaying.value && !blurPaused.value) pauseBlur()
  if (splitPlaying.value && !splitPaused.value) {
    splitTextRef.value?.pause()
    splitPaused.value = true
  }
}

function resetAll() {
  resetWord()
  resetChunk()
  resetTrail()
  resetBlur()
  resetSplit()
}

function setAllStreamSpeeds(value: number) {
  wordSpeed.value = value
  chunkSpeed.value = value
  trailSpeed.value = value
  blurSpeed.value = value
}

const globalSpeed = ref(50)
watch(globalSpeed, (v) => setAllStreamSpeeds(v))

onMounted(() => {
  prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
})
</script>

<template>
  <div class="fade-debug">
    <header class="fade-debug__header">
      <p class="fade-debug__eyebrow">Debug</p>
      <h1 class="fade-debug__title">Story text fade-in</h1>
      <p class="fade-debug__lede">
        Tune each effect below. Global Play runs all panels; each panel also has its own stream speed and animation params.
      </p>

      <div class="fade-debug__controls">
        <button type="button" class="fade-debug__btn" :disabled="splitLoading" @click="playAll">
          {{ anyPlaying ? 'Replay all' : 'Play all' }}
        </button>
        <button
          type="button"
          class="fade-debug__btn fade-debug__btn--ghost"
          :disabled="!canPauseAll"
          @click="pauseAll"
        >
          {{ anyPaused ? 'Resume all' : 'Pause all' }}
        </button>
        <button
          type="button"
          class="fade-debug__btn fade-debug__btn--ghost"
          :disabled="splitLoading"
          @click="resetAll"
        >
          Reset all
        </button>
        <label class="fade-debug__param">
          <span>Sync all stream speeds {{ globalSpeed }} chars/s</span>
          <input v-model.number="globalSpeed" type="range" min="10" max="120" step="5" />
        </label>
        <span class="fade-debug__meta">flush every {{ INTERVAL_MS }}ms</span>
      </div>
    </header>

    <div class="fade-debug__panels">
      <!-- A: Word fade -->
      <section class="fade-debug__panel">
        <div class="fade-debug__panel-head">
          <div>
            <h2 class="fade-debug__panel-title">A · Word fade</h2>
            <p class="fade-debug__panel-desc">
              Each word mounts at opacity 0 and fades in. Spaces stay static.
            </p>
          </div>
          <div class="fade-debug__panel-actions">
            <button type="button" class="fade-debug__btn" @click="playWord">
              {{ wordPlaying ? 'Replay' : 'Play' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="!wordPlaying"
              @click="togglePauseWord"
            >
              {{ wordPaused ? 'Resume' : 'Pause' }}
            </button>
            <button type="button" class="fade-debug__btn fade-debug__btn--ghost" @click="resetWord">
              Reset
            </button>
          </div>
        </div>
        <div class="fade-debug__params">
          <label class="fade-debug__toggle">
            <input v-model="wordAnimOn" type="checkbox" />
            Fade animation
          </label>
          <label class="fade-debug__param">
            <span>Stream {{ wordSpeed }} chars/s</span>
            <input v-model.number="wordSpeed" type="range" min="10" max="120" step="5" />
          </label>
          <label class="fade-debug__param">
            <span>Fade {{ wordFadeMs }}ms</span>
            <input v-model.number="wordFadeMs" type="range" min="50" max="1000" step="10" />
          </label>
        </div>
        <div class="story-prose fade-debug__prose">
          <p class="fade-debug__stream">
            <template v-if="prefersReducedMotion || !wordAnimOn">{{ wordRevealed }}</template>
            <template v-else>
              <span
                v-for="token in wordTokens"
                :key="token.id"
                :class="token.isSpace ? 'fade-word--space' : 'fade-word'"
              >{{ token.text }}</span>
            </template>
          </p>
        </div>
      </section>

      <!-- B: Chunk fade -->
      <section class="fade-debug__panel">
        <div class="fade-debug__panel-head">
          <div>
            <h2 class="fade-debug__panel-title">B · Chunk fade</h2>
            <p class="fade-debug__panel-desc">
              Each flushed stream chunk fades in as a unit.
            </p>
          </div>
          <div class="fade-debug__panel-actions">
            <button type="button" class="fade-debug__btn" @click="playChunk">
              {{ chunkPlaying ? 'Replay' : 'Play' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="!chunkPlaying"
              @click="togglePauseChunk"
            >
              {{ chunkPaused ? 'Resume' : 'Pause' }}
            </button>
            <button type="button" class="fade-debug__btn fade-debug__btn--ghost" @click="resetChunk">
              Reset
            </button>
          </div>
        </div>
        <div class="fade-debug__params">
          <label class="fade-debug__toggle">
            <input v-model="chunkAnimOn" type="checkbox" />
            Fade animation
          </label>
          <label class="fade-debug__param">
            <span>Stream {{ chunkSpeed }} chars/s</span>
            <input v-model.number="chunkSpeed" type="range" min="10" max="120" step="5" />
          </label>
          <label class="fade-debug__param">
            <span>Fade {{ chunkFadeMs }}ms</span>
            <input v-model.number="chunkFadeMs" type="range" min="50" max="1000" step="10" />
          </label>
        </div>
        <div class="story-prose fade-debug__prose">
          <p class="fade-debug__stream">
            <template v-if="prefersReducedMotion || !chunkAnimOn">{{ chunkRevealed }}</template>
            <template v-else>
              <span
                v-for="chunk in chunkSpans"
                :key="chunk.id"
                class="fade-chunk"
              >{{ chunk.text }}</span>
            </template>
          </p>
        </div>
      </section>

      <!-- C: Soft trailing fade -->
      <section class="fade-debug__panel">
        <div class="fade-debug__panel-head">
          <div>
            <h2 class="fade-debug__panel-title">C · Soft trailing fade</h2>
            <p class="fade-debug__panel-desc">
              Settled prefix is solid; only the newest characters use a soft opacity ramp.
            </p>
          </div>
          <div class="fade-debug__panel-actions">
            <button type="button" class="fade-debug__btn" @click="playTrail">
              {{ trailPlaying ? 'Replay' : 'Play' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="!trailPlaying"
              @click="togglePauseTrail"
            >
              {{ trailPaused ? 'Resume' : 'Pause' }}
            </button>
            <button type="button" class="fade-debug__btn fade-debug__btn--ghost" @click="resetTrail">
              Reset
            </button>
          </div>
        </div>
        <div class="fade-debug__params">
          <label class="fade-debug__toggle">
            <input v-model="trailSoftOn" type="checkbox" />
            Soft trail
          </label>
          <label class="fade-debug__param">
            <span>Stream {{ trailSpeed }} chars/s</span>
            <input v-model.number="trailSpeed" type="range" min="10" max="120" step="5" />
          </label>
          <label class="fade-debug__param">
            <span>Trail length {{ trailChars }} chars</span>
            <input v-model.number="trailChars" type="range" min="4" max="80" step="1" />
          </label>
          <label class="fade-debug__param">
            <span>Trail start opacity {{ trailStartOpacity }}%</span>
            <input v-model.number="trailStartOpacity" type="range" min="0" max="80" step="5" />
          </label>
        </div>
        <div class="story-prose fade-debug__prose">
          <p class="fade-debug__stream">
            <template v-if="prefersReducedMotion || !trailSoftOn">{{ trailRevealed }}</template>
            <template v-else>
              <span class="fade-trail__head">{{ trailParts.head }}</span>
              <span class="fade-trail__tail">{{ trailParts.tail }}</span>
            </template>
          </p>
        </div>
      </section>

      <!-- D: GSAP SplitText -->
      <section class="fade-debug__panel">
        <div class="fade-debug__panel-head">
          <div>
            <h2 class="fade-debug__panel-title">D · GSAP SplitText</h2>
            <p class="fade-debug__panel-desc">
              Full sample text staggers in via CDN GSAP. Not streamed — Play runs once.
            </p>
          </div>
          <div class="fade-debug__panel-actions">
            <button
              type="button"
              class="fade-debug__btn"
              :disabled="splitLoading"
              @click="playSplit"
            >
              {{ splitLoading ? 'Loading…' : splitPlaying ? 'Replay' : 'Play' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="!splitPlaying || splitLoading"
              @click="togglePauseSplit"
            >
              {{ splitPaused ? 'Resume' : 'Pause' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="splitLoading"
              @click="resetSplit"
            >
              Reset
            </button>
          </div>
        </div>
        <div class="fade-debug__params">
          <label class="fade-debug__toggle">
            <input v-model="splitAnimOn" type="checkbox" />
            Motion (opacity + y)
          </label>
          <label class="fade-debug__param">
            <span>Split</span>
            <select v-model="splitType" class="fade-debug__select">
              <option value="chars">chars</option>
              <option value="words">words</option>
            </select>
          </label>
          <label class="fade-debug__param">
            <span>Stagger {{ splitDelayMs }}ms</span>
            <input v-model.number="splitDelayMs" type="range" min="0" max="200" step="5" />
          </label>
          <label class="fade-debug__param">
            <span>Duration {{ splitDurationSec.toFixed(2) }}s</span>
            <input v-model.number="splitDurationSec" type="range" min="0.1" max="2" step="0.05" />
          </label>
          <label class="fade-debug__param">
            <span>Y offset {{ splitY }}px</span>
            <input v-model.number="splitY" type="range" min="0" max="60" step="2" />
          </label>
        </div>
        <div class="story-prose fade-debug__prose">
          <p v-if="splitLoading" class="fade-debug__status">Loading GSAP from CDN…</p>
          <p v-else-if="splitError" class="fade-debug__status fade-debug__status--error">
            {{ splitError }}
          </p>
          <p v-else-if="prefersReducedMotion && splitActive" class="fade-debug__stream">
            {{ SAMPLE_TEXT }}
          </p>
          <SplitText
            v-else-if="splitActive"
            ref="splitTextRef"
            :key="`${splitPlayKey}-${splitType}-${splitDelayMs}-${splitDurationSec}-${splitY}-${splitAnimOn}`"
            :text="SAMPLE_TEXT"
            class-name="fade-debug__stream fade-debug__split"
            :delay="splitDelayMs"
            :duration="splitDurationSec"
            ease="power3.out"
            :split-type="splitType"
            :from="splitFrom"
            :to="{ opacity: 1, y: 0 }"
            text-align="left"
            tag="p"
            :scroll-trigger="false"
            @letter-animation-complete="onSplitComplete"
            @load-error="onSplitLoadError"
          />
        </div>
      </section>

      <!-- E: Blur to focus -->
      <section class="fade-debug__panel">
        <div class="fade-debug__panel-head">
          <div>
            <h2 class="fade-debug__panel-title">E · Blur to focus</h2>
            <p class="fade-debug__panel-desc">
              Each word mounts blurred and sharpens into focus. Streamed like A–C.
            </p>
          </div>
          <div class="fade-debug__panel-actions">
            <button type="button" class="fade-debug__btn" @click="playBlur">
              {{ blurPlaying ? 'Replay' : 'Play' }}
            </button>
            <button
              type="button"
              class="fade-debug__btn fade-debug__btn--ghost"
              :disabled="!blurPlaying"
              @click="togglePauseBlur"
            >
              {{ blurPaused ? 'Resume' : 'Pause' }}
            </button>
            <button type="button" class="fade-debug__btn fade-debug__btn--ghost" @click="resetBlur">
              Reset
            </button>
          </div>
        </div>
        <div class="fade-debug__params">
          <label class="fade-debug__toggle">
            <input v-model="blurAnimOn" type="checkbox" />
            Blur animation
          </label>
          <label class="fade-debug__param">
            <span>Stream {{ blurSpeed }} chars/s</span>
            <input v-model.number="blurSpeed" type="range" min="10" max="120" step="5" />
          </label>
          <label class="fade-debug__param">
            <span>Duration {{ blurMs }}ms</span>
            <input v-model.number="blurMs" type="range" min="50" max="1200" step="10" />
          </label>
          <label class="fade-debug__param">
            <span>Blur {{ blurPx }}px</span>
            <input v-model.number="blurPx" type="range" min="0" max="20" step="1" />
          </label>
          <label class="fade-debug__param">
            <span>Start opacity {{ blurStartOpacity }}%</span>
            <input v-model.number="blurStartOpacity" type="range" min="0" max="100" step="5" />
          </label>
        </div>
        <div class="story-prose fade-debug__prose">
          <p class="fade-debug__stream">
            <template v-if="prefersReducedMotion || !blurAnimOn">{{ blurRevealed }}</template>
            <template v-else>
              <span
                v-for="token in blurTokens"
                :key="token.id"
                :class="token.isSpace ? 'fade-blur--space' : 'fade-blur'"
              >{{ token.text }}</span>
            </template>
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.fade-debug {
  min-height: 100dvh;
  padding: 2rem clamp(1rem, 4vw, 3rem) 4rem;
  background: var(--paper, #f7f3ea);
  color: var(--ink, #1a1814);
}

.fade-debug__header {
  max-width: 56rem;
  margin-bottom: 2.5rem;
}

.fade-debug__eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--blue-deep, #1e4d7b);
}

.fade-debug__title {
  margin: 0 0 0.5rem;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(1.8rem, 3vw, 2.4rem);
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.fade-debug__lede {
  margin: 0 0 1.25rem;
  color: var(--ink-soft, #5c564c);
  font-size: 0.95rem;
  line-height: 1.5;
  max-width: 36rem;
}

.fade-debug__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
}

.fade-debug__btn {
  border: 1.5px solid var(--ink, #1a1814);
  background: var(--ink, #1a1814);
  color: var(--paper, #f7f3ea);
  padding: 0.4rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.fade-debug__btn--ghost {
  background: transparent;
  color: var(--ink, #1a1814);
}

.fade-debug__btn:hover {
  opacity: 0.88;
}

.fade-debug__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.fade-debug__status {
  margin: 0;
  font-size: 0.85rem;
  color: var(--ink-soft, #5c564c);
}

.fade-debug__status--error {
  color: #8b2e2e;
}

.fade-debug__params {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr));
  gap: 0.65rem 1rem;
  margin-bottom: 0.85rem;
  align-items: end;
}

.fade-debug__param {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: 0.72rem;
  color: var(--ink-soft, #5c564c);
  min-width: 0;
}

.fade-debug__param input[type='range'] {
  width: 100%;
}

.fade-debug__toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--ink, #1a1814);
  font-weight: 600;
  padding-bottom: 0.15rem;
  user-select: none;
}

.fade-debug__select {
  border: 1px solid var(--line-soft, #d4cbb8);
  background: var(--paper, #f7f3ea);
  color: var(--ink, #1a1814);
  padding: 0.25rem 0.4rem;
  font-size: 0.8rem;
}

.fade-debug__meta {
  font-size: 0.75rem;
  color: var(--ink-soft, #5c564c);
}

.fade-debug__panels {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  align-items: stretch;
}

.fade-debug__panel {
  flex: 1 1 22rem;
  max-width: 100%;
  box-sizing: border-box;
  border: 1.5px solid var(--line-soft, #d4cbb8);
  padding: 1rem 1.1rem 1.15rem;
}

.fade-debug__panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  margin-bottom: 0.65rem;
}

.fade-debug__panel-actions {
  display: flex;
  flex-shrink: 0;
  gap: 0.5rem;
}

.fade-debug__panel-title {
  margin: 0 0 0.25rem;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.fade-debug__panel-desc {
  margin: 0;
  font-size: 0.8rem;
  color: var(--ink-soft, #5c564c);
  line-height: 1.45;
  max-width: 28rem;
}

.fade-debug__prose {
  min-height: 6rem;
}

.fade-debug__stream {
  margin: 0;
  white-space: pre-wrap;
}

.fade-debug__split {
  width: 100%;
  max-width: 100%;
}

.fade-debug__split :deep(.split-char),
.fade-debug__split :deep(.split-word) {
  display: inline-block;
}

/* A · Word fade */
.fade-word {
  display: inline;
  animation: story-fade-in v-bind(wordFadeDuration) ease both;
}

.fade-word--space {
  display: inline;
}

/* B · Chunk fade */
.fade-chunk {
  display: inline;
  animation: story-fade-in-chunk v-bind(chunkFadeDuration) ease both;
}

/* E · Blur to focus */
.fade-blur {
  display: inline-block;
  animation: story-blur-in v-bind(blurDuration) ease both;
}

.fade-blur--space {
  display: inline;
}

/* C · Soft trailing fade */
.fade-trail__head {
  display: inline;
}

.fade-trail__tail {
  display: inline;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--ink, #1a1814) v-bind(trailStartOpacityCss), transparent) 0%,
    var(--ink, #1a1814) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

@keyframes story-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes story-fade-in-chunk {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes story-blur-in {
  from {
    opacity: v-bind(blurOpacityCss);
    filter: blur(v-bind(blurAmount));
  }
  to {
    opacity: 1;
    filter: blur(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .fade-word,
  .fade-chunk,
  .fade-blur {
    animation: none;
    filter: none;
  }

  .fade-trail__tail {
    background: none;
    color: inherit;
    -webkit-background-clip: unset;
    background-clip: unset;
  }
}
</style>
