<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import { LLMModelService } from '@/services/llmModelService'
import type { LLMModel } from '@/types/llm'
import type { GameScenario } from '@/types/game'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
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
const scenarios = ref<GameScenario[]>([])
const scenes = ref<Array<{ level: string; text: string }>>([])
const isGeneratingScenes = ref(false)

// Computed properties for genres and sub-genres
const genres = computed(() =>
  scenarios.value
    .filter(s => s.category === 'genre')
    .map(s => ({
      value: s.name,
      label: s.name,
      example: s.example
    }))
)

const subGenres = computed(() =>
  scenarios.value
    .filter(s => s.category === 'sub-genre')
    .map(s => ({
      value: s.name,
      label: s.name,
      example: s.example
    }))
)

// Combine all options for the combobox
const genreOptions = computed(() => [
  {
    label: 'Main Genres',
    options: genres.value
  },
  {
    label: 'Sub-Genres',
    options: subGenres.value
  }
])

const getEmptyStars = computed(() => (index: number) => {
  const maxStars = 6
  return Math.max(0, Math.min(maxStars - index, maxStars))
})

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

const loadScenarios = async () => {
  try {
    scenarios.value = await GameService.getScenarios()
  } catch (error) {
    console.error('Error loading scenarios:', error)
    toast({
      title: 'Error',
      description: 'Failed to load scenarios',
      variant: 'destructive',
    })
  }
}

onMounted(async () => {
  try {
    await Promise.all([updateModelQuotas(), loadScenarios()])
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to load data',
      variant: 'destructive',
    })
  }
})

async function generateScenes() {
  if (!selectedGenre.value) {
    toast({
      title: 'Error',
      description: 'Please select a genre first',
      variant: 'destructive',
    })
    return
  }

  isGeneratingScenes.value = true
  try {
    const response = await GameService.generateScenes(selectedGenre.value)
    scenes.value = response.scenes
  } catch (error) {
    console.error('Error generating scenes:', error)
    toast({
      title: 'Error',
      description: 'Failed to generate scenes',
      variant: 'destructive',
    })
  } finally {
    isGeneratingScenes.value = false
  }
}

async function startGame(sceneText?: string, cefrLevel?: string) {
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
    const story = await GameService.createStory(
      selectedGenre.value,
      selectedModel.value,
      sceneText,
      cefrLevel
    )
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
    <Card class="max-w-md mx-auto mb-8">
      <CardHeader>
        <CardTitle class="text-3xl font-bold">Start Your Adventure</CardTitle>
        <CardDescription>Select a model and genre to start your adventure</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4 pt-6">
        <!-- Model Selection -->
        <div class="space-y-2">
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
        </div>

        <!-- Genre Selection -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Select Genre</label>
          <Combobox
            v-model="selectedGenre"
            :options="genreOptions"
            placeholder="Select a genre"
          />
        </div>

        <Button
          class="w-full"
          :disabled="isGeneratingScenes || !selectedGenre"
          @click="generateScenes"
        >
          {{ isGeneratingScenes ? 'Generating Scenes...' : 'Generate Scenes' }}
        </Button>
      </CardContent>
    </Card>

    <!-- Generated Scenes -->
    <div v-if="scenes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
      <Card
        v-for="(scene, index) in scenes"
        :key="index"
        class="cursor-pointer hover:shadow-lg transition-shadow"
        @click="startGame(scene.text, scene.level)"
      >
        <CardHeader>
          <CardTitle> Level {{ index + 1 }}</CardTitle>
          <CardDescription>
            <span class="flex">
              <span v-for="i in Math.min(index + 1, 5)" :key="i" class="text-yellow-400">★</span>
              <span v-for="i in getEmptyStars(index + 1)" :key="`empty-${i}`" class="text-gray-300">★</span>
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm">{{ scene.text }}</p>
        </CardContent>
        <CardFooter>
          <Button class="w-full" variant="outline">
            Start with this difficulty
          </Button>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
