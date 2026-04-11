<template>
  <div class="fixed inset-0 flex items-center justify-center bg-background">
    <div class="max-w-4xl w-full px-8 flex flex-col items-center space-y-8">
      <!-- Image and Text Display -->
      <div class="relative w-full aspect-video rounded-lg overflow-hidden shadow-2xl">
        <transition name="fade" mode="out-in">
          <img
            :key="currentIndex"
            :src="currentAsset.image"
            :alt="`Loading screen ${currentIndex + 1}`"
            class="w-full h-full object-cover"
          />
        </transition>
      </div>

      <!-- Text Content -->
      <transition name="fade" mode="out-in">
        <div :key="currentIndex" class="text-center space-y-4">
          <p class="text-lg text-foreground whitespace-pre-line">{{ currentAsset.text }}</p>
        </div>
      </transition>

      <!-- Initialization Status -->
      <div class="flex flex-col items-center space-y-4">
        <div v-if="!isReady" class="flex items-center space-x-3">
          <div class="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
          <p class="text-muted-foreground">{{ initializationMessage }}</p>
        </div>

        <!-- Start Game Button - only visible when ready -->
        <Button
          v-if="isReady"
          @click="$emit('start-game')"
          size="lg"
          class="px-8 py-6 text-lg"
        >
          Start Game
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Button } from '@/components/ui/button'

interface LoadingAsset {
  image: string
  text: string
}

defineProps<{
  isReady: boolean
  initializationMessage?: string
}>()

defineEmits<{
  (e: 'start-game'): void
}>()

const currentIndex = ref(0)
const loadingAssets = ref<LoadingAsset[]>([])

// Load all assets from public folder
const loadAssets = async () => {
  const assets: LoadingAsset[] = []

  // Load 3 image/text pairs
  for (let i = 1; i <= 3; i++) {
    try {
      const imageUrl = `/loading-assets/image${i}.png`
      const textResponse = await fetch(`/loading-assets/text${i}.txt`)
      const textContent = await textResponse.text()

      assets.push({
        image: imageUrl,
        text: textContent.trim()
      })
    } catch (error) {
      console.error(`Failed to load asset ${i}:`, error)
    }
  }

  loadingAssets.value = assets
}

const currentAsset = computed(() => {
  if (loadingAssets.value.length === 0) {
    return { image: '', text: '' }
  }
  return loadingAssets.value[currentIndex.value]
})

let rotationInterval: number | null = null

onMounted(async () => {
  await loadAssets()

  // Rotate images every 12 seconds
  rotationInterval = window.setInterval(() => {
    if (loadingAssets.value.length > 0) {
      currentIndex.value = (currentIndex.value + 1) % loadingAssets.value.length
    }
  }, 12000)
})

onUnmounted(() => {
  if (rotationInterval) {
    clearInterval(rotationInterval)
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.8s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
