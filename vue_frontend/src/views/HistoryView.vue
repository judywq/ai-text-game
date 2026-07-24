<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { GameService } from '@/services/gameService'
import { useRouter } from 'vue-router'
import type { GameStory } from '@/types/game'
import BookFrame from '@/components/line-art/BookFrame.vue'

const router = useRouter()
const data = ref<GameStory[]>([])
const selected = ref<GameStory | null>(null)
const filter = ref<'all' | 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'>('all')

const filtered = computed(() => {
  if (filter.value === 'all') return data.value
  return data.value.filter((s) => s.status === filter.value)
})

async function loadData() {
  try {
    const response = await GameService.getRecentStories(1, 100)
    data.value = response.results
    if (!selected.value && response.results.length) {
      selected.value = response.results[0]
    } else if (selected.value) {
      selected.value =
        response.results.find((s) => s.id === selected.value!.id) ?? response.results[0] ?? null
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

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function continueStory(story: GameStory) {
  router.push(`/game/${story.id}`)
}

onMounted(loadData)
</script>

<template>
  <div class="library-shell" style="padding-top: 0">
    <BookFrame variant="library-book">
      <template #left>
        <section class="library-list-leaf">
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
            <li v-for="(story, idx) in filtered" :key="story.id">
              <a href="#" @click.prevent="selected = story">
                <span class="ledger-number">{{ pad(idx + 1) }}</span>
                <span class="ledger-main">
                  <strong>{{ story.title || 'Untitled story' }}</strong>
                  <small>{{ story.scenario?.name || 'Story' }} · {{ new Date(story.updated_at).toLocaleDateString() }}</small>
                </span>
                <span class="ledger-status" :class="statusClass(story.status)">
                  {{ statusLabel(story.status) }}
                </span>
                <span aria-hidden="true">→</span>
              </a>
            </li>
            <li v-if="filtered.length === 0" style="padding: 24px 0; color: var(--ink-soft)">
              No stories yet. Start a new chapter.
            </li>
          </ul>
        </section>
      </template>

      <template #right>
        <section class="library-detail-leaf">
          <template v-if="selected">
            <p class="library-kicker">SELECTED</p>
            <h2>{{ selected.title || 'Untitled story' }}</h2>
            <p class="detail-lede">
              {{ selected.scenario?.name || 'A generative adventure' }} —
              {{ statusLabel(selected.status).toLowerCase() }}.
            </p>
            <a class="continue-story" href="#" @click.prevent="continueStory(selected)">
              Continue reading <span aria-hidden="true">→</span>
            </a>
            <div class="detail-rule" aria-hidden="true"><span></span><i></i><span></span></div>
            <dl class="library-stats">
              <div>
                <dt>Status</dt>
                <dd>{{ statusLabel(selected.status) }}</dd>
              </div>
              <div>
                <dt>Updated</dt>
                <dd>{{ new Date(selected.updated_at).toLocaleDateString() }}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{{ new Date(selected.created_at).toLocaleDateString() }}</dd>
              </div>
            </dl>
          </template>
          <template v-else>
            <p class="library-kicker">SELECTED</p>
            <h2>Nothing selected</h2>
            <p class="detail-lede">Pick a story from your shelf, or start a new one.</p>
            <router-link class="continue-story" :to="{ name: 'game-scenarios' }">
              New story <span aria-hidden="true">→</span>
            </router-link>
          </template>
        </section>
      </template>
    </BookFrame>
  </div>
</template>
