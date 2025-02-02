<script setup lang="ts">
import { ref, watch } from 'vue'
import { Check, ChevronsUpDown } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { cn } from '@/lib/utils'

interface Option {
  value: string
  label: string
  example?: string
}

interface OptionGroup {
  label: string
  options: Option[]
}

const props = defineProps<{
  modelValue: string
  options: OptionGroup[]
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)
const searchTerm = ref('')

const getCurrentLabel = () => {
  for (const group of props.options) {
    const option = group.options.find(opt => opt.value === props.modelValue)
    if (option) return option.label
  }
  return ''
}

// Reset search when closing
watch(open, (newValue) => {
  if (!newValue) {
    searchTerm.value = ''
  }
})
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
        {{ getCurrentLabel() || placeholder }}
        <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-full p-0">
      <Command v-model:value="searchTerm">
        <CommandInput :placeholder="placeholder" />
        <CommandEmpty>No option found.</CommandEmpty>
        <CommandList>
          <CommandGroup v-for="group in options" :key="group.label">
            <h3 class="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
              {{ group.label }}
            </h3>
            <CommandItem
              v-for="option in group.options"
              :key="option.value"
              :value="option.value"
              @select="() => {
                emit('update:modelValue', option.value)
                open = false
              }"
            >
              <Check
                :class="cn(
                  'mr-2 h-4 w-4',
                  modelValue === option.value ? 'opacity-100' : 'opacity-0'
                )"
              />
              <div>
                <div>{{ option.label }}</div>
                <div v-if="option.example" class="text-sm text-muted-foreground">
                  {{ option.example }}
                </div>
              </div>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </PopoverContent>
  </Popover>
</template>
