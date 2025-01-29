<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import type { GameScenario } from '@/types/game'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem, SelectGroup } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast/use-toast'
import { LLMModelService } from '@/services/llmModelService'
import type { LLMModel } from '@/types/llm'

const router = useRouter()
const { toast } = useToast()
const scenarios = ref<GameScenario[]>([])
const selectedModel = ref('')
const isLoading = ref(false)
const modelOptions = ref<LLMModel[]>([])

const updateModelQuotas = async () => {
  try {
    const models = await LLMModelService.getActiveModels()
    modelOptions.value = models
    // If current selected model is no longer available, select default or first
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
    await Promise.all([
      GameService.getScenarios().then(data => scenarios.value = data),
      updateModelQuotas()
    ])
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to load data',
      variant: 'destructive',
    })
  }
})

async function startGame(scenario: GameScenario) {
  if (!selectedModel.value) {
    toast({
      title: 'Error',
      description: 'Please select a model first',
      variant: 'destructive',
    })
    return
  }

  isLoading.value = true
  try {
    const story = await GameService.createStory(scenario.id, selectedModel.value)
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
    <h1 class="text-3xl font-bold mb-6">Choose Your Adventure</h1>

    <div class="mb-6">
      <Select v-model="selectedModel">
        <SelectTrigger class="w-[280px]">
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

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="scenario in scenarios"
        :key="scenario.id"
        class="hover:shadow-lg transition-shadow"
      >
        <CardHeader>
          <CardTitle>{{ scenario.title }}</CardTitle>
          <CardDescription>{{ scenario.description }}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            class="w-full"
            :disabled="isLoading || !selectedModel"
            @click="startGame(scenario)"
          >
            Start Adventure
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
