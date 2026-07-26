<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { GameService } from '@/services/gameService'
import { ExplanationService } from '@/services/explanationService'
import { useRouter } from 'vue-router'
import type { GameStory } from '@/types/game'
import { useToast } from '@/components/ui/toast/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const LEDE_MAX = 160

const router = useRouter()
const { toast } = useToast()
const data = ref<GameStory[]>([])
const selectedId = ref<number | null>(null)
const filter = ref<'all' | 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'>('all')
const emptyReviewOpen = ref(false)
const pendingReviewStoryId = ref<number | null>(null)
const isCheckingReview = ref(false)

const filtered = computed(() => {
  if (filter.value === 'all') return data.value
  if (filter.value === 'IN_PROGRESS') {
    return data.value.filter((s) => s.status === 'IN_PROGRESS' || s.status === 'INIT')
  }
  return data.value.filter((s) => s.status === filter.value)
})

async function loadData() {
  try {
    const response = await GameService.getRecentStories(1, 100)
    data.value = response.results
    if (selectedId.value != null) {
      const stillThere = response.results.some((s) => s.id === selectedId.value)
      if (!stillThere) selectedId.value = null
    }
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

function statusClass(status: GameStory['status']) {
  if (status === 'IN_PROGRESS' || status === 'INIT') return 'is-active'
  if (status === 'COMPLETED') return 'is-done'
  return 'is-muted'
}

function statusLabel(status: GameStory['status']) {
  if (status === 'IN_PROGRESS' || status === 'INIT') return 'In progress'
  if (status === 'COMPLETED') return 'Completed'
  if (status === 'ABANDONED') return 'Abandoned'
  return status
}

function storyGenre(story: GameStory) {
  return story.genre || story.scenario?.name || 'Story'
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function truncate(text: string, max: number) {
  const trimmed = text.trim().replace(/\s+/g, ' ')
  if (trimmed.length <= max) return trimmed
  return trimmed.slice(0, max - 1).trimEnd() + '…'
}

function openingLede(story: GameStory) {
  const progress = story.progress
  if (progress?.length) {
    const earliest = [...progress].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )[0]
    if (earliest?.content?.trim()) return truncate(earliest.content, LEDE_MAX)
  }
  const genre = storyGenre(story)
  const label = genre === 'Story' ? 'A generative adventure' : genre
  return `${label} — ${statusLabel(story.status).toLowerCase()}.`
}

function toggleStory(story: GameStory) {
  selectedId.value = selectedId.value === story.id ? null : story.id
}

function continueStory(story: GameStory) {
  router.push(`/game/${story.id}`)
}

async function openVocabularyReview(story: GameStory) {
  if (isCheckingReview.value) return
  isCheckingReview.value = true
  try {
    const history = await ExplanationService.getLookupHistory(story.id)
    const hasCompletedLookups = history.some(
      (e) => e.status === 'completed' && (e.explanation || '').trim().length > 0,
    )
    if (!hasCompletedLookups) {
      pendingReviewStoryId.value = story.id
      emptyReviewOpen.value = true
      return
    }
    router.push({ name: 'game-quiz', params: { id: story.id } })
  } catch (e: unknown) {
    const err = e as { message?: string }
    toast({
      title: 'Error',
      description: err.message || (e instanceof Error ? e.message : 'Failed to check vocabulary lookups'),
      variant: 'destructive',
    })
  } finally {
    isCheckingReview.value = false
  }
}

function closeEmptyReviewDialog() {
  emptyReviewOpen.value = false
  pendingReviewStoryId.value = null
}

function openStoryFromEmptyReview() {
  const id = pendingReviewStoryId.value
  closeEmptyReviewDialog()
  if (id != null) {
    router.push({ name: 'game-play', params: { id } })
  }
}

onMounted(loadData)
</script>

<template>
  <div class="library-shell" style="padding-top: 0">
    <section class="library-panel">
      <p class="library-kicker">YOUR SHELF</p>
      <div class="library-title-row">
        <div>
          <h1>My library</h1>
          <p>Open a story to continue where you paused.</p>
        </div>
        <label class="filter-label">
          Filter
          <select v-model="filter">
            <option value="all">All</option>
            <option value="IN_PROGRESS">In progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="ABANDONED">Abandoned</option>
          </select>
        </label>
      </div>

      <TransitionGroup name="la-fade" tag="ul" class="story-ledger">
        <li
          v-for="(story, idx) in filtered"
          :key="story.id"
          :class="{ 'is-expanded': selectedId === story.id }"
        >
          <div class="ledger-item-bar">
            <button
              type="button"
              class="ledger-row"
              :aria-expanded="selectedId === story.id"
              @click="toggleStory(story)"
            >
              <span class="ledger-number">{{ pad(idx + 1) }}</span>
              <span class="ledger-main">
                <strong>{{ story.title || 'Untitled story' }}</strong>
                <small
                  >{{ storyGenre(story) }} ·
                  {{ new Date(story.updated_at).toLocaleDateString() }}</small
                >
              </span>
              <span class="ledger-status" :class="statusClass(story.status)">
                {{ statusLabel(story.status) }}
              </span>
              <span class="ledger-chevron" aria-hidden="true" />
            </button>
            <div class="ledger-actions">
              <button
                v-if="story.status === 'COMPLETED'"
                type="button"
                class="la-btn la-btn--secondary ledger-continue"
                :disabled="isCheckingReview"
                @click="openVocabularyReview(story)"
              >
                Review vocabulary <span aria-hidden="true">→</span>
              </button>
              <button
                type="button"
                class="la-btn ledger-continue"
                @click="continueStory(story)"
              >
                Continue reading <span aria-hidden="true">→</span>
              </button>
            </div>
          </div>

          <div v-if="selectedId === story.id" class="ledger-detail">
            <p class="detail-lede">{{ openingLede(story) }}</p>
            <dl class="library-stats">
              <div>
                <dt>Status</dt>
                <dd>{{ statusLabel(story.status) }}</dd>
              </div>
              <div>
                <dt>Updated</dt>
                <dd>{{ new Date(story.updated_at).toLocaleDateString() }}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{{ new Date(story.created_at).toLocaleDateString() }}</dd>
              </div>
            </dl>
          </div>
        </li>
        <li v-if="filtered.length === 0" key="empty" class="ledger-empty">
          <p>No stories yet. Start a new chapter.</p>
          <router-link class="continue-story" :to="{ name: 'game-scenarios' }">
            New story <span aria-hidden="true">→</span>
          </router-link>
        </li>
      </TransitionGroup>
    </section>

    <Dialog
      :open="emptyReviewOpen"
      @update:open="(open) => (open ? (emptyReviewOpen = true) : closeEmptyReviewDialog())"
    >
      <DialogContent class="bg-[var(--paper)] text-[var(--ink)] border-[var(--line)]">
        <DialogHeader>
          <DialogTitle>No vocabulary to review</DialogTitle>
          <DialogDescription>
            You haven’t looked up any words in this story yet. Open the story to look some up?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" class="la-btn la-btn--secondary" @click="closeEmptyReviewDialog">
            Cancel
          </button>
          <button type="button" class="la-btn" @click="openStoryFromEmptyReview">
            Open story
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
