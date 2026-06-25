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
  connect,
  startStory,
  onStoryUpdate,
  onError,
  onSkeletonGenerationStarted,
} = useGameWebSocket()

onStoryUpdate.value = () => {
  isStoryReady.value = true
  initMessage.value = 'Your story is ready!'
}

onSkeletonGenerationStarted.value = (message: string) => {
  initMessage.value = message || 'Generating story structure...'
}

onError.value = (error: Error) => {
  console.error('WebSocket error:', error)
  initMessage.value = 'Error initializing story. Please try again.'
}

const initializeStory = async () => {
  try {
    const id = parseInt(route.params.id as string)
    storyId.value = id

    await GameService.getStory(id)
    await connect(id)
    await startStory()
  } catch (error) {
    console.error('Failed to initialize story:', error)
    initMessage.value = 'Failed to initialize story. Please try again.'
  }
}

const startGame = () => {
  if (isStoryReady.value && storyId.value) {
    router.push({ name: 'game-play', params: { id: storyId.value } })
  }
}

onMounted(() => {
  initializeStory()
})
</script>
