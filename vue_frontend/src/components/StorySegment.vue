<template>
  <div class="story-segment space-y-4">
    <!-- Loading state -->
    <div v-if="entry.content === 'LOADING'" class="flex flex-col items-center justify-center py-8 space-y-4">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
      <p class="text-muted-foreground">Getting new content...</p>
    </div>

    <!-- Normal content -->
    <template v-else>
      <!-- Image FIRST in HTML - hidden until loaded, then appears at top -->
      <div v-if="entry.image_url" class="story-image-wrapper" :class="{ 'image-loaded': isImageLoaded }">
        <StoryImage
          :image-url="entry.image_url"
          :alt="`Story illustration for segment ${entry.id}`"
          @loaded="onImageLoaded"
          @error="onImageError"
        />
      </div>

      <!-- Text content AFTER image in HTML - slides down when image appears -->
      <div class="story-text-container" :class="{ 'text-push-down': isImageLoaded && entry.image_url }">
        <div class="prose dark:prose-invert max-w-none">
          <div v-html="renderedContent" />

          <!-- Show chosen option if exists -->
          <div v-if="entry.chosen_option_text" class="text-sm text-muted-foreground mt-4 italic">
            Vous avez choisi : {{ entry.chosen_option_text }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import type { StoryProgress } from '@/types/game'
import StoryImage from './StoryImage.vue'

const props = defineProps<{
  entry: StoryProgress
  isLatest: boolean
  isContentReady: boolean
}>()

const emit = defineEmits<{
  (e: 'allParagraphsShown'): void
}>()

const isImageLoaded = ref(false)

const renderedContent = computed(() => marked.parse(props.entry.content) as string)

// Watch for image URL - reset loaded state when new image comes
watch(() => props.entry.image_url, (newUrl) => {
  if (newUrl) {
    isImageLoaded.value = false
  }
}, { immediate: true })

// Emit allParagraphsShown immediately when content is ready
watch(() => props.isContentReady, (ready) => {
  if (ready && props.isLatest && !props.entry.chosen_option_text) {
    emit('allParagraphsShown')
  }
}, { immediate: true })

const onImageLoaded = () => {
  isImageLoaded.value = true
}

const onImageError = () => {
  // Even on error, mark as loaded
  isImageLoaded.value = true
}
</script>

<style scoped>
.story-segment {
  padding: 1rem 0;
}

.story-text-container {
  width: 100%;
  transition: transform 0.8s ease-out;
  transform: translateY(0);
}

/* When image is loaded, text has already moved down (no additional transform needed) */
.story-text-container.text-push-down {
  /* No transform needed - text is already in final position */
}

.story-image-wrapper {
  width: 100%;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 0.8s ease-out, opacity 0.8s ease-out;
}

.story-image-wrapper.image-loaded {
  max-height: 800px;
  opacity: 1;
}
</style>
