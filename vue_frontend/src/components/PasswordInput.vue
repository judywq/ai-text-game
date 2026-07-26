<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const attrs = useAttrs()

const isDisabled = computed(() => {
  const disabled = attrs.disabled
  return disabled === true || disabled === '' || disabled === 'true'
})

function toggleVisible() {
  if (isDisabled.value) return
  emit('update:visible', !props.visible)
}
</script>

<template>
  <div class="password-field">
    <input v-bind="attrs" :type="visible ? 'text' : 'password'" />
    <button
      type="button"
      class="password-toggle"
      :aria-label="visible ? 'Hide password' : 'Show password'"
      :aria-pressed="visible"
      :disabled="isDisabled"
      :tabindex="isDisabled ? -1 : 0"
      @click="toggleVisible"
    >
      <EyeOff v-if="visible" :size="18" aria-hidden="true" />
      <Eye v-else :size="18" aria-hidden="true" />
    </button>
  </div>
</template>
