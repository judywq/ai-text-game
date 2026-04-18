<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { ExplanationService } from '@/services/explanationService'
import type { GameStory, StoryProgress, StoryOption, TextExplanation, ExplanationStatus, StoryUpdate } from '@/types/game'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast/use-toast'
import { Separator } from '@/components/ui/separator'
import { useGameWebSocket } from '@/composables/useGameWebSocket'
import { marked } from 'marked'
import { CircleHelp } from 'lucide-vue-next'
import StorySegment from '@/components/StorySegment.vue'
import StoryOptions from '@/components/StoryOptions.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)

const {
  isConnected,
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
  onError
} = useGameWebSocket()

const currentOptions = ref<StoryOption[]>([])
const rawSelection = ref('')
const contextSelection = ref('')
const popupPosition = ref({ x: 0, y: 0 })
const showLookupButton = ref(false)
const explanationModalVisible = ref(false)
const currentExplanation = ref<TextExplanation | null>(null)
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

// Computed property to determine if options should be shown
const shouldShowOptions = computed(() => {
  if (progressEntries.value.length === 0) return false
  const lastEntry = progressEntries.value[progressEntries.value.length - 1]
  const lastEntryIndex = progressEntries.value.length - 1

  // Show options only if:
  // 1. Content is ready (streaming complete and refetch done)
  // 2. No option has been chosen yet
  // 3. All paragraphs have been shown
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

function finalizeStoryStream() {
  const update = pendingStoryUpdate.value
  if (!update) {
    return
  }

  const latestEntryIndex = activeStreamingEntryIndex.value ?? (progressEntries.value.length - 1)
  const latestEntry = latestEntryIndex >= 0 ? progressEntries.value[latestEntryIndex] : null

  allParagraphsShown.value = false

  if (latestEntry) {
    latestEntry.decision_point_id = update.current_decision || ''
    latestEntry.options = update.options || []
    isContentReady.value[latestEntryIndex] = true
  }

  if (update.status && story.value) {
    story.value.status = update.status as GameStory['status']
  }

  currentStreamingContent.value = ''
  pendingStreamingBuffer.value = ''
  activeStreamingEntryIndex.value = null
  pendingStoryUpdate.value = null
  stopStreamRenderTimer()
  scrollToBottom()
}

function flushStreamingBuffer() {
  if (!pendingStreamingBuffer.value) {
    stopStreamRenderTimer()
    finalizeStoryStream()
    return
  }

  const nextChunk = pendingStreamingBuffer.value.slice(0, STREAM_REVEAL_CHUNK_SIZE)
  pendingStreamingBuffer.value = pendingStreamingBuffer.value.slice(nextChunk.length)
  currentStreamingContent.value += nextChunk
  syncVisibleStreamingContent()
  scrollToBottom()

  if (!pendingStreamingBuffer.value && pendingStoryUpdate.value) {
    finalizeStoryStream()
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
}

const loadStory = async () => {
  try {
    const storyId = parseInt(route.params.id as string)
    await fetchStoryAndProgress()

    // Connect WebSocket and wait for connection
    await connect(storyId)

    // Wait for WebSocket connection to be established
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'))
      }, 5000)

      const checkConnection = setInterval(() => {
        if (isConnected.value) {
          clearInterval(checkConnection)
          clearTimeout(timeout)
          resolve()
        }
      }, 100)
    })

    // Start story if no progress exists
    if (progressEntries.value.length === 0 && story.value?.status === 'INIT') {
      await startStory(storyId)
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
        finalizeStoryStream()
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
  <div class="container mx-auto max-w-6xl md:pt-6 h-[calc(100vh-64px)] flex flex-col">
    <!-- Flex container: Game area and Lookup History side by side -->
    <div class="flex flex-col md:flex-row md:space-x-4 flex-1 overflow-hidden">
      <div class="flex-1 flex flex-col h-full border border-transparent overflow-hidden">
        <div class="py-4 border-b flex-shrink-0">
          <div v-if="story">
            <h2 class="text-2xl font-bold">{{ story.title }}</h2>
          </div>
        </div>

        <!-- Update the Interaction Area for better mobile handling -->
        <div
          class="flex-1 relative overflow-y-auto"
          ref="scrollRef"
          @mouseup="handleTextSelection"
          @touchend="handleTextSelection"
        >
          <div v-if="story" class="space-y-6 pt-4 px-4 pb-4">
            <!-- Add loading state -->
            <div v-if="progressEntries.length === 0" class="flex flex-col items-center justify-center h-[200px] space-y-4">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
              <p class="text-muted-foreground">Initializing your story...</p>
            </div>

            <!-- Story segments using new component -->
            <div v-else>
              <StorySegment
                v-for="(entry, entryIndex) in progressEntries"
                :key="entry.id"
                :entry="entry"
                :is-latest="entryIndex === progressEntries.length - 1"
                :is-content-ready="isContentReady[entryIndex] || false"
                @all-paragraphs-shown="onAllParagraphsShown"
              />

              <!-- Loading spinner after option selection -->
              <div v-if="isLoading" class="flex flex-col items-center justify-center py-8 space-y-4">
                <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
                <p class="text-muted-foreground">Generating next part...</p>
              </div>
            </div>
          </div>

          <!-- Lookup button remains within interaction area for text selection -->
          <div v-if="showLookupButton"
            :style="{ position: 'absolute', top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
            <Button variant="outline" size="icon" @click="lookupExplanationSubmit" @touchend.stop="lookupExplanationSubmit">
              <CircleHelp class="w-4 h-4" />
            </Button>
          </div>
        </div>

        <!-- Story Options -->
        <div class="px-4">
          <StoryOptions
            v-if="shouldShowOptions"
            :options="currentOptions"
            :disabled="false"
            @select="handleOptionSelect"
          />
        </div>

        <!-- Update the input area to stay fixed at bottom -->
        <div class="py-4 border-t bg-background flex-shrink-0">
          <!-- <Textarea
            v-model="userInput"
            placeholder="What would you like to do?"
            @keydown.enter.exact.prevent="handleOptionSelect"
            class="min-h-[80px]"
          /> -->
          <div class="flex justify-end space-x-2 mt-2">
            <Button
              class="md:hidden"
              variant="outline"
              @click="showHistoryPanel = true"
            >
              History
            </Button>
            <Button
              v-if="isGameEnded"
              variant="secondary"
              :disabled="isLoading || !canOpenVocabularyReview"
              :title="!canOpenVocabularyReview ? 'Look up at least one word during the game to use review.' : undefined"
              @click="router.push({ name: 'game-quiz', params: { id: route.params.id } })"
            >
              Review
            </Button>
            <Button
              variant="outline"
              :disabled="isLoading"
              @click="router.push('/game')"
            >
              Exit Game
            </Button>
            <!-- <Button
              :disabled="isLoading || !userInput.trim()"
              @click="handleOptionSelect"
            >
              Send
            </Button> -->
          </div>
        </div>
      </div>

      <!-- Desktop: Lookup History panel -->
      <div class="hidden md:block w-[240px]">
        <div class="bg-white rounded-lg shadow h-full overflow-auto">
          <div class="p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-bold text-lg">Lookup History</h4>
              <Button
                variant="ghost"
                size="icon"
                class="h-8 w-8"
                title="Language settings"
                @click="openNativeLanguageSettings"
              >
                <Settings class="h-4 w-4" />
              </Button>
            </div>
            <Separator />
            <ul>
              <li v-for="item in lookupHistory" :key="item.id" class="mb-2 cursor-pointer hover:bg-gray-100 p-2 rounded"
                @click="currentExplanation = item; explanationModalVisible = true">
                <div class="text-sm font-medium truncate">{{ item.selected_text }}</div>
              </li>
              <li v-if="lookupHistory.length === 0" class="text-sm text-gray-500">Select text in the story to lookup
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <Dialog :open="nativeLanguagePromptOpen" @update:open="nativeLanguagePromptOpen = $event">
      <DialogContent>
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

    <!-- Mobile: Modal for Lookup History -->
    <Dialog v-model:open="showHistoryPanel">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Lookup History</DialogTitle>
        </DialogHeader>

        <ul>
          <li v-for="item in lookupHistory"
              :key="item.id"
              class="mb-2 cursor-pointer hover:bg-gray-100 p-2 rounded"
              @click="currentExplanation = item; explanationModalVisible = true; showHistoryPanel = false">
            <div class="text-sm font-medium truncate">{{ item.selected_text }}</div>
          </li>
          <li v-if="lookupHistory.length === 0" class="text-sm text-gray-500">
            Select text in the story to lookup
          </li>
        </ul>
      </DialogContent>
    </Dialog>

    <!-- Explanation details -->
    <Dialog :open="explanationModalVisible" @update:open="explanationModalVisible = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            <div class="flex items-center space-x-2">
              <span>Lookup</span>
              <div v-if="currentExplanation?.status === 'streaming'" class="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div v-if="currentExplanation?.status === 'pending'" class="mb-4 flex items-center space-x-2">
          <span>Waiting for server response...</span>
        </div>
        <div v-else-if="currentExplanation?.status === 'streaming'" class="mb-4">
          <!-- Show streaming content -->
          <div class="space-y-4">
            <div class="bg-muted p-3 rounded text-sm">
              {{ currentExplanation?.context_text.substring(0, currentExplanation?.context_text.indexOf(currentExplanation?.selected_text)) }}
              <strong class="text-primary">{{ currentExplanation?.selected_text }}</strong>
              {{ currentExplanation?.context_text.substring(currentExplanation?.context_text.indexOf(currentExplanation?.selected_text) + currentExplanation?.selected_text.length) }}
            </div>
            <div class="text-sm">
              <div class="font-medium mb-1">Explanation:</div>
              <p>{{ currentExplanation?.explanation }}<span class="animate-pulse">▋</span></p>
            </div>
          </div>
        </div>
        <div v-else class="space-y-4">
          <!-- Context with highlighted selection -->
          <div class="bg-muted p-3 rounded text-sm">
            {{ currentExplanation?.context_text.substring(0, currentExplanation?.context_text.indexOf(currentExplanation?.selected_text)) }}
            <strong class="text-primary">{{ currentExplanation?.selected_text }}</strong>
            {{ currentExplanation?.context_text.substring(currentExplanation?.context_text.indexOf(currentExplanation?.selected_text) + currentExplanation?.selected_text.length) }}
          </div>

          <!-- Explanation -->
          <div class="text-sm">
            <div class="font-medium mb-1">Explanation:</div>
            <p>{{ currentExplanation?.explanation }}</p>
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
