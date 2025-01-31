<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { useGameStream } from '@/composables/useGameStream'
import type { GameStory, GameInteraction } from '@/types/game'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast/use-toast'
import { Separator } from '@/components/ui/separator'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const story = ref<GameStory | null>(null)
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const pollInterval = ref<number | null>(null)
const currentWatcher = ref<(() => void) | null>(null)

const { streamingContent, startStream, stopStream } = useGameStream()

async function pollForUpdates() {
  if (!story.value?.id) return

  try {
    const updatedStory = await GameService.pollStoryUpdates(story.value.id)
    story.value = updatedStory

    // Check if we should stop polling
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

    // Check if there are no interactions and trigger system message
    if (story.value.interactions.length === 1 && story.value.interactions[0].role === 'system' && story.value.interactions[0].status === 'pending') {
      await startSystemMessage(storyId)
    }

    scrollToBottom()

    // Start polling if there are pending interactions
    const hasPendingInteractions = story.value.interactions.some(
      interaction => interaction.status === 'pending'
    )
    if (hasPendingInteractions) {
      pollInterval.value = setInterval(pollForUpdates, 2000) // Poll every 2 seconds
    }
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

  // Clean up previous watcher if it exists
  if (currentWatcher.value) {
    currentWatcher.value()
    currentWatcher.value = null
  }

  const input = userInput.value
  userInput.value = ''
  isLoading.value = true

  try {
    // Create a streaming interaction immediately
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

    // Add it to the story immediately
    story.value.interactions.push(pendingInteraction)
    scrollToBottom()

    // Start streaming
    const streamPromise = startStream(story.value.id, input)
    const streamingInteractionId = pendingInteraction.id

    // Create new watcher and store its cleanup function
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

    // Wait for completion
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
    // Clean up the watcher
    if (currentWatcher.value) {
      currentWatcher.value()
      currentWatcher.value = null
    }
    isLoading.value = false
    stopStream()
  }
}

// Add new function to handle system message
async function startSystemMessage(storyId: number) {
  try {
    // Get the existing system interaction
    const systemInteraction = story.value?.interactions[0]
    if (!systemInteraction) {
      throw new Error('No system interaction found')
    }

    // Create a streaming interaction based on the existing one
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

    // Replace the existing interaction with the streaming one
    if (story.value) {
      const index = story.value.interactions.findIndex(i => i.id === systemInteraction.id)
      if (index >= 0) {
        story.value.interactions[index] = pendingInteraction
      }
    }
    scrollToBottom()

    // Start streaming
    const streamPromise = startStream(storyId, '', true)
    const streamingInteractionId = pendingInteraction.id

    // Create new watcher for streaming content
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

    // Wait for completion
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
  // Return the lines joined with <br> tags for line breaks
  return interaction.system_output.split('\n').join('<br>')
}
</script>

<template>
  <div class="container mx-auto py-8 max-w-4xl">
    <Card class="h-[800px] flex flex-col">
      <CardContent class="flex-1 p-6 flex flex-col overflow-hidden">
        <!-- Story Header -->
        <div v-if="story" class="mb-6">
          <h2 class="text-2xl font-bold">{{ story.title }}</h2>
          <!-- <p class="text-muted-foreground">{{ story.scenario.description }}</p> -->
        </div>

        <Separator />

        <!-- Chat Messages -->
        <ScrollArea ref="scrollRef" class="flex-1 h-full pr-4 pt-4">
          <div v-if="story" class="space-y-2">
            <div v-for="interaction in story.interactions" :key="interaction.id" class="space-y-2">
              <!-- User Message -->
              <div v-if="interaction.system_input" class="flex justify-end">
                <div class="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                  {{ interaction.system_input }}
                </div>
              </div>

              <!-- System Response -->
              <div class="flex">
                <div class="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
                  <div v-if="interaction.status === 'streaming'">
                    {{ interaction.system_output }}<span class="animate-pulse">▋</span>
                  </div>
                  <div v-else-if="interaction.status === 'failed'" class="text-destructive">
                    Failed to generate response. Please try again.
                  </div>
                  <div v-else v-html="formatMessage(interaction)" />
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <!-- Input Area -->
        <div class="mt-4 space-y-4">
          <Textarea
            v-model="userInput"
            placeholder="What would you like to do?"
            :disabled="isLoading"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="flex justify-end space-x-2">
            <Button
              variant="outline"
              :disabled="isLoading"
              @click="router.push('/game')"
            >
              Exit Game
            </Button>
            <Button
              :disabled="isLoading || !userInput.trim()"
              @click="sendMessage"
            >
              Send
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
