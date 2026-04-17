<template>
  <Transition name="options-fade">
    <div v-if="options.length > 0 && !disabled" class="story-options">
      <button
        v-for="option in options"
        :key="option.option_id"
        class="story-option-button"
        @click="onSelect(option.option_id)"
        :disabled="disabled"
      >
        {{ option.option_name }}
      </button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import type { StoryOption } from '@/types/game'

const props = defineProps<{
  options: StoryOption[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', optionId: string): void
}>()

const onSelect = (optionId: string) => {
  if (!props.disabled) {
    emit('select', optionId)
  }
}
</script>

<style scoped>
.story-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
  padding: 1rem;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.02));
  border-radius: 0.5rem;
}

.story-option-button {
  padding: 1rem 1.5rem;
  border: 2px solid hsl(var(--border));
  border-radius: 0.5rem;
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.story-option-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 100%;
  background: hsl(var(--primary) / 0.1);
  transition: width 0.3s ease;
}

.story-option-button:hover:not(:disabled) {
  border-color: hsl(var(--primary));
  transform: translateX(4px);
}

.story-option-button:hover:not(:disabled)::before {
  width: 100%;
}

.story-option-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Fade in animation for options */
.options-fade-enter-active {
  transition: all 0.5s ease-out;
}

.options-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.options-fade-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.options-fade-leave-active {
  transition: all 0.3s ease-in;
}

.options-fade-leave-from {
  opacity: 1;
}

.options-fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments */
@media (min-width: 768px) {
  .story-options {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .story-option-button {
    flex: 1;
    min-width: 200px;
  }
}
</style>
