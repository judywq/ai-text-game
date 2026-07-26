<template>
  <div class="story-image-container relative">
    <!-- Loading skeleton while image is loading -->
    <div v-if="isLoading && !hasError" class="image-skeleton">
      <div class="animate-pulse bg-muted rounded-lg aspect-[3/4] w-full max-h-full flex items-center justify-center">
        <span class="text-muted-foreground">Loading image...</span>
      </div>
    </div>

    <!-- Actual image - always in DOM so it can load, but out of layout while loading -->
    <img
      v-if="imageUrl && !hasError"
      :src="imageUrl"
      :alt="alt"
      :class="[
        'story-image rounded-lg w-full transition-opacity duration-600',
        isLoading ? 'hidden' : 'opacity-100 cursor-pointer'
      ]"
      @load="onImageLoad"
      @error="onImageError"
      @click="openFullscreen"
    />

    <!-- Error state -->
    <div v-if="hasError" class="image-error bg-muted rounded-lg aspect-[3/4] w-full max-h-full flex items-center justify-center">
      <span class="text-destructive">Failed to load image</span>
    </div>

    <Dialog :open="isFullscreenOpen" @update:open="isFullscreenOpen = $event">
      <DialogContent
        class="fullscreen-image-dialog max-w-[95vw] max-h-[95vh] w-auto h-auto p-0 border-0 bg-transparent shadow-none"
      >
        <DialogTitle class="sr-only">{{ alt || 'Story image' }}</DialogTitle>
        <img
          :src="imageUrl"
          :alt="alt"
          class="max-w-[95vw] max-h-[95vh] object-contain"
        />
      </DialogContent>
    </Dialog>

    <Teleport to="body">
      <button
        v-if="isFullscreenOpen"
        type="button"
        class="fullscreen-image-close"
        aria-label="Close"
        @click="isFullscreenOpen = false"
      >
        <X class="w-5 h-5" />
      </button>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'

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
const isFullscreenOpen = ref(false)

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

const openFullscreen = () => {
  if (!isLoading.value && !hasError.value) {
    isFullscreenOpen.value = true
  }
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

<!-- Unscoped: DialogContent teleports outside this component -->
<style>
/* Hide DialogContent's built-in close (positioned on the image) */
.fullscreen-image-dialog > button {
  display: none;
}

.fullscreen-image-close {
  position: fixed;
  right: 1rem;
  top: 1rem;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  color: white;
  background: rgb(0 0 0 / 0.5);
  border: none;
  border-radius: 9999px;
  cursor: pointer;
}

.fullscreen-image-close:hover {
  background: rgb(0 0 0 / 0.7);
}
</style>
