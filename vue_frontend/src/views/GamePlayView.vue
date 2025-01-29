<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import type { GameStory, GameInteraction } from '@/types/game'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast/use-toast'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const story = ref<GameStory | null>(null)
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)

onMounted(async () => {
  const storyId = Number(route.params.id)
  if (!storyId) {
    router.push('/game')
    return
  }

  try {
    story.value = await GameService.getStory(storyId)
    scrollToBottom()
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to load story',
      variant: 'destructive',
    })
    router.push('/game')
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

  const input = userInput.value
  userInput.value = ''
  isLoading.value = true

  try {
    const interaction = await GameService.interact(story.value.id, input)
    story.value.interactions.push(interaction)
    scrollToBottom()
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to send message',
      variant: 'destructive',
    })
    userInput.value = input // Restore the input if failed
  } finally {
    isLoading.value = false
  }
}

function formatMessage(interaction: GameInteraction) {
  // Return the lines joined with <br> tags for line breaks
  return interaction.system_response.split('\n').join('<br>')
}
</script>

<template>
  <div class="container mx-auto py-8 max-w-4xl">
    <Card class="h-[800px] flex flex-col">
      <CardContent class="flex-1 p-6 flex flex-col">
        <!-- Story Header -->
        <div v-if="story" class="mb-6">
          <h2 class="text-2xl font-bold">{{ story.scenario.title }}</h2>
          <p class="text-muted-foreground">{{ story.scenario.description }}</p>
        </div>

        <!-- Chat Messages -->
        <ScrollArea ref="scrollRef" class="flex-1 pr-4">
          <div v-if="story" class="space-y-6">
            <template v-for="interaction in story.interactions" :key="interaction.id">
              <!-- User Message -->
              <div class="flex justify-end">
                <div class="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                  {{ interaction.user_input }}
                </div>
              </div>

              <!-- System Response -->
              <div class="flex">
                <div class="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
                  <div v-if="interaction.status === 'pending'">
                    Thinking...
                  </div>
                  <div v-else-if="interaction.status === 'failed'" class="text-destructive">
                    Failed to generate response. Please try again.
                  </div>
                  <div v-else v-html="formatMessage(interaction)" />
                </div>
              </div>
            </template>
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
