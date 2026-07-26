<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
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
const isLoading = ref(false)
const scenarios = ref<GameScenario[]>([])
const scenes = ref<Array<{ level: string; text: string }>>([])
const isGeneratingScenes = ref(false)
const customGenre = ref('')
const showCustomGenreInput = ref(false)
const details = ref('')
const theme = ref('')
const recentGames = ref<GameStory[]>([])
const selectedLevelIndex = ref(0)

const genres = computed(() =>
  scenarios.value
    .filter((s) => s.category === 'genre')
    .map((s) => ({ value: s.name, label: s.name, example: s.example })),
)

const subGenres = computed(() =>
  scenarios.value
    .filter((s) => s.category === 'sub-genre')
    .map((s) => ({ value: s.name, label: s.name, example: s.example })),
)

const genreOptions = computed(() => [
  { label: 'Main Genres', options: genres.value },
  { label: 'Sub-Genres', options: subGenres.value },
  {
    label: 'Other',
    options: [{ value: 'other', label: 'Other (Custom Genre)', example: 'Type your own genre' }],
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
  const prompt = typeof route.query.prompt === 'string' ? route.query.prompt : ''
  if (prompt) details.value = prompt

  try {
    await Promise.all([loadScenarios(), loadRecentGames()])
  } catch {
    toast({ title: 'Error', description: 'Failed to load data', variant: 'destructive' })
  }
})

watch(selectedGenre, (newValue) => {
  showCustomGenreInput.value = newValue === 'other'
  if (newValue !== 'other') customGenre.value = ''
})

async function generateScenes() {
  if (isGeneratingScenes.value) return

  const genreToUse = selectedGenre.value === 'other' ? customGenre.value : selectedGenre.value
  if (!genreToUse) {
    toast({
      title: 'Error',
      description:
        selectedGenre.value === 'other' ? 'Please enter a custom genre' : 'Please select a genre first',
      variant: 'destructive',
    })
    return
  }

  isGeneratingScenes.value = true
  scenes.value = []
  selectedLevelIndex.value = 0

  try {
    const eventSource = await GameService.generateScenesStream(genreToUse, details.value, theme.value || undefined)

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
  const genreToUse = selectedGenre.value === 'other' ? customGenre.value : selectedGenre.value
  if (!genreToUse) {
    toast({ title: 'Error', description: 'Please select a genre', variant: 'destructive' })
    return
  }

  isLoading.value = true
  try {
    const story = await GameService.createStory(
      genreToUse,
      sceneText,
      languageLevel,
      details,
      theme.value || undefined,
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
</script>

<template>
  <div class="story-settings">
    <BookFrame variant="setting-book">
      <template #left>
        <section class="setting-page setup-page">
          <p class="setting-kicker">STORY SETUP</p>
          <h1>Start a chapter</h1>
          <p class="setting-intro">Choose a genre, add a detail if you like, then generate reading levels.</p>

          <div class="setting-form">
            <div class="setting-field">
              <label>Genre</label>
              <Combobox v-model="selectedGenre" :options="genreOptions" placeholder="Select a genre" />
              <input
                v-if="showCustomGenreInput"
                v-model="customGenre"
                type="text"
                placeholder="Enter your genre"
                style="margin-top: 8px"
              />
            </div>

            <div class="setting-field">
              <label>Theme <span>(optional)</span></label>
              <input
                v-model="theme"
                type="text"
                placeholder="e.g., friendship, loyalty"
                maxlength="100"
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
              :disabled="
                isGeneratingScenes ||
                !selectedGenre ||
                (selectedGenre === 'other' && !customGenre)
              "
              @click="generateScenes"
            >
              {{ isGeneratingScenes ? 'Generating…' : 'Generate scenes' }}
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </section>
      </template>

      <template #right>
        <section class="setting-page shelf-page">
          <div class="shelf-heading">
            <p class="setting-kicker">RECENT</p>
            <h2>On your shelf</h2>
          </div>
          <ul class="story-list">
            <li v-for="(story, idx) in recentGames" :key="story.id">
              <a href="#" @click.prevent="handleGameClick(story)">
                <span class="story-index">{{ pad(idx + 1) }}</span>
                <span class="story-details">
                  <strong>{{ story.title || 'Untitled' }}</strong>
                  <small>{{ story.status }}</small>
                </span>
                <span class="story-arrow" aria-hidden="true">→</span>
              </a>
            </li>
            <li v-if="recentGames.length === 0" style="padding: 18px 0; color: var(--ink-soft)">
              No recent stories yet.
            </li>
          </ul>
          <router-link class="library-link" :to="{ name: 'history' }">
            Open full library <span aria-hidden="true">→</span>
          </router-link>
        </section>
      </template>
    </BookFrame>

    <section v-if="scenes.length" class="level-section">
      <div class="level-heading">
        <p class="setting-kicker">READING LEVEL</p>
        <h2>Pick a difficulty</h2>
        <p>Choose the scene that matches how you want to read today.</p>
      </div>

      <div class="level-form">
        <fieldset>
          <legend>Reading level</legend>
          <div class="level-options">
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
          </div>
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
  </div>
</template>
