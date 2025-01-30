<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Check, ChevronsUpDown } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

const props = defineProps<{
  modelValue: string
  options: string[]
  placeholder?: string
  allowCustom?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const open = ref(false)
const search = ref('')
const customValue = ref('')

const filteredOptions = computed(() => {
  if (!search.value) return props.options
  return props.options.filter((option) =>
    option.toLowerCase().includes(search.value.toLowerCase())
  )
})

watch(() => props.modelValue, (newValue) => {
  if (newValue && !props.options.includes(newValue)) {
    customValue.value = newValue
  }
})

const selectOption = (value: string) => {
  emit('update:modelValue', value)
  open.value = false
}

const handleCustomInput = (value: string) => {
  if (props.allowCustom) {
    customValue.value = value
    emit('update:modelValue', value)
  }
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        role="combobox"
        :aria-expanded="open"
        class="w-full justify-between"
      >
        {{ modelValue || placeholder || "Select option..." }}
        <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-full p-0">
      <Command>
        <CommandInput
          v-model="search"
          placeholder="Search options..."
          @input="handleCustomInput($event.target.value)"
        />
        <CommandEmpty v-if="!allowCustom">No options found.</CommandEmpty>
        <CommandEmpty v-else>
          Press enter to use "{{ search }}"
        </CommandEmpty>
        <CommandGroup>
          <CommandItem
            v-for="option in filteredOptions"
            :key="option"
            @select="selectOption(option)"
          >
            <Check
              :class="[
                'mr-2 h-4 w-4',
                modelValue === option ? 'opacity-100' : 'opacity-0'
              ]"
            />
            {{ option }}
          </CommandItem>
        </CommandGroup>
      </Command>
    </PopoverContent>
  </Popover>
</template>
