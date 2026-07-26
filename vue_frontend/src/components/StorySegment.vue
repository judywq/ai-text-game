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
      <div
        v-if="showImage && entry.image_url"
        class="story-image-wrapper"
        :class="{ 'image-loaded': isImageLoaded }"
      >
        <StoryImage
          :image-url="entry.image_url"
          :alt="`Story illustration for segment ${entry.id}`"
          @loaded="onImageLoaded"
          @error="onImageError"
        />
      </div>

      <!-- Text content AFTER image in HTML - slides down when image appears -->
      <div
        class="story-text-container"
        :class="{ 'text-push-down': showImage && isImageLoaded && entry.image_url }"
      >
        <div class="prose max-w-none">
          <div v-html="renderedContent" />

          <!-- Show chosen option if exists -->
          <div v-if="entry.chosen_option_text" class="text-sm text-muted-foreground mt-4 italic">
            {{ chosenLabel }} {{ entry.chosen_option_text }}
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

const props = withDefaults(
  defineProps<{
    entry: StoryProgress
    isLatest: boolean
    isContentReady: boolean
    showImage?: boolean
  }>(),
  { showImage: true },
)

const emit = defineEmits<{
  (e: 'allParagraphsShown'): void
}>()

// Label follows the content language (mirrors backend PROMPT_LANGUAGE_CODE)
const chosenLabel = import.meta.env.VITE_PROMPT_LANGUAGE_CODE === 'French'
  ? 'Vous avez choisi :'
  : 'You chose:'

const isImageLoaded = ref(false)

// The LLM restates the decision options as a bullet list at the end of the segment.
// They already appear as clickable buttons, so drop that trailing list and keep the
// closing question. Requiring whitespace or end-of-line after the marker keeps
// *emphasis* and a *** rule from looking like list items.
const LIST_ITEM_PATTERN = /^ {0,3}(?:[-*+]|\d{1,9}[.)])(?:\s.*)?$/

const stripTrailingOptionList = (content: string) => {
  const lines = content.split('\n')
  let end = lines.length

  // Walk back over the trailing list items and the blank lines between them,
  // stopping at the first line that is neither.
  while (end > 0 && (lines[end - 1].trim() === '' || LIST_ITEM_PATTERN.test(lines[end - 1]))) {
    end--
  }

  return lines.slice(0, end).join('\n').trimEnd()
}

const renderedContent = computed(
  () => marked.parse(stripTrailingOptionList(props.entry.content)) as string
)

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
