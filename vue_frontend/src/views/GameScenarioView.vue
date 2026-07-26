<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GameService } from '@/services/gameService'
import type { GameScenario, GameStory } from '@/types/game'
import { Combobox } from '@/components/ui/combobox'
import { useToast } from '@/components/ui/toast/use-toast'
import BookFrame from '@/components/line-art/BookFrame.vue'

const RECENT_GAMES_LIMIT = 5
const router = useRouter()
const route = useRoute()
const { toast } = useToast()
const selectedGenre = ref('')
const selectedTheme = ref('')
const isLoading = ref(false)
const scenarios = ref<GameScenario[]>([])
const scenes = ref<Array<{ level: string; text: string }>>([])
const isGeneratingScenes = ref(false)
const details = ref('')
const recentGames = ref<GameStory[]>([])
const selectedLevelIndex = ref(0)
const shelfCollapsed = ref(false)
const SHELF_MOBILE_MQ = '(max-width: 760px)'
let shelfMobileMql: MediaQueryList | null = null

function syncShelfCollapsedForViewport() {
  if (typeof window === 'undefined') return
  if (window.matchMedia(SHELF_MOBILE_MQ).matches) {
    shelfCollapsed.value = true
  }
}

function onShelfViewportChange(event: MediaQueryListEvent) {
  if (event.matches) {
    shelfCollapsed.value = true
  }
}

const genreScenarios = computed(() =>
  scenarios.value
    .filter((s) => s.category === 'genre')
    .slice()
    .sort((a, b) => a.order - b.order || a.name.localeCompare(b.name)),
)

const selectedGenreId = computed(() => {
  const match = genreScenarios.value.find((s) => s.name === selectedGenre.value)
  return match?.id ?? null
})

const themeScenarios = computed(() => {
  if (selectedGenreId.value == null) return []
  return scenarios.value
    .filter((s) => s.category === 'theme' && s.parent === selectedGenreId.value)
    .slice()
    .sort((a, b) => a.order - b.order || a.name.localeCompare(b.name))
})

const genreOptions = computed(() => [
  {
    label: 'Genres',
    options: genreScenarios.value.map((s) => ({
      value: s.name,
      label: s.name,
    })),
  },
])

const themeOptions = computed(() => [
  {
    label: 'Themes',
    options: themeScenarios.value.map((s) => ({
      value: s.name,
      label: s.name,
      description: s.description,
    })),
  },
])

const loadScenarios = async () => {
  try {
    scenarios.value = await GameService.getScenarios()
  } catch (error) {
    console.error('Error loading scenarios:', error)
    toast({ title: 'Error', description: 'Failed to load scenarios', variant: 'destructive' })
  }
}

const loadRecentGames = async () => {
  try {
    const response = await GameService.getRecentStories(1, RECENT_GAMES_LIMIT)
    recentGames.value = response.results
  } catch (error) {
    console.error('Error loading recent games:', error)
  }
}

onMounted(async () => {
  syncShelfCollapsedForViewport()
  shelfMobileMql = window.matchMedia(SHELF_MOBILE_MQ)
  shelfMobileMql.addEventListener('change', onShelfViewportChange)

  const prompt = typeof route.query.prompt === 'string' ? route.query.prompt : ''
  if (prompt) details.value = prompt

  try {
    await Promise.all([loadScenarios(), loadRecentGames()])
  } catch {
    toast({ title: 'Error', description: 'Failed to load data', variant: 'destructive' })
  }
})

onUnmounted(() => {
  shelfMobileMql?.removeEventListener('change', onShelfViewportChange)
  shelfMobileMql = null
})

watch(selectedGenre, () => {
  selectedTheme.value = ''
})

async function generateScenes() {
  if (isGeneratingScenes.value) return

  if (!selectedGenre.value) {
    toast({
      title: 'Error',
      description: 'Please select a genre first',
      variant: 'destructive',
    })
    return
  }
  if (!selectedTheme.value) {
    toast({
      title: 'Error',
      description: 'Please select a theme first',
      variant: 'destructive',
    })
    return
  }

  isGeneratingScenes.value = true
  scenes.value = []
  selectedLevelIndex.value = 0

  try {
    const eventSource = await GameService.generateScenesStream(
      selectedGenre.value,
      details.value,
      selectedTheme.value,
    )

    eventSource.addEventListener('scene', ((event: MessageEvent) => {
      const sceneData = JSON.parse(event.data)
      const nextScenes = sceneData.scenes || []
      const isNewCard = nextScenes.length > scenes.value.length
      scenes.value = nextScenes
      if (isNewCard) scrollToGeneratedScenes()
    }) as EventListener)

    eventSource.addEventListener('complete', ((event: MessageEvent) => {
      const completeData = JSON.parse(event.data)
      const nextScenes = completeData.scenes || []
      const isNewCard = nextScenes.length > scenes.value.length
      scenes.value = nextScenes
      isGeneratingScenes.value = false
      eventSource.close()
      if (isNewCard) scrollToGeneratedScenes()
    }) as EventListener)

    eventSource.addEventListener('error', (() => {
      toast({ title: 'Error', description: 'Failed to generate scenes', variant: 'destructive' })
      isGeneratingScenes.value = false
      eventSource.close()
    }) as EventListener)

    eventSource.addEventListener('close', () => {
      isGeneratingScenes.value = false
    })

    eventSource.connect()
  } catch {
    toast({ title: 'Error', description: 'Failed to generate scenes', variant: 'destructive' })
    isGeneratingScenes.value = false
  }
}

function scrollToGeneratedScenes() {
  nextTick(() => {
    document.querySelector('.level-section')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  })
}

async function startGame(sceneText?: string, languageLevel?: string, details?: string) {
  if (!selectedGenre.value) {
    toast({ title: 'Error', description: 'Please select a genre', variant: 'destructive' })
    return
  }
  if (!selectedTheme.value) {
    toast({ title: 'Error', description: 'Please select a theme', variant: 'destructive' })
    return
  }

  isLoading.value = true
  try {
    const story = await GameService.createStory(
      selectedGenre.value,
      sceneText,
      languageLevel,
      details,
      selectedTheme.value,
    )
    router.push(`/game/${story.id}/loading`)
  } catch {
    toast({ title: 'Error', description: 'Failed to start game', variant: 'destructive' })
  } finally {
    isLoading.value = false
  }
}

function startSelectedLevel() {
  const scene = scenes.value[selectedLevelIndex.value]
  if (!scene) return
  startGame(scene.text, scene.level, details.value)
}

const handleGameClick = (story: GameStory) => {
  if (story.status === 'INIT') {
    router.push(`/game/${story.id}/loading`)
  } else {
    router.push(`/game/${story.id}`)
  }
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function statusLabel(status: GameStory['status']) {
  if (status === 'IN_PROGRESS' || status === 'INIT') return 'In progress'
  if (status === 'COMPLETED') return 'Completed'
  if (status === 'ABANDONED') return 'Abandoned'
  return status
}

function statusClass(status: GameStory['status']) {
  if (status === 'IN_PROGRESS' || status === 'INIT') return 'is-active'
  if (status === 'COMPLETED') return 'is-done'
  return 'is-muted'
}

function toggleShelf() {
  shelfCollapsed.value = !shelfCollapsed.value
}

function closeShelf() {
  shelfCollapsed.value = true
}
</script>

<template>
  <div class="story-settings" :class="{ 'shelf-collapsed': shelfCollapsed }">
    <button
      type="button"
      class="shelf-backdrop"
      aria-label="Close shelf"
      tabindex="-1"
      @click="closeShelf"
    />
    <BookFrame variant="setting-book">
      <template #left>
        <section class="setting-page setup-page">
          <p class="setting-kicker">STORY SETUP</p>
          <h1>Start a chapter</h1>
          <p class="setting-intro">Choose a genre and theme, add a detail if you like, then generate reading levels.</p>

          <div class="setting-form">
            <div class="setting-field">
              <label>Genre</label>
              <Combobox v-model="selectedGenre" :options="genreOptions" placeholder="Select a genre" />
            </div>

            <div class="setting-field">
              <label>Theme</label>
              <Combobox
                v-model="selectedTheme"
                :options="themeOptions"
                placeholder="Select a theme"
                :disabled="!selectedGenre"
              />
            </div>

            <div class="setting-field">
              <label>Details <span>(optional)</span></label>
              <textarea
                v-model="details"
                placeholder="A place, a feeling, a first line..."
                maxlength="500"
              />
            </div>

            <button
              type="button"
              class="generate-button"
              :disabled="isGeneratingScenes || !selectedGenre || !selectedTheme"
              @click="generateScenes"
            >
              {{ isGeneratingScenes ? 'Generating…' : 'Generate scenes' }}
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </section>
      </template>

      <template #right>
        <section class="setting-page shelf-page" id="settings-shelf-panel">
          <button
            type="button"
            class="shelf-tab"
            :aria-expanded="!shelfCollapsed"
            aria-controls="settings-shelf-panel"
            @click="toggleShelf"
          >
            Shelf
          </button>
          <div class="shelf-content">
            <div class="shelf-heading">
              <p class="setting-kicker">RECENT</p>
              <h2>On your shelf</h2>
            </div>
            <TransitionGroup name="la-fade" tag="ul" class="story-list">
              <li v-for="(story, idx) in recentGames" :key="story.id">
                <a href="#" @click.prevent="handleGameClick(story)">
                  <span class="story-index">{{ pad(idx + 1) }}</span>
                  <span class="story-details">
                    <strong>{{ story.title || 'Untitled' }}</strong>
                    <span class="story-meta">
                      <small :class="statusClass(story.status)">{{ statusLabel(story.status) }}</small>
                      <small class="story-date" aria-hidden="true">·</small>
                      <small class="story-date">{{ new Date(story.updated_at).toLocaleDateString() }}</small>
                    </span>
                  </span>
                  <span class="story-arrow" aria-hidden="true">→</span>
                </a>
              </li>
              <li
                v-if="recentGames.length === 0"
                key="empty"
                style="padding: 18px 0; color: var(--ink-soft)"
              >
                No recent stories yet.
              </li>
            </TransitionGroup>
            <router-link class="library-link" :to="{ name: 'history' }">
              Open full library <span aria-hidden="true">→</span>
            </router-link>
          </div>
        </section>
      </template>
    </BookFrame>

    <Transition name="la-fade">
      <section v-if="scenes.length" class="level-section">
        <div class="level-heading">
          <p class="setting-kicker">READING LEVEL</p>
          <h2>Pick a difficulty</h2>
          <p>Choose the scene that matches how you want to read today.</p>
        </div>

        <div class="level-form">
          <fieldset>
            <legend>Reading level</legend>
            <TransitionGroup name="la-fade" tag="div" class="level-options">
              <label
                v-for="(scene, index) in scenes"
                :key="index"
                class="level-choice"
              >
                <input
                  v-model="selectedLevelIndex"
                  type="radio"
                  name="level"
                  :value="index"
                />
                <span class="level-option">
                  <span class="level-code">{{ scene.level || `L${index + 1}` }}</span>
                  <span class="level-copy">
                    <strong>Level {{ index + 1 }}</strong>
                    <small>{{ scene.text }}</small>
                  </span>
                </span>
              </label>
            </TransitionGroup>
          </fieldset>

          <button
            type="button"
            class="start-button"
            :disabled="isLoading"
            @click="startSelectedLevel"
          >
            {{ isLoading ? 'Starting…' : 'Start story' }}
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </section>
    </Transition>
  </div>
</template>
