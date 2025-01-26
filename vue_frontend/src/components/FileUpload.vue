<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Loader2, Upload } from 'lucide-vue-next'

const props = defineProps<{
  accept?: string
  loading?: boolean
  disabled?: boolean
}>()

const emit = defineEmits(['file-selected'])
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const handleClick = () => {
  fileInput.value?.click()
}

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    emit('file-selected', target.files[0])
  }
}

const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = false
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    emit('file-selected', files[0])
  }
}
</script>

<template>
  <div
    class="relative flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors z-10"
    :class="{
      'border-primary bg-primary/5': isDragging,
      'border-input hover:border-primary/50': !isDragging,
      'opacity-50 cursor-not-allowed': disabled || loading,
    }"
    @click="handleClick"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      class="hidden"
      @change="handleFileChange"
      :disabled="disabled || loading"
    />

    <div class="flex flex-col items-center justify-center pt-5 pb-6">
      <Upload class="w-8 h-8 mb-2 text-muted-foreground" />
      <p class="mb-2 text-sm text-muted-foreground">
        <span class="font-semibold">Click to upload</span> or drag and drop
      </p>
      <p class="text-xs text-muted-foreground">Word documents only</p>
    </div>

    <div
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center bg-background/80 rounded-lg"
    >
      <Loader2 class="w-6 h-6 animate-spin" />
    </div>
  </div>
</template>
