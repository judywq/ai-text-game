<template>
  <div class="story-image-container relative">
    <!-- Loading skeleton while image is loading -->
    <div v-if="isLoading && !hasError" class="image-skeleton">
      <div class="animate-pulse bg-muted rounded-lg w-full h-64 flex items-center justify-center">
        <span class="text-muted-foreground">Loading image...</span>
      </div>
    </div>

    <!-- Actual image - always in DOM so it can load, but hidden while loading -->
    <img
      v-if="imageUrl && !hasError"
      :src="imageUrl"
      :alt="alt"
      :class="[
        'story-image rounded-lg w-full transition-opacity duration-600',
        isLoading ? 'opacity-0 absolute top-0 left-0' : 'opacity-100'
      ]"
      @load="onImageLoad"
      @error="onImageError"
    />

    <!-- Error state -->
    <div v-if="hasError" class="image-error bg-muted rounded-lg w-full h-64 flex items-center justify-center">
      <span class="text-destructive">Failed to load image</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  imageUrl?: string
  alt?: string
}>()

const emit = defineEmits<{
  (e: 'loaded'): void
  (e: 'error'): void
}>()

const isLoading = ref(true)
const hasError = ref(false)

// Watch for image URL changes
watch(() => props.imageUrl, (newUrl) => {
  if (newUrl) {
    isLoading.value = true
    hasError.value = false
  } else {
    isLoading.value = true
  }
}, { immediate: true })

const onImageLoad = () => {
  isLoading.value = false
  emit('loaded')
}

const onImageError = () => {
  isLoading.value = false
  hasError.value = true
  emit('error')
}
</script>

<style scoped>
.story-image-container {
  width: 100%;
}

.story-image {
  object-fit: cover;
  max-height: 500px;
}

/* Fade-in animation for images */
.image-fade-enter-active {
  transition: opacity 0.6s ease-in;
}

.image-fade-enter-from {
  opacity: 0;
}

.image-fade-enter-to {
  opacity: 1;
}
</style>
