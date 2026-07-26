import { onUnmounted, ref, type Ref } from 'vue'

const DEFAULT_INTERVAL_MS = 50

/**
 * Reveals sample text in timed chunks, matching GamePlay stream pacing.
 * charsPerSecond drives chunk size the same way STREAM_REVEAL_* does in GamePlayView.
 * Pass a shared Ref to sync speed across multiple independent streams.
 */
export function useSimulatedTextStream(
  sampleText: string,
  options?: { charsPerSecond?: Ref<number> },
) {
  const revealed = ref('')
  const isPlaying = ref(false)
  const isPaused = ref(false)
  const charsPerSecond = options?.charsPerSecond ?? ref(50)

  let buffer = ''
  let timer: number | null = null

  function chunkSize() {
    return Math.max(1, Math.round((charsPerSecond.value * DEFAULT_INTERVAL_MS) / 1000))
  }

  function clearTimer() {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
  }

  function stop() {
    clearTimer()
    isPlaying.value = false
    isPaused.value = false
  }

  function flush() {
    if (!buffer) {
      stop()
      return
    }
    const size = chunkSize()
    const next = buffer.slice(0, size)
    buffer = buffer.slice(next.length)
    revealed.value += next
  }

  function startTimer() {
    clearTimer()
    timer = window.setInterval(flush, DEFAULT_INTERVAL_MS)
  }

  function play() {
    stop()
    revealed.value = ''
    buffer = sampleText
    isPlaying.value = true
    isPaused.value = false
    startTimer()
  }

  function pause() {
    if (!isPlaying.value || isPaused.value || !buffer) return
    clearTimer()
    isPaused.value = true
  }

  function resume() {
    if (!isPlaying.value || !isPaused.value) return
    if (!buffer) {
      stop()
      return
    }
    isPaused.value = false
    startTimer()
  }

  function togglePause() {
    if (isPaused.value) resume()
    else pause()
  }

  function reset() {
    stop()
    revealed.value = ''
    buffer = ''
  }

  onUnmounted(stop)

  return {
    revealed: revealed as Ref<string>,
    isPlaying: isPlaying as Ref<boolean>,
    isPaused: isPaused as Ref<boolean>,
    charsPerSecond,
    play,
    pause,
    resume,
    togglePause,
    reset,
    stop,
    intervalMs: DEFAULT_INTERVAL_MS,
  }
}
