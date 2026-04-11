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
          <!-- Display paragraphs incrementally -->
          <template v-for="(paragraph, index) in paragraphs" :key="`${entry.id}-p-${index}`">
            <div v-if="index <= currentParagraphIndex" v-html="marked(paragraph)" />
          </template>

          <!-- Show chosen option if exists -->
          <div v-if="entry.chosen_option_text" class="text-sm text-muted-foreground mt-4 italic">
            Vous avez choisi : {{ entry.chosen_option_text }}
          </div>
        </div>
      </div>
    </template>

    <!-- Proceed button - shown until all paragraphs are displayed -->
    <div v-if="shouldShowProceedButton && entry.content !== 'LOADING'" class="proceed-button-container">
      <Button
        @click="proceedToNext"
        variant="outline"
        class="w-full transition-all"
        :disabled="isProceedDisabled"
      >
        <template v-if="isProceedDisabled">
          <span class="flex items-center justify-center gap-2">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
            Waiting for image...
          </span>
        </template>
        <template v-else>
          Proceed
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import type { StoryProgress } from '@/types/game'
import StoryImage from './StoryImage.vue'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  entry: StoryProgress
  isLatest: boolean
  isContentReady: boolean
}>()

const emit = defineEmits<{
  (e: 'allParagraphsShown'): void
}>()

const currentParagraphIndex = ref(0)
const isImageLoaded = ref(false)

// Split content into paragraphs
const paragraphs = computed(() => {
  return props.entry.content.split(/\n\n+/).filter(p => p.trim().length > 0)
})

// Check if we're on the last paragraph
const isOnLastParagraph = computed(() => {
  return currentParagraphIndex.value >= paragraphs.value.length - 1
})

// Track if we've shown all paragraphs (used to hide button after last proceed click)
const hasShownAllParagraphs = ref(false)

// Should show proceed button - show when first paragraph is fully displayed on UI
const shouldShowProceedButton = computed(() => {
  // Don't show if this entry has a chosen option (user already moved on)
  if (props.entry.chosen_option_text) return false

  // Don't show if this isn't the latest entry
  if (!props.isLatest) return false

  // Don't show if user has finished all paragraphs
  if (hasShownAllParagraphs.value) return false

  // Show button if we have at least one paragraph to display
  if (paragraphs.value.length > 0) {
    return true
  }

  return false
})

// Proceed button is disabled until image loads
const isProceedDisabled = computed(() => {
  // ALWAYS disabled until image has loaded
  // (Either we're waiting for image_url, or waiting for it to load)
  return !isImageLoaded.value
})

// Watch for image URL - reset loaded state when new image comes
watch(() => props.entry.image_url, (newUrl) => {
  if (newUrl) {
    isImageLoaded.value = false
  }
}, { immediate: true })

const proceedToNext = () => {
  if (!isOnLastParagraph.value) {
    // Move to next paragraph
    currentParagraphIndex.value++
  } else {
    // We're on the last paragraph, mark as all shown
    hasShownAllParagraphs.value = true
    // Notify parent that all paragraphs are shown (so it can show options)
    emit('allParagraphsShown')
  }
}

const onImageLoaded = () => {
  isImageLoaded.value = true
}

const onImageError = () => {
  // Even on error, allow proceeding
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

.proceed-button-container {
  margin-top: 1rem;
}
</style>
