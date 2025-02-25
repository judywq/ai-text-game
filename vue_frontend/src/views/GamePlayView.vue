<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { ExplanationService } from '@/services/explanationService'
import type { GameStory, StoryProgress } from '@/types/game'
import type { TextExplanation, ExplanationStatus } from '@/types/explanation'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast/use-toast'
import { Separator } from '@/components/ui/separator'
import { useGameWebSocket } from '@/composables/useGameWebSocket'
import { marked } from 'marked'
import { CircleHelp } from 'lucide-vue-next'
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

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const story = ref<GameStory | null>(null)
const progressEntries = ref<StoryProgress[]>([])
const userInput = ref('')
const isLoading = ref(false)
const isInitializing = ref(false)
const scrollRef = ref<HTMLElement | null>(null)

const {
  isConnected,
  connect,
  selectOption,
  startStory,
  lookupExplanation,
  onStream,
  onStoryUpdate,
  onExplanationCreated,
  onExplanationStream,
  onExplanationStatus,
  onExplanationCompleted
} = useGameWebSocket()

const currentOptions = ref<StoryOption[]>([])
const rawSelection = ref('')
const contextSelection = ref('')
const popupPosition = ref({ x: 0, y: 0 })
const showLookupButton = ref(false)
const explanationModalVisible = ref(false)
const currentExplanation = ref<TextExplanation | null>(null)
const lookupHistory = ref<TextExplanation[]>([])

// Add reactive variable for mobile lookup history panel
const showHistoryPanel = ref(false)

// Add this watch after the ref declarations
watch(progressEntries, (entries) => {
  if (entries.length > 0) {
    const lastEntry = entries[entries.length - 1]
    // Only show options if there's no chosen option yet
    if (!lastEntry.chosen_option_text) {
      currentOptions.value = lastEntry.options || []
    } else {
      currentOptions.value = []
    }
  } else {
    currentOptions.value = []
  }
}, { deep: true })

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

function handleTextSelection(e: MouseEvent) {
  const sel = window.getSelection();
  if (!sel || sel.toString().trim().length === 0) {
    showLookupButton.value = false;
    return;
  }

  // If selection spans different nodes, refuse the request
  if (sel.anchorNode !== sel.focusNode) {
    toast({
      title: 'Error',
      description: 'Please select text within a single message!',
      variant: 'destructive',
    });
    sel.removeAllRanges();
    showLookupButton.value = false;
    return;
  }

  const range = sel.getRangeAt(0);
  rawSelection.value = sel.toString().trim();
  contextSelection.value = extractSentenceFromRange(range);

  // Calculate popup position relative to the scroll container including its scroll offsets.
  const containerRect = scrollRef.value?.getBoundingClientRect();
  if (containerRect && scrollRef.value) {
    const scrollLeft = scrollRef.value.scrollLeft;
    const scrollTop = scrollRef.value.scrollTop;
    popupPosition.value = {
      x: e.clientX - containerRect.left + scrollLeft,
      y: e.clientY - containerRect.top + scrollTop,
    }
  } else {
    popupPosition.value = {
      x: e.clientX,
      y: e.clientY,
    }
  }

  showLookupButton.value = true;
}

function clearTextSelection() {
  rawSelection.value = ''
  contextSelection.value = ''
  showLookupButton.value = false
}

async function lookupExplanationSubmit() {
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
      clientId
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

async function fetchLookupHistory() {
  if (!story.value) return;
  try {
    const history = await ExplanationService.getLookupHistory(story.value.id)
    lookupHistory.value = history
  } catch (error) {
    console.error("Failed to fetch lookup history", error)
  }
}

const loadStory = async () => {
  try {
    isInitializing.value = true
    const storyId = parseInt(route.params.id as string)
    story.value = await GameService.getStory(storyId)
    progressEntries.value = await GameService.getStoryProgress(storyId)

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
    if (progressEntries.value.length === 0 && story.value.status === 'INIT') {
      await startStory(storyId)
    }
  } catch (error: any) {
    console.error('Failed to load story', error)
    toast({
      title: 'Error',
      description: error.message || 'Failed to load story',
      variant: 'destructive',
    })
    router.push('/game')
  } finally {
    isInitializing.value = false
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

    // Send the selection to the server
    await selectOption(optionId)

  } catch (error: any) {
    toast({
      title: 'Error',
      description: 'Failed to select option',
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

    onStoryUpdate.value = (update: any) => {
      console.log('onStoryUpdate', update)

      // Create a new progress entry
      if (update.content) {
        progressEntries.value.push({
          id: Date.now(), // Temporary ID for frontend
          content: update.content,
          chosen_option_text: update.chosen_option_text || '',
          options: update.options || [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
      }

      scrollToBottom()

      // Update story status if provided
      if (update.status) {
        story.value.status = update.status
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
        >
          <div v-if="story" class="space-y-2 pt-4 px-4 pb-4">
            <!-- Add loading state -->
            <div v-if="isInitializing && progressEntries.length === 0" class="flex flex-col items-center justify-center h-[200px] space-y-4">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
              <p class="text-muted-foreground">Initializing your story...</p>
            </div>

            <!-- Existing progress entries display -->
            <div v-else v-for="entry in progressEntries" :key="entry.id" class="space-y-2">
              <div class="prose dark:prose-invert">
                <div v-html="marked(entry.content)" />
                <div v-if="entry.chosen_option_text" class="text-sm text-muted-foreground mt-2">
                  You chose: {{ entry.chosen_option_text }}
                </div>
              </div>
            </div>
          </div>

          <!-- Lookup button remains within interaction area for text selection -->
          <div v-if="showLookupButton"
            :style="{ position: 'absolute', top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
            <Button variant="outline" size="icon" @click="lookupExplanationSubmit">
              <CircleHelp class="w-4 h-4" />
            </Button>
          </div>
        </div>

        <!-- Story Options -->
        <div class="px-4">
          <StoryOptions
            :options="currentOptions"
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
            <h4 class="font-bold text-lg mb-2">Lookup History</h4>
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
