<template>
  <LoadingScreen
    :is-ready="isStoryReady"
    :initialization-message="initMessage"
    @start-game="startGame"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameWebSocket } from '@/composables/useGameWebSocket'
import { GameService } from '@/services/gameService'
import LoadingScreen from '@/components/LoadingScreen.vue'

const route = useRoute()
const router = useRouter()

const isStoryReady = ref(false)
const initMessage = ref('Initializing your story...')
const storyId = ref<number | null>(null)

const {
  isConnected,
  connect,
  startStory,
  onStoryUpdate,
  onError
} = useGameWebSocket()

// Handle when story update arrives (initialization complete)
onStoryUpdate.value = () => {
  isStoryReady.value = true
  initMessage.value = 'Your story is ready!'
}

// Handle errors
onError.value = (error: Error) => {
  console.error('WebSocket error:', error)
  initMessage.value = 'Error initializing story. Please try again.'
}

const initializeStory = async () => {
  try {
    // Get story ID from route params
    const id = parseInt(route.params.id as string)
    storyId.value = id

    // Fetch story details
    const story = await GameService.getStory(id)

    // Connect WebSocket
    connect(id)

    // Wait for connection
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'))
      }, 10000)

      const checkConnection = setInterval(() => {
        if (isConnected.value) {
          clearInterval(checkConnection)
          clearTimeout(timeout)
          resolve()
        }
      }, 100)
    })

    // Start the story (triggers backend to generate first content)
    await startStory(id)
  } catch (error) {
    console.error('Failed to initialize story:', error)
    initMessage.value = 'Failed to initialize story. Please try again.'
  }
}

const startGame = () => {
  if (isStoryReady.value && storyId.value) {
    // Navigate to actual game view
    router.push({ name: 'game-play', params: { id: storyId.value } })
  }
}

onMounted(() => {
  initializeStory()
})
</script>
