<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ExplanationService } from '@/services/explanationService'
import { GameService } from '@/services/gameService'
import type { TextExplanation, VocabularyQuizSubmitResponse } from '@/types/game'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/toast/use-toast'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const storyTitle = ref('')
const items = ref<TextExplanation[]>([])
const explanationsById = reactive<Record<number, string>>({})
const isLoading = ref(true)
const isSubmitting = ref(false)
const quizResult = ref<VocabularyQuizSubmitResponse | null>(null)

const storyId = computed(() => Number(route.params.id))

const quizItems = computed(() =>
  items.value.filter(
    (e) => e.status === 'completed' && (e.explanation || '').trim().length > 0
  )
)

const canSubmit = computed(() => {
  if (quizItems.value.length === 0) return false
  return quizItems.value.every((e) => (explanationsById[e.id] || '').trim().length > 0)
})

function scoreLabel(score: number) {
  if (score >= 1) return 'Correct'
  if (score >= 0.5) return 'Partial'
  return 'Incorrect'
}

async function load() {
  isLoading.value = true
  quizResult.value = null
  try {
    const id = storyId.value
    if (!id) {
      router.push('/game')
      return
    }
    const story = await GameService.getStory(id)
    storyTitle.value = story.title
    const history = await ExplanationService.getLookupHistory(id)
    items.value = history
    for (const key of Object.keys(explanationsById)) {
      delete explanationsById[Number(key)]
    }
    for (const e of history) {
      explanationsById[e.id] = ''
    }
  } catch (e: unknown) {
    toast({
      title: 'Error',
      description: e instanceof Error ? e.message : 'Failed to load quiz',
      variant: 'destructive',
    })
    router.push('/game')
  } finally {
    isLoading.value = false
  }
}

async function submitQuiz() {
  if (!canSubmit.value || isSubmitting.value) return
  const id = storyId.value
  const answers = quizItems.value.map((e) => ({
    explanation_id: e.id,
    user_explanation: explanationsById[e.id].trim(),
  }))
  isSubmitting.value = true
  quizResult.value = null
  try {
    quizResult.value = await ExplanationService.submitVocabularyQuiz(id, answers)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    const msg = err.response?.data?.error || (e instanceof Error ? e.message : 'Submit failed')
    toast({
      title: 'Error',
      description: msg,
      variant: 'destructive',
    })
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <div class="container mx-auto max-w-3xl md:pt-6 pb-10 px-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold">Vocabulary review</h1>
        <p v-if="storyTitle" class="text-muted-foreground text-sm mt-1">{{ storyTitle }}</p>
      </div>
      <Button variant="outline" @click="router.push({ name: 'game-play', params: { id: storyId } })">
        Back to story
      </Button>
    </div>

    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 gap-3">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
      <p class="text-muted-foreground text-sm">Loading lookups…</p>
    </div>

    <template v-else>
      <p v-if="quizItems.length === 0" class="text-muted-foreground mb-6">
        There are no completed word lookups for this story yet. Use lookups during the game, wait until each
        explanation finishes, then open this page again.
      </p>

      <div v-else class="space-y-6">
        <p class="text-sm text-muted-foreground">
          For each expression you looked up, explain in your own words what it means in the story.
        </p>

        <Card v-for="item in quizItems" :key="item.id">
          <CardHeader class="pb-2">
            <CardTitle class="text-lg font-semibold text-primary">{{ item.selected_text }}</CardTitle>
          </CardHeader>
          <CardContent class="space-y-3">
            <div class="text-sm text-muted-foreground">
              <span class="font-medium text-foreground">Context: </span>{{ item.context_text }}
            </div>
            <div>
              <label class="text-sm font-medium block mb-2" :for="`explain-${item.id}`">Your explanation</label>
              <Textarea
                :id="`explain-${item.id}`"
                v-model="explanationsById[item.id]"
                placeholder="Explain the meaning in your own words…"
                class="min-h-[100px]"
                :disabled="!!quizResult || isSubmitting"
              />
            </div>
          </CardContent>
        </Card>

        <div class="flex flex-wrap gap-2 justify-end">
          <Button
            :disabled="!canSubmit || isSubmitting || !!quizResult"
            @click="submitQuiz"
          >
            <span v-if="isSubmitting" class="flex items-center gap-2">
              <span class="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
              Checking…
            </span>
            <span v-else>Submit</span>
          </Button>
        </div>

        <template v-if="quizResult">
          <Separator class="my-8" />
          <h2 class="text-xl font-bold mb-4">Results</h2>
          <p class="text-sm text-muted-foreground mb-4">
            Average score:
            <span class="font-semibold text-foreground">{{ quizResult.average_score.toFixed(2) }}</span>
            (0 = incorrect, 0.5 = partial, 1 = correct)
          </p>
          <div class="space-y-4">
            <Card v-for="row in quizResult.results" :key="row.explanation_id">
              <CardHeader class="pb-2">
                <div class="flex flex-wrap items-baseline justify-between gap-2">
                  <CardTitle class="text-base font-semibold">{{ row.selected_text }}</CardTitle>
                  <span
                    class="text-sm font-medium"
                    :class="{
                      'text-green-600': row.score >= 1,
                      'text-amber-600': row.score >= 0.5 && row.score < 1,
                      'text-destructive': row.score < 0.5,
                    }"
                  >
                    {{ scoreLabel(row.score) }} ({{ row.score }})
                  </span>
                </div>
              </CardHeader>
              <CardContent class="text-sm space-y-2">
                <p><span class="font-medium">Feedback: </span>{{ row.reason }}</p>
              </CardContent>
            </Card>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>
