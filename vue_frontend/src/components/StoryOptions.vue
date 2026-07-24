<template>
  <Transition name="options-fade">
    <div v-if="options.length > 0 && !disabled" class="story-options">
      <button
        v-for="option in options"
        :key="option.option_id"
        type="button"
        class="story-option-button"
        :disabled="disabled"
        @click="onSelect(option.option_id)"
      >
        {{ option.option_name }}
        <span aria-hidden="true">→</span>
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
  display: grid;
  gap: 10px;
  margin: 12px 0 0;
}

.story-option-button {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  min-height: 48px;
  padding: 10px 14px;
  border: 2px solid var(--line);
  border-radius: 7px;
  background: var(--paper);
  color: var(--ink);
  box-shadow: 3px 3px 0 var(--blue);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 0.95rem;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease;
}

.story-option-button:hover:not(:disabled) {
  background: var(--blue-deep);
  color: var(--paper);
  transform: translate(2px, 2px);
  box-shadow: 1px 1px 0 var(--ink);
}

.story-option-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
</style>
