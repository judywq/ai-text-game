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

const markStoryReady = () => {
  isStoryReady.value = true
  initMessage.value = 'Your story is ready!'
}

onStoryUpdate.value = () => {
  markStoryReady()
}

onSkeletonGenerationStarted.value = (message: string) => {
  initMessage.value = message || 'Generating story structure...'
}

onError.value = (error: Error) => {
  if (error.message === 'Story already started.') {
    markStoryReady()
    return
  }
  console.error('WebSocket error:', error)
  initMessage.value = 'Error initializing story. Please try again.'
}

const initializeStory = async () => {
  try {
    const id = parseInt(route.params.id as string)
    storyId.value = id

    const story = await GameService.getStory(id)
    if (story.status !== 'INIT') {
      markStoryReady()
      return
    }

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
