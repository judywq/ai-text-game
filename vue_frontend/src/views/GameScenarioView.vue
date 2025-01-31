<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { LLMModelService } from '@/services/llmModelService'
import type { LLMModel } from '@/types/llm'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Combobox } from '@/components/ui/combobox'
import { useToast } from '@/components/ui/toast/use-toast'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const router = useRouter()
const { toast } = useToast()
const selectedModel = ref('')
const selectedGenre = ref('')
const isLoading = ref(false)
const modelOptions = ref<LLMModel[]>([])

// Predefined genres
const genres = [
  'Fantasy',
  'Science Fiction',
  'Mystery',
  'Horror',
  'Romance',
  'Adventure',
  'Historical Fiction',
  'Western',
  'Thriller',
  'Comedy'
]

const updateModelQuotas = async () => {
  try {
    const models = await LLMModelService.getActiveModels()
    modelOptions.value = models
    if (!models.find(model => model.name === selectedModel.value)) {
      const defaultModel = models.find(model => model.is_default)
      selectedModel.value = defaultModel?.name || models[0]?.name || ''
    }
  } catch (err) {
    console.error('Error updating models:', err)
    toast({
      title: 'Error',
      description: 'Failed to load models',
      variant: 'destructive',
    })
  }
}

onMounted(async () => {
  try {
    await updateModelQuotas()
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to load data',
      variant: 'destructive',
    })
  }
})

async function startGame() {
  if (!selectedModel.value || !selectedGenre.value) {
    toast({
      title: 'Error',
      description: 'Please select both a model and genre',
      variant: 'destructive',
    })
    return
  }

  isLoading.value = true
  try {
    const story = await GameService.createStory(selectedGenre.value, selectedModel.value)
    router.push(`/game/${story.id}`)
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to start game',
      variant: 'destructive',
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="container mx-auto py-8">


    <Card class="max-w-md mx-auto">
    <CardHeader>
      <CardTitle class="text-3xl font-bold">Start Your Adventure</CardTitle>
      <CardDescription>Select a model and genre to start your adventure</CardDescription>
    </CardHeader>
      <CardContent class="space-y-4 pt-6">
        <!-- Model Selection -->

          <label class="text-sm font-medium mb-2 block">Select Model</label>
          <Select v-model="selectedModel">
            <SelectTrigger class="w-full">
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem
                  v-for="model in modelOptions"
                  :key="model.name"
                  :value="model.name"
                >
                  {{ model.display_name }}
                  <span
                    v-if="model.daily_limit"
                    :class="{
                      'text-red-500': model.used_quota >= model.daily_limit,
                      'text-muted-foreground': model.used_quota < model.daily_limit
                    }"
                    class="ml-2"
                  >
                    ({{ model.used_quota }}/{{ model.daily_limit }})
                  </span>
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>

        <!-- Genre Selection -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Select or Enter Genre</label>
          <Combobox
            v-model="selectedGenre"
            :options="genres"
            placeholder="Select or type a genre"
            :allow-custom="true"
          />
        </div>

        <!-- Start Button -->
        <Button
          class="w-full"
          :disabled="isLoading || !selectedModel || !selectedGenre"
          @click="startGame"
        >
          Start Adventure
        </Button>
      </CardContent>
    </Card>
  </div>
</template>
