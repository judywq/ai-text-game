<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ExplanationService } from '@/services/explanationService'
import { GameService } from '@/services/gameService'
import type { TextExplanation, VocabularyQuizSubmitResponse } from '@/types/game'
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
const resultsSectionRef = ref<HTMLElement | null>(null)

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

function scoreClass(score: number) {
  if (score >= 1) return 'is-correct'
  if (score >= 0.5) return 'is-partial'
  return 'is-incorrect'
}

function goBackToStory() {
  router.push({ name: 'game-play', params: { id: storyId.value } })
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
    const latest = await ExplanationService.getLatestVocabularyQuiz(id)
    if (latest) {
      for (const row of latest.results) {
        if (row.user_explanation != null) {
          explanationsById[row.explanation_id] = row.user_explanation
        }
      }
      quizResult.value = {
        average_score: latest.average_score,
        results: latest.results.map(({ explanation_id, selected_text, score, reason }) => ({
          explanation_id,
          selected_text,
          score,
          reason,
        })),
      }
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
    await nextTick()
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultsSectionRef.value?.scrollIntoView({
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
      block: 'start',
    })
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
  <div class="library-shell" style="padding-top: 0">
    <section class="library-panel quiz-panel">
      <button type="button" class="quiz-back-link" @click="goBackToStory">
        ← Back to story
      </button>
      <div class="library-title-row">
        <div>
          <h1>Vocabulary review</h1>
          <p v-if="storyTitle">{{ storyTitle }}</p>
          <p v-else>Explain each saved phrase in your own words.</p>
        </div>
      </div>

      <div v-if="isLoading" class="quiz-loading">
        <div class="quiz-spinner" aria-hidden="true" />
        <p>Loading lookups…</p>
      </div>

      <template v-else>
        <p v-if="quizItems.length === 0" class="quiz-empty">
          There are no completed word lookups for this story yet. Use lookups during the game, wait
          until each explanation finishes, then open this page again.
        </p>

        <div v-else class="quiz-body">
          <p class="quiz-intro">
            For each expression you looked up, explain in your own words what it means in the story.
          </p>

          <article v-for="item in quizItems" :key="item.id" class="quiz-term">
            <strong>{{ item.selected_text }}</strong>
            <small>
              <span class="quiz-context-label">Context:</span>
              {{ item.context_text }}
            </small>
            <div class="la-field">
              <label :for="`explain-${item.id}`">Your explanation</label>
              <textarea
                :id="`explain-${item.id}`"
                v-model="explanationsById[item.id]"
                placeholder="Explain the meaning in your own words…"
                rows="4"
                :disabled="!!quizResult || isSubmitting"
              />
            </div>
          </article>

          <div class="quiz-actions">
            <button
              type="button"
              class="la-btn"
              :disabled="!canSubmit || isSubmitting || !!quizResult"
              @click="submitQuiz"
            >
              <span v-if="isSubmitting" class="quiz-submit-busy">
                <span class="quiz-spinner quiz-spinner--sm" aria-hidden="true" />
                Checking…
              </span>
              <span v-else>Submit review <span aria-hidden="true">→</span></span>
            </button>
          </div>

          <div v-if="quizResult" ref="resultsSectionRef" class="quiz-results">
            <h2>Results</h2>
            <p class="quiz-score-line">
              Average score:
              <strong>{{ quizResult.average_score.toFixed(2) }}</strong>
            </p>
            <p class="quiz-scale">0 = incorrect · 0.5 = partial · 1 = correct</p>
            <div
              v-for="row in quizResult.results"
              :key="row.explanation_id"
              class="quiz-result-row"
            >
              <div class="quiz-result-head">
                <strong>{{ row.selected_text }}</strong>
                <span class="quiz-score-badge" :class="scoreClass(row.score)">
                  {{ scoreLabel(row.score) }} ({{ row.score }})
                </span>
              </div>
              <p><span class="quiz-feedback-label">Feedback:</span> {{ row.reason }}</p>
            </div>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>
