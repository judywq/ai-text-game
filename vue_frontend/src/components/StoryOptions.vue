<template>
  <div v-if="options.length > 0" class="story-options">
    <button
      v-for="option in options"
      :key="option.option_id"
      class="story-option-button"
      @click="onSelect(option.option_id)"
    >
      {{ option.option_name }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { StoryOption } from '@/types/game'

const props = defineProps<{
  options: StoryOption[]
}>()

const emit = defineEmits<{
  (e: 'select', optionId: string): void
}>()

const onSelect = (optionId: string) => {
  emit('select', optionId)
}
</script>

<style scoped>
.story-options {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.story-option-button {
  padding: 0.5rem 1rem;
  border: 2px solid #4a5568;
  border-radius: 0.5rem;
  background-color: #2d3748;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.story-option-button:hover {
  background-color: #4a5568;
}
</style>
