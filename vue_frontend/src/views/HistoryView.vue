<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { GameService } from '@/services/gameService'
import { useRouter } from 'vue-router'
import type { GameStory } from '@/types/game'

const LEDE_MAX = 160

const router = useRouter()
const data = ref<GameStory[]>([])
const selectedId = ref<number | null>(null)
const filter = ref<'all' | 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'>('all')

const filtered = computed(() => {
  if (filter.value === 'all') return data.value
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
  if (status === 'IN_PROGRESS') return 'is-active'
  if (status === 'COMPLETED') return 'is-done'
  return 'is-muted'
}

function statusLabel(status: GameStory['status']) {
  if (status === 'IN_PROGRESS') return 'In progress'
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

      <ul class="story-ledger">
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
            <button
              type="button"
              class="la-btn ledger-continue"
              @click="continueStory(story)"
            >
              Continue reading <span aria-hidden="true">→</span>
            </button>
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
        <li v-if="filtered.length === 0" class="ledger-empty">
          <p>No stories yet. Start a new chapter.</p>
          <router-link class="continue-story" :to="{ name: 'game-scenarios' }">
            New story <span aria-hidden="true">→</span>
          </router-link>
        </li>
      </ul>
    </section>
  </div>
</template>
