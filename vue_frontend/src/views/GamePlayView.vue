<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { ExplanationService } from '@/services/explanationService'
import type { GameStory, GameInteraction } from '@/types/game'
import type { TextExplanation } from '@/types/explanation'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast/use-toast'
import { Separator } from '@/components/ui/separator'
import { useGameStream } from '@/composables/useGameStream'
import { marked } from 'marked'
import { CircleHelp } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const story = ref<GameStory | null>(null)
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const pollInterval = ref<ReturnType<typeof setInterval> | null>(null)
const currentWatcher = ref<(() => void) | null>(null)

const { streamingContent, startStream, stopStream } = useGameStream()

const rawSelection = ref('')
const contextSelection = ref('')
const popupPosition = ref({ x: 0, y: 0 })
const showLookupButton = ref(false)
const explanationModalVisible = ref(false)
const currentExplanation = ref<TextExplanation | null>(null)
const lookupHistory = ref<TextExplanation[]>([])

// Add reactive variable for mobile lookup history panel
const showHistoryPanel = ref(false)

// Add new polling interval for explanations
const explanationPollInterval = ref<ReturnType<typeof setInterval> | null>(null)

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
    const result = await ExplanationService.lookupExplanation(story.value.id, rawSelection.value, contextSelection.value)
    currentExplanation.value = result

    // Start polling if explanation is pending
    if (result.status === 'pending') {
      explanationModalVisible.value = true
      startExplanationPolling(result.id)
    } else {
      explanationModalVisible.value = true
      fetchLookupHistory()
    }
  } catch (error: any) {
    toast({
      title: 'Error',
      description: 'Failed to lookup explanation',
      variant: 'destructive',
    })
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

async function pollForUpdates() {
  if (!story.value?.id) return

  try {
    const updatedStory = await GameService.pollStoryUpdates(story.value.id)
    story.value = updatedStory

    const pendingInteractions = updatedStory.interactions.some(
      interaction => interaction.status === 'pending'
    )
    if (!pendingInteractions && pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }

    scrollToBottom()
  } catch (error) {
    console.error('Failed to poll for updates:', error)
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
  }
}

onMounted(async () => {
  const storyId = Number(route.params.id)
  if (!storyId) {
    router.push('/game')
    return
  }

  try {
    story.value = await GameService.getStory(storyId)

    if (story.value.interactions.length === 1 && story.value.interactions[0].role === 'system' && story.value.interactions[0].status === 'pending') {
      await startSystemMessage(storyId)
    }

    scrollToBottom()

    const hasPendingInteractions = story.value.interactions.some(
      interaction => interaction.status === 'pending'
    )
    if (hasPendingInteractions) {
      pollInterval.value = setInterval(pollForUpdates, 2000)
    }
    fetchLookupHistory()
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to load story',
      variant: 'destructive',
    })
    router.push('/game')
  }
})

onUnmounted(() => {
  stopStream()
  stopExplanationPolling()
  if (currentWatcher.value) {
    currentWatcher.value()
  }
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
})

function scrollToBottom() {
  setTimeout(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  }, 100)
}

async function sendMessage() {
  if (!userInput.value.trim() || !story.value) return

  if (currentWatcher.value) {
    currentWatcher.value()
    currentWatcher.value = null
  }

  const input = userInput.value
  userInput.value = ''
  isLoading.value = true

  try {
    const pendingInteraction: GameInteraction = {
      id: Date.now(),
      story: story.value.id,
      role: 'user',
      system_input: input,
      system_output: '',
      status: 'streaming',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    story.value.interactions.push(pendingInteraction)
    scrollToBottom()

    const streamPromise = startStream(story.value.id, input)
    const streamingInteractionId = pendingInteraction.id

    currentWatcher.value = watch(streamingContent, (newContent) => {
      if (story.value) {
        const streamingInteraction = story.value.interactions.find(
          i => i.id === streamingInteractionId
        )
        if (streamingInteraction) {
          streamingInteraction.system_output = newContent
          scrollToBottom()
        }
      }
    })

    const completedInteraction = await streamPromise
    if (story.value) {
      const index = story.value.interactions.findIndex(
        i => i.id === streamingInteractionId
      )
      if (index >= 0) {
        story.value.interactions[index] = completedInteraction
      }
    }

  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to send message',
      variant: 'destructive',
    })
    if (story.value) {
      story.value.interactions = story.value.interactions.filter(
        i => i.id !== Date.now()
      )
    }
    userInput.value = input
  } finally {
    if (currentWatcher.value) {
      currentWatcher.value()
      currentWatcher.value = null
    }
    isLoading.value = false
    stopStream()
  }
}

async function startSystemMessage(storyId: number) {
  try {
    const systemInteraction = story.value?.interactions[0]
    if (!systemInteraction) {
      throw new Error('No system interaction found')
    }
    const pendingInteraction: GameInteraction = {
      id: systemInteraction.id,
      story: storyId,
      role: 'system',
      system_input: '',
      system_output: '',
      status: 'streaming',
      created_at: systemInteraction.created_at,
      updated_at: systemInteraction.updated_at
    }
    if (story.value) {
      const index = story.value.interactions.findIndex(i => i.id === systemInteraction.id)
      if (index >= 0) {
        story.value.interactions[index] = pendingInteraction
      }
    }
    scrollToBottom()
    const streamPromise = startStream(storyId, '', true)
    const streamingInteractionId = pendingInteraction.id

    currentWatcher.value = watch(streamingContent, (newContent) => {
      if (story.value) {
        const streamingInteraction = story.value.interactions.find(
          i => i.id === streamingInteractionId
        )
        if (streamingInteraction) {
          streamingInteraction.system_output = newContent
          scrollToBottom()
        }
      }
    })

    const completedInteraction = await streamPromise
    if (story.value) {
      const index = story.value.interactions.findIndex(
        i => i.id === streamingInteractionId
      )
      if (index >= 0) {
        story.value.interactions[index] = completedInteraction
      }
    }

  } catch (error) {
    console.error('Failed to start system message:', error)
    toast({
      title: 'Error',
      description: 'Failed to start game',
      variant: 'destructive',
    })
  } finally {
    if (currentWatcher.value) {
      currentWatcher.value()
      currentWatcher.value = null
    }
    stopStream()
  }
}

function formatMessage(interaction: GameInteraction) {
  return marked(interaction.system_output)
}

// Add new polling function for explanations
async function pollExplanation(explanationId: number) {
  try {
    const explanation = await ExplanationService.getExplanation(story.value!.id, explanationId)
    if (explanation.status !== 'pending') {
      currentExplanation.value = explanation
      stopExplanationPolling()
      fetchLookupHistory()
    }
  } catch (error) {
    console.error('Failed to poll explanation:', error)
    stopExplanationPolling()
  }
}

function startExplanationPolling(explanationId: number) {
  if (explanationPollInterval.value) {
    clearInterval(explanationPollInterval.value)
  }
  explanationPollInterval.value = setInterval(() => pollExplanation(explanationId), 2000)
}

function stopExplanationPolling() {
  if (explanationPollInterval.value) {
    clearInterval(explanationPollInterval.value)
    explanationPollInterval.value = null
  }
}
</script>

<template>
  <div class="container mx-auto max-w-6xl md:pt-6" style="height: calc(100vh - 64px)">
    <!-- Flex container: Game area and Lookup History side by side -->
    <div class="flex flex-col md:flex-row md:space-x-4 h-full">
      <div class="flex-1 flex flex-col border border-transparent">
        <div class="py-4 border-b">
          <div v-if="story">
            <h2 class="text-2xl font-bold">{{ story.title }}</h2>
          </div>
        </div>

        <!-- Interaction Area (ScrollArea) -->
        <div class="flex-1 relative overflow-auto" ref="scrollRef" @mouseup="handleTextSelection">
          <div v-if="story" class="space-y-2 pt-4 pr-4">
            <div v-for="interaction in story.interactions" :key="interaction.id" class="space-y-2">
              <div v-if="interaction.system_input" class="flex justify-end">
                <div class="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                  {{ interaction.system_input }}
                </div>
              </div>

              <div class="flex">
                <div class="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
                  <div v-if="interaction.status === 'streaming'">
                    {{ interaction.system_output }}<span class="animate-pulse">▋</span>
                  </div>
                  <div v-else-if="interaction.status === 'failed'" class="text-destructive">
                    Failed to generate response. Please try again.
                  </div>
                  <div v-else class="prose dark:prose-invert" v-html="formatMessage(interaction)"></div>
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

        <!-- Message input and buttons fixed at bottom of game area -->
        <div class="py-4 border-t">
          <Textarea v-model="userInput" placeholder="What would you like to do?"
            @keydown.enter.exact.prevent="sendMessage" />
          <div class="flex justify-end space-x-2 mt-2">
            <!-- Mobile: Lookup History -->
            <Button class="md:hidden" variant="outline"
              @click="showHistoryPanel = true">
              History
            </Button>
            <Button variant="outline" :disabled="isLoading" @click="router.push('/game')">
              Exit Game
            </Button>
            <Button :disabled="isLoading || !userInput.trim()" @click="sendMessage">
              Send
            </Button>
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
    <div v-if="showHistoryPanel"
      class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 md:hidden">
      <div class="bg-white p-4 rounded shadow-lg w-11/12 max-h-[80vh] overflow-auto">
        <div class="flex justify-between items-center mb-4">
          <h4 class="font-bold text-lg">Lookup History</h4>
          <Button variant="outline" size="sm" @click="showHistoryPanel = false">Close</Button>
        </div>
        <Separator />
        <ul>
          <li v-for="item in lookupHistory" :key="item.id" class="mb-2 cursor-pointer hover:bg-gray-100 p-2 rounded"
            @click="currentExplanation = item; explanationModalVisible = true; showHistoryPanel = false">
            <div class="text-sm font-medium truncate">{{ item.selected_text }}</div>
          </li>
          <li v-if="lookupHistory.length === 0" class="text-sm text-gray-500">Select text in the story to lookup</li>
        </ul>
      </div>
    </div>

    <!-- Update Explanation modal to show loading state -->
    <div v-if="explanationModalVisible" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
      <div class="bg-white p-4 rounded shadow-lg max-w-md">
        <h3 class="font-bold mb-2">Explanation</h3>
        <div v-if="currentExplanation?.status === 'pending'" class="mb-4 flex items-center space-x-2">
          <div class="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
          <span>Generating explanation...</span>
        </div>
        <p v-else class="mb-4">{{ currentExplanation?.explanation }}</p>
        <Button @click="explanationModalVisible = false">Close</Button>
      </div>
    </div>
  </div>
</template>
