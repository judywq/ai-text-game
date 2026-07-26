<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { ExplanationService } from '@/services/explanationService'
import type { GameStory, StoryProgress, StoryOption, TextExplanation, ExplanationStatus, StoryUpdate } from '@/types/game'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast/use-toast'
import { useGameWebSocket } from '@/composables/useGameWebSocket'
import { CircleHelp } from 'lucide-vue-next'
import StorySegment from '@/components/StorySegment.vue'
import StoryImage from '@/components/StoryImage.vue'
import StoryOptions from '@/components/StoryOptions.vue'
import BrandMark from '@/components/line-art/BrandMark.vue'
import { marked } from 'marked'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAuthStore } from '@/stores/auth'
import { AuthService } from '@/services/authService'
import { NATIVE_LANGUAGE_OPTIONS } from '@/constants/nativeLanguage'
import { Settings } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()
const authStore = useAuthStore()

const story = ref<GameStory | null>(null)
const progressEntries = ref<StoryProgress[]>([])
const chapterIndex = ref(0)
const chapterPickerOpen = ref(false)
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const notesCollapsed = ref(false)
const NOTES_MOBILE_MQ = '(max-width: 1100px)'
let notesMobileMql: MediaQueryList | null = null

function syncNotesCollapsedForViewport() {
  if (typeof window === 'undefined') return
  if (window.matchMedia(NOTES_MOBILE_MQ).matches) {
    notesCollapsed.value = true
  }
}

function onNotesViewportChange(event: MediaQueryListEvent) {
  if (event.matches) {
    notesCollapsed.value = true
  }
}

const {
  connect,
  selectOption,
  startStory,
  lookupExplanation,
  onStoryUpdate,
  onStoryStream,
  onImageReady,
  onExplanationCreated,
  onExplanationStream,
  onExplanationStatus,
  onExplanationCompleted,
  onError,
  onSkeletonGenerationStarted,
} = useGameWebSocket()

const currentOptions = ref<StoryOption[]>([])
const rawSelection = ref('')
const contextSelection = ref('')
const popupPosition = ref({ x: 0, y: 0 })
const showLookupButton = ref(false)
const explanationModalVisible = ref(false)
const currentExplanation = ref<TextExplanation | null>(null)
// Render the completed explanation as markdown so the model's bolded
// definition shows. Streaming stays plain text to avoid mid-token flicker.
const renderedExplanation = computed(() =>
  currentExplanation.value?.explanation
    ? (marked.parse(currentExplanation.value.explanation) as string)
    : ''
)
const lookupHistory = ref<TextExplanation[]>([])
const nativeLanguagePromptOpen = ref(false)
const nativeLanguageChoiceForPrompt = ref('')
const nativeLanguagePersistToProfile = ref(false)
const sessionNativeLanguage = ref<string>('')
const nativeLanguageDialogMode = ref<'lookup' | 'settings'>('lookup')

// Add reactive variable for mobile lookup history panel
const showHistoryPanel = ref(false)

// Add a new ref for the current streaming content
const currentStreamingContent = ref('')
const pendingStreamingBuffer = ref('')
const activeStreamingEntryIndex = ref<number | null>(null)
const pendingStoryUpdate = ref<StoryUpdate | null>(null)
const isFinalizingStoryStream = ref(false)
const STREAM_REVEAL_INTERVAL_MS = 50
const STREAM_REVEAL_CHARS_PER_SECOND = 50
const STREAM_REVEAL_CHUNK_SIZE = Math.max(
  1,
  Math.round((STREAM_REVEAL_CHARS_PER_SECOND * STREAM_REVEAL_INTERVAL_MS) / 1000)
)
let streamRenderTimer: number | null = null

// Track which entries are ready to display (after refetch completes)
const isContentReady = ref<{ [entryIndex: number]: boolean }>({})

// Track if all paragraphs have been shown for the latest entry
const allParagraphsShown = ref(false)

const isGameEnded = computed(() => story.value?.status === 'COMPLETED')

const canOpenVocabularyReview = computed(() => lookupHistory.value.length > 0)

const chapterCount = computed(() => progressEntries.value.length)

const currentEntry = computed(() => {
  if (progressEntries.value.length === 0) return null
  const index = Math.min(chapterIndex.value, progressEntries.value.length - 1)
  return progressEntries.value[index] ?? null
})

const isOnLatestChapter = computed(() => {
  if (progressEntries.value.length === 0) return false
  return chapterIndex.value === progressEntries.value.length - 1
})

const canGoPrevChapter = computed(() => chapterIndex.value > 0)

const canGoNextChapter = computed(
  () => chapterIndex.value < progressEntries.value.length - 1,
)

function goToLatestChapter() {
  if (progressEntries.value.length === 0) {
    chapterIndex.value = 0
    return
  }
  chapterIndex.value = progressEntries.value.length - 1
}

function goToPrevChapter() {
  if (canGoPrevChapter.value) {
    chapterIndex.value -= 1
  }
}

function goToNextChapter() {
  if (canGoNextChapter.value) {
    chapterIndex.value += 1
  }
}

function goToChapter(index: number) {
  if (index < 0 || index >= progressEntries.value.length) return
  chapterIndex.value = index
  chapterPickerOpen.value = false
}

// Computed property to determine if options should be shown
const shouldShowOptions = computed(() => {
  if (progressEntries.value.length === 0) return false
  if (!isOnLatestChapter.value) return false
  const lastEntry = progressEntries.value[progressEntries.value.length - 1]
  const lastEntryIndex = progressEntries.value.length - 1

  // Show options only if:
  // 1. Viewing the latest chapter
  // 2. Content is ready (streaming complete and refetch done)
  // 3. No option has been chosen yet
  // 4. All paragraphs have been shown
  return isContentReady.value[lastEntryIndex] &&
         !lastEntry.chosen_option_text &&
         allParagraphsShown.value
})

// Update current options based on shouldShowOptions
watch(shouldShowOptions, (show) => {
  if (show && progressEntries.value.length > 0) {
    const lastEntry = progressEntries.value[progressEntries.value.length - 1]
    currentOptions.value = lastEntry.options || []
  } else {
    currentOptions.value = []
  }
}, { immediate: true })

watch(chapterIndex, () => {
  if (scrollRef.value) {
    scrollRef.value.scrollTop = 0
  }
})

// Handle when all paragraphs are shown in a segment
function onAllParagraphsShown() {
  allParagraphsShown.value = true
  scrollToBottom()
}

function stopStreamRenderTimer() {
  if (streamRenderTimer !== null) {
    window.clearInterval(streamRenderTimer)
    streamRenderTimer = null
  }
}

function resetStreamingState() {
  stopStreamRenderTimer()
  currentStreamingContent.value = ''
  pendingStreamingBuffer.value = ''
  activeStreamingEntryIndex.value = null
  pendingStoryUpdate.value = null
}

function ensureStreamingEntry() {
  if (activeStreamingEntryIndex.value !== null && progressEntries.value[activeStreamingEntryIndex.value]) {
    return
  }

  if (
    progressEntries.value.length > 0 &&
    progressEntries.value[progressEntries.value.length - 1].id === -1
  ) {
    progressEntries.value.pop()
  }

  progressEntries.value.push({
    id: Date.now(),
    content: '',
    decision_point_id: '',
    chosen_option_id: '',
    chosen_option_text: '',
    is_end_point: false,
    options: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  })

  activeStreamingEntryIndex.value = progressEntries.value.length - 1
  currentStreamingContent.value = ''
  allParagraphsShown.value = false
  isContentReady.value[activeStreamingEntryIndex.value] = false
  goToLatestChapter()
}

function syncVisibleStreamingContent() {
  if (activeStreamingEntryIndex.value === null) {
    return
  }

  const activeEntry = progressEntries.value[activeStreamingEntryIndex.value]
  if (!activeEntry) {
    activeStreamingEntryIndex.value = null
    return
  }

  activeEntry.content = currentStreamingContent.value
  activeEntry.updated_at = new Date().toISOString()
}

async function syncCompletedStoryEntry(entryIndex: number) {
  if (!story.value || !progressEntries.value[entryIndex]) {
    return
  }

  try {
    const serverEntries = await GameService.getStoryProgress(story.value.id)
    const completedEntry = serverEntries[entryIndex]

    if (completedEntry) {
      progressEntries.value[entryIndex] = completedEntry
    }
  } catch (error) {
    console.error('Failed to sync completed story entry', error)
  } finally {
    isContentReady.value[entryIndex] = true
    scrollToBottom()
  }
}

async function finalizeStoryStream() {
  if (isFinalizingStoryStream.value) {
    return
  }

  const update = pendingStoryUpdate.value
  if (!update) {
    return
  }

  isFinalizingStoryStream.value = true

  const latestEntryIndex = activeStreamingEntryIndex.value ?? (progressEntries.value.length - 1)
  const latestEntry = latestEntryIndex >= 0 ? progressEntries.value[latestEntryIndex] : null

  allParagraphsShown.value = false

  if (latestEntry) {
    if (update.content) {
      latestEntry.content = update.content
    }
    latestEntry.decision_point_id = update.current_decision || ''
    latestEntry.options = update.options || []
    latestEntry.updated_at = new Date().toISOString()
    isContentReady.value[latestEntryIndex] = false
  }

  if (update.status && story.value) {
    story.value.status = update.status as GameStory['status']
  }

  currentStreamingContent.value = ''
  pendingStreamingBuffer.value = ''
  activeStreamingEntryIndex.value = null
  pendingStoryUpdate.value = null
  stopStreamRenderTimer()

  try {
    if (latestEntry) {
      await syncCompletedStoryEntry(latestEntryIndex)
    } else {
      scrollToBottom()
    }
  } finally {
    isFinalizingStoryStream.value = false
  }
}

function flushStreamingBuffer() {
  if (!pendingStreamingBuffer.value) {
    stopStreamRenderTimer()
    void finalizeStoryStream()
    return
  }

  const nextChunk = pendingStreamingBuffer.value.slice(0, STREAM_REVEAL_CHUNK_SIZE)
  pendingStreamingBuffer.value = pendingStreamingBuffer.value.slice(nextChunk.length)
  currentStreamingContent.value += nextChunk
  syncVisibleStreamingContent()
  scrollToBottom()

  if (!pendingStreamingBuffer.value && pendingStoryUpdate.value) {
    void finalizeStoryStream()
  }
}

function startStreamRenderTimer() {
  if (streamRenderTimer !== null) {
    return
  }

  streamRenderTimer = window.setInterval(() => {
    flushStreamingBuffer()
  }, STREAM_REVEAL_INTERVAL_MS)
}

// New helper function using the Range object for an accurate context extraction.
function extractSentenceFromRange(range: Range): string {
  // Get the text node in which the selection exists.
  const textNode = range.startContainer;
  if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
    // If it's not a text node, return the raw selection.
    return range.toString().trim();
  }
  const textContent = textNode.textContent || "";
  let start = range.startOffset;
  // Move backwards until a sentence delimiter is found or the beginning is reached.
  while (start > 0 && !".!?".includes(textContent[start - 1])) {
    start--;
  }
  let end = range.endOffset;
  // Move forward until a sentence delimiter is found or the end is reached.
  while (end < textContent.length && !".!?".includes(textContent[end])) {
    end++;
  }
  return textContent.slice(start, end).trim();
}

function handleTextSelection(e: MouseEvent | TouchEvent) {
  const sel = window.getSelection();
  if (!sel || sel.toString().trim().length === 0) {
    showLookupButton.value = false;
    return;
  }

  // If selection spans different nodes, refuse the request
  if (sel.anchorNode !== sel.focusNode) {
    // toast({
    //   title: 'Error',
    //   description: 'Please select text within a single message!',
    //   variant: 'destructive',
    // });
    // sel.removeAllRanges();
    showLookupButton.value = false;
    return;
  }

  const range = sel.getRangeAt(0);
  rawSelection.value = sel.toString().trim();
  contextSelection.value = extractSentenceFromRange(range);

  // Get client coordinates from either mouse or touch event
  let clientX: number;
  let clientY: number;

  if (e instanceof MouseEvent) {
    clientX = e.clientX;
    clientY = e.clientY;
  } else {
    // TouchEvent - use the first touch point
    const touch = e.changedTouches[0];
    clientX = touch.clientX;
    clientY = touch.clientY;
  }

  // Calculate popup position relative to the scroll container including its scroll offsets.
  const containerRect = scrollRef.value?.getBoundingClientRect();
  if (containerRect && scrollRef.value) {
    const scrollLeft = scrollRef.value.scrollLeft;
    const scrollTop = scrollRef.value.scrollTop;
    popupPosition.value = {
      x: clientX - containerRect.left + scrollLeft,
      y: clientY - containerRect.top + scrollTop,
    }
  } else {
    popupPosition.value = {
      x: clientX,
      y: clientY,
    }
  }

  showLookupButton.value = true;
}

function clearTextSelection() {
  rawSelection.value = ''
  contextSelection.value = ''
  showLookupButton.value = false
}

async function runLookupExplanation() {
  if (!story.value) return
  try {
    const clientId = Date.now()
    // Open the modal before starting the request
    currentExplanation.value = {
      id: 0, // temporary id
      story: story.value.id,
      selected_text: rawSelection.value,
      context_text: contextSelection.value,
      explanation: '',
      status: 'pending',
      created_at: new Date().toISOString(),
    }
    explanationModalVisible.value = true

    // Start the WebSocket request
    const result = await lookupExplanation(
      story.value.id,
      rawSelection.value,
      contextSelection.value,
      clientId,
      nativeLanguageForLookup.value
    )
    currentExplanation.value = result
    fetchLookupHistory()
  } catch (error: any) {
    toast({
      title: 'Error',
      description: 'Failed to lookup explanation',
      variant: 'destructive',
    })
    // Close the modal on error
    explanationModalVisible.value = false
  } finally {
    clearTextSelection()
  }
}

async function lookupExplanationSubmit() {
  if (!story.value) return
  if (!authStore.user?.native_language && !sessionNativeLanguage.value) {
    nativeLanguageDialogMode.value = 'lookup'
    nativeLanguageChoiceForPrompt.value = ''
    nativeLanguagePersistToProfile.value = false
    nativeLanguagePromptOpen.value = true
    return
  }
  await runLookupExplanation()
}

function openNativeLanguageSettings() {
  nativeLanguageDialogMode.value = 'settings'
  nativeLanguageChoiceForPrompt.value =
    authStore.user?.native_language || sessionNativeLanguage.value || ''
  nativeLanguagePersistToProfile.value = true
  nativeLanguagePromptOpen.value = true
}

async function confirmNativeLanguageAndLookup() {
  if (!nativeLanguageChoiceForPrompt.value) {
    toast({
      title: 'Explanation language required',
      description: 'Please choose your explanation language to continue.',
      variant: 'destructive',
    })
    return
  }
  try {
    if (nativeLanguagePersistToProfile.value) {
      const user = await AuthService.updateUser({
        native_language: nativeLanguageChoiceForPrompt.value,
      })
      authStore.user = user
      authStore.saveState()
      sessionNativeLanguage.value = ''
    } else {
      sessionNativeLanguage.value = nativeLanguageChoiceForPrompt.value
    }
    nativeLanguagePromptOpen.value = false
    if (nativeLanguageDialogMode.value === 'lookup') {
      await runLookupExplanation()
    }
  } catch (error: any) {
    toast({
      title: 'Error',
      description: error?.message ?? 'Failed to save language preference',
      variant: 'destructive',
    })
  }
}

async function fetchLookupHistory() {
  if (!story.value) return;
  try {
    const history = await ExplanationService.getLookupHistory(story.value.id)
    lookupHistory.value = history
  } catch (error) {
    console.error("Failed to fetch lookup history", error)
  }
}

const nativeLanguageForLookup = computed(() => {
  // Session override must take precedence over profile value.
  return sessionNativeLanguage.value || authStore.user?.native_language || undefined
})

async function fetchStoryAndProgress() {
  const storyId = parseInt(route.params.id as string)
  resetStreamingState()
  story.value = await GameService.getStory(storyId)
  progressEntries.value = await GameService.getStoryProgress(storyId)
  // Mark all existing entries as ready to display
  progressEntries.value.forEach((_, index) => {
    isContentReady.value[index] = true
  })
  goToLatestChapter()
}

const loadStory = async () => {
  try {
    const storyId = parseInt(route.params.id as string)
    await fetchStoryAndProgress()

    await connect(storyId)

    onSkeletonGenerationStarted.value = () => {
      router.push(`/game/${storyId}/loading`)
    }

    // Start story if no progress exists
    if (progressEntries.value.length === 0 && story.value?.status === 'INIT') {
      await startStory()
    }

    // Add error handler
    onError.value = async (error: Error) => {
      await fetchStoryAndProgress()

      toast({
        title: 'WebSocket Error',
        description: error.message,
        variant: 'destructive',
      })
    }
  } catch (error: any) {
    console.error('Failed to load story', error)
    toast({
      title: 'Error',
      description: error.message || 'Failed to load story',
      variant: 'destructive',
    })
    router.push('/game')
  }
}

const handleOptionSelect = async (optionId: string) => {
  if (!story.value || isLoading.value) return

  isLoading.value = true
  try {
    // Get the latest progress entry
    const latestEntry = progressEntries.value[progressEntries.value.length - 1]

    // Find the selected option text from currentOptions
    const selectedOption = currentOptions.value.find(opt => opt.option_id === optionId)

    // Update the latest entry with the chosen option
    if (latestEntry && selectedOption) {
      latestEntry.chosen_option_text = selectedOption.option_name
    }

    // Hide options immediately after selection
    currentOptions.value = []
    allParagraphsShown.value = false

    // Add a loading placeholder entry
    progressEntries.value.push({
      id: -1, // Special ID for loading state
      content: 'LOADING',
      decision_point_id: '',
      chosen_option_id: '',
      chosen_option_text: '',
      is_end_point: false,
      options: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })
    goToLatestChapter()

    // Send the selection to the server
    await selectOption(optionId)

  } catch (error: any) {
    toast({
      title: 'Error',
      description: error.message || 'Failed to select option',
      variant: 'destructive',
    })
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  syncNotesCollapsedForViewport()
  notesMobileMql = window.matchMedia(NOTES_MOBILE_MQ)
  notesMobileMql.addEventListener('change', onNotesViewportChange)

  const storyId = Number(route.params.id)
  if (!storyId) {
    router.push('/game')
    return
  }

  try {
    // Add handler for story streaming
    onStoryStream.value = (content: string) => {
      // Turn off loading spinner when streaming starts
      isLoading.value = false

      // Ignore empty chunks from backend
      if (!content || content.trim() === '') {
        return
      }

      ensureStreamingEntry()
      pendingStreamingBuffer.value += content
      startStreamRenderTimer()
    }

    // Modify the existing story update handler to handle the final state
    onStoryUpdate.value = (update: StoryUpdate) => {
      pendingStoryUpdate.value = update

      if (!pendingStreamingBuffer.value && streamRenderTimer === null) {
        void finalizeStoryStream()
      }
    }

    // Set up explanation handlers
    onExplanationCreated.value = (explanation: TextExplanation) => {
      if (currentExplanation.value) {
        currentExplanation.value = {
          ...explanation,
          explanation: '', // Reset explanation text as it will come through stream
          status: 'pending' // Keep as pending until streaming starts
        }
      }
    }

    // Add handler for status updates
    onExplanationCompleted.value = (explanation: TextExplanation) => {
      if (currentExplanation.value?.id === explanation.id) {
        currentExplanation.value = explanation
        fetchLookupHistory()
      }
    }

    onExplanationStream.value = (id: number, content: string) => {
      if (currentExplanation.value?.id === id) {
        currentExplanation.value.explanation += content
      }
    }

    onExplanationStatus.value = (id: number, status: ExplanationStatus) => {
      if (currentExplanation.value?.id === id) {
        currentExplanation.value.status = status
      }
    }

    // Add handler for image_ready message
    onImageReady.value = (progressId: number, imageUrl: string) => {
      // Update the latest progress entry (images arrive in order)
      const latestEntry = progressEntries.value[progressEntries.value.length - 1]
      if (latestEntry) {
        latestEntry.image_url = imageUrl
        latestEntry.id = progressId // Update to real database ID
      }
    }

    // Load initial story data and establish WebSocket connection
    await loadStory()

    scrollToBottom()
    fetchLookupHistory()

  } catch (error) {
    console.error('Failed to load story', error)
    toast({
      title: 'Error',
      description: 'Failed to load story',
      variant: 'destructive',
    })
    router.push('/game')
  }
})

onUnmounted(() => {
  stopStreamRenderTimer()
  notesMobileMql?.removeEventListener('change', onNotesViewportChange)
  notesMobileMql = null
})

function scrollToBottom() {
  setTimeout(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  }, 100)
}

</script>

<template>
  <div class="reader-shell">
    <header class="reader-header">
      <BrandMark class="reader-brand" />
      <nav class="reader-nav" aria-label="Primary">
        <router-link :to="{ name: 'game-scenarios' }">Stories</router-link>
        <router-link :to="{ name: 'history' }">My library</router-link>
      </nav>
      <button
        type="button"
        class="exit-link"
        :disabled="isLoading"
        @click="router.push('/game')"
      >
        Exit
      </button>
    </header>

    <div class="reader-stage" :class="{ 'notes-collapsed': notesCollapsed }">
      <button
        type="button"
        class="notes-backdrop"
        aria-label="Close notes"
        tabindex="-1"
        @click="notesCollapsed = true"
      />
      <div class="book-stage">
        <header class="reader-title-block">
          <p class="reader-kicker">CHAPTER {{ chapterCount ? chapterIndex + 1 : '—' }}</p>
          <h1>{{ story?.title || 'Reading…' }}</h1>
        </header>

        <section class="reader-panel">
          <figure class="scene-leaf scene-leaf--image">
            <StoryImage
              v-if="currentEntry?.image_url"
              :image-url="currentEntry.image_url"
              :alt="`Illustration for chapter ${chapterIndex + 1}`"
            />
            <div v-else class="scene-image-placeholder" aria-hidden="true" />
          </figure>

          <section class="story-leaf">
            <div
              class="story-scroll"
              ref="scrollRef"
              @mouseup="handleTextSelection"
              @touchend="handleTextSelection"
            >
              <div v-if="progressEntries.length === 0" class="story-prose" style="opacity: 0.7">
                <p>Initializing your story…</p>
              </div>

              <div v-else-if="currentEntry" class="story-prose">
                <StorySegment
                  :key="currentEntry.id"
                  :entry="currentEntry"
                  :is-latest="isOnLatestChapter"
                  :is-content-ready="isContentReady[chapterIndex] || false"
                  :show-image="false"
                  @all-paragraphs-shown="onAllParagraphsShown"
                />

                <div v-if="isLoading && isOnLatestChapter" class="story-prose" style="opacity: 0.7; margin-top: 1rem">
                  <p>Generating next part…</p>
                </div>
              </div>

              <div
                v-if="showLookupButton"
                :style="{
                  position: 'absolute',
                  top: popupPosition.y + 'px',
                  left: popupPosition.x + 'px',
                  zIndex: 5,
                }"
              >
                <button
                  type="button"
                  class="la-btn"
                  style="min-height: 36px; padding: 0 10px; box-shadow: 2px 2px 0 var(--blue)"
                  aria-label="Look up selection"
                  @click="lookupExplanationSubmit"
                  @touchend.stop="lookupExplanationSubmit"
                >
                  <CircleHelp class="w-4 h-4" />
                </button>
              </div>
            </div>

            <div class="story-controls">
              <div class="story-options-wrap">
                <StoryOptions
                  v-if="shouldShowOptions"
                  :options="currentOptions"
                  :disabled="false"
                  @select="handleOptionSelect"
                />
              </div>

              <nav
                v-if="chapterCount > 0"
                class="page-turner"
                aria-label="Chapters"
              >
                <button
                  type="button"
                  class="page-turner-btn"
                  :disabled="!canGoPrevChapter"
                  @click="goToPrevChapter"
                >
                  ← Prev
                </button>
                <Popover v-model:open="chapterPickerOpen">
                  <PopoverTrigger as-child>
                    <button
                      type="button"
                      class="page-turner-chapter"
                      aria-haspopup="listbox"
                      :aria-expanded="chapterPickerOpen"
                    >
                      Chapter {{ chapterIndex + 1 }} of {{ chapterCount }}
                    </button>
                  </PopoverTrigger>
                  <PopoverContent
                    side="top"
                    align="center"
                    :side-offset="8"
                    class="chapter-picker"
                  >
                    <ul class="chapter-picker-list" role="listbox" aria-label="Jump to chapter">
                      <li v-for="(_, index) in progressEntries" :key="index">
                        <button
                          type="button"
                          role="option"
                          :aria-selected="index === chapterIndex"
                          :aria-current="index === chapterIndex ? 'page' : undefined"
                          :class="{ 'is-current': index === chapterIndex }"
                          @click="goToChapter(index)"
                        >
                          Chapter {{ index + 1 }}
                        </button>
                      </li>
                    </ul>
                  </PopoverContent>
                </Popover>
                <button
                  type="button"
                  class="page-turner-btn"
                  :disabled="!canGoNextChapter"
                  @click="goToNextChapter"
                >
                  Next →
                </button>
              </nav>
            </div>
          </section>
        </section>
      </div>

      <aside class="notes-rail" id="reader-notes-panel">
        <button
          type="button"
          class="notes-tab"
          :aria-expanded="!notesCollapsed"
          aria-controls="reader-notes-panel"
          @click="notesCollapsed = !notesCollapsed"
        >
          Notes
        </button>
        <div class="notes-content">
          <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 8px">
            <div>
              <p class="reader-kicker">LOOKUPS</p>
            </div>
            <button
              type="button"
              class="la-btn"
              style="min-height: 32px; padding: 0 8px; box-shadow: 2px 2px 0 var(--blue)"
              title="Language settings"
              aria-label="Language settings"
              @click="openNativeLanguageSettings"
            >
              <Settings class="h-4 w-4" />
            </button>
          </div>
          <p class="notes-instruction">Select text in the story to look up a word or phrase.</p>
          <ul class="note-list">
            <li v-for="item in lookupHistory" :key="item.id">
              <button
                type="button"
                @click="
                  currentExplanation = item;
                  explanationModalVisible = true
                "
              >
                <strong>{{ item.selected_text }}</strong>
                <span>{{ item.explanation?.slice(0, 80) || 'Tap to open' }}</span>
              </button>
            </li>
            <li v-if="lookupHistory.length === 0" style="color: var(--ink-soft); font-size: 0.85rem">
              No lookups yet.
            </li>
          </ul>
          <button
            type="button"
            class="review-link md:hidden"
            @click="showHistoryPanel = true"
          >
            Open notes <span aria-hidden="true">→</span>
          </button>
          <button
            v-if="isGameEnded"
            type="button"
            class="la-btn review-vocab-btn"
            :disabled="isLoading || !canOpenVocabularyReview"
            :title="!canOpenVocabularyReview ? 'Look up at least one word during the game to use review.' : undefined"
            @click="router.push({ name: 'game-quiz', params: { id: route.params.id } })"
          >
            Review vocabulary
          </button>
        </div>
      </aside>
    </div>

    <Dialog :open="nativeLanguagePromptOpen" @update:open="nativeLanguagePromptOpen = $event">
      <DialogContent class="bg-[var(--paper)] text-[var(--ink)] border-[var(--line)]">
        <DialogHeader>
          <DialogTitle>Choose your explanation language</DialogTitle>
          <DialogDescription>
            Word explanations will be written in this language. You can change it anytime from the gear button in the lookup panel.
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-2 py-2">
          <label class="text-sm font-medium">Explanation language</label>
          <Select v-model="nativeLanguageChoiceForPrompt">
            <SelectTrigger class="w-full">
              <SelectValue placeholder="Select a language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="opt in NATIVE_LANGUAGE_OPTIONS"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="flex items-start gap-2 pb-2">
          <input
            id="native-language-persist"
            type="checkbox"
            class="mt-1 h-4 w-4"
            v-model="nativeLanguagePersistToProfile"
          />
          <label for="native-language-persist" class="text-sm text-muted-foreground">
            Do not display this option next time (save to my profile).
            <span class="text-foreground">If unchecked, this is used only for the current game session.</span>
          </label>
        </div>
        <DialogFooter class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="outline" @click="nativeLanguagePromptOpen = false">
            Cancel
          </Button>
          <Button @click="confirmNativeLanguageAndLookup">
            Continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="showHistoryPanel">
      <DialogContent class="bg-[var(--paper)] text-[var(--ink)] border-[var(--line)]">
        <DialogHeader>
          <DialogTitle>Lookup History</DialogTitle>
        </DialogHeader>
        <ul class="note-list">
          <li v-for="item in lookupHistory" :key="item.id">
            <button
              type="button"
              @click="
                currentExplanation = item;
                explanationModalVisible = true;
                showHistoryPanel = false
              "
            >
              <strong>{{ item.selected_text }}</strong>
            </button>
          </li>
          <li v-if="lookupHistory.length === 0" style="color: var(--ink-soft)">
            Select text in the story to lookup
          </li>
        </ul>
      </DialogContent>
    </Dialog>

    <Dialog :open="explanationModalVisible" @update:open="explanationModalVisible = $event">
      <DialogContent class="bg-[var(--paper)] text-[var(--ink)] border-[var(--line)]">
        <DialogHeader>
          <DialogTitle>
            <div class="flex items-center space-x-2">
              <span>Lookup</span>
              <div
                v-if="currentExplanation?.status === 'streaming'"
                class="animate-spin rounded-full h-4 w-4 border-2 border-[var(--blue)] border-t-transparent"
              />
            </div>
          </DialogTitle>
        </DialogHeader>

        <div v-if="currentExplanation?.status === 'pending'" class="mb-4">
          Waiting for server response…
        </div>
        <div v-else-if="currentExplanation?.status === 'streaming'" class="mb-4 space-y-4">
          <div
            class="p-3 rounded text-sm"
            style="background: var(--paper-muted); border: 1px solid var(--line-soft)"
          >
            {{
              currentExplanation?.context_text.substring(
                0,
                currentExplanation?.context_text.indexOf(currentExplanation?.selected_text),
              )
            }}
            <strong style="color: var(--blue-deep)">{{ currentExplanation?.selected_text }}</strong>
            {{
              currentExplanation?.context_text.substring(
                currentExplanation?.context_text.indexOf(currentExplanation?.selected_text) +
                  currentExplanation?.selected_text.length,
              )
            }}
          </div>
          <div class="text-sm">
            <div class="font-extrabold mb-1">Explanation</div>
            <p>{{ currentExplanation?.explanation }}<span class="animate-pulse">▋</span></p>
          </div>
        </div>
        <div v-else class="space-y-4">
          <div
            class="p-3 rounded text-sm"
            style="background: var(--paper-muted); border: 1px solid var(--line-soft)"
          >
            {{
              currentExplanation?.context_text.substring(
                0,
                currentExplanation?.context_text.indexOf(currentExplanation?.selected_text),
              )
            }}
            <strong style="color: var(--blue-deep)">{{ currentExplanation?.selected_text }}</strong>
            {{
              currentExplanation?.context_text.substring(
                currentExplanation?.context_text.indexOf(currentExplanation?.selected_text) +
                  currentExplanation?.selected_text.length,
              )
            }}
          </div>
          <div class="text-sm">
            <div class="font-extrabold mb-1">Explanation</div>
            <div class="prose prose-sm dark:prose-invert max-w-none" v-html="renderedExplanation" />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
/* Add these styles to ensure proper mobile layout */
@media (max-width: 768px) {
  :deep(.prose) {
    max-width: 100%;
  }
}
</style>
