<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BookFrame from '@/components/line-art/BookFrame.vue'
import { GameService } from '@/services/gameService'
import { onMounted } from 'vue'
import type { GameStory } from '@/types/game'

const authStore = useAuthStore()
const router = useRouter()
const prompt = ref('')
const continueStory = ref<GameStory | null>(null)

const greeting = computed(() => {
  const name = authStore.user?.username || 'learner'
  return name
})

const seeds = [
  'A bell beneath the fog',
  'The last train arrives',
  'A letter with no name',
]

function startWithPrompt(text?: string) {
  const idea = (text ?? prompt.value).trim()
  router.push({
    name: 'game-scenarios',
    query: idea ? { prompt: idea } : undefined,
  })
}

function useSeed(seed: string) {
  prompt.value = seed
  startWithPrompt(seed)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await GameService.getRecentStories(1, 1)
    continueStory.value = res.results?.[0] ?? null
  } catch {
    continueStory.value = null
  }
})
</script>

<template>
  <main class="home-shell">
    <BookFrame variant="home-book">
      <template #left>
        <section class="home-title-page">
          <p class="home-kicker">A READING ADVENTURE</p>
          <h1>
            Hello,<br />
            {{ greeting }}.
          </h1>
          <p class="home-intro">
            Every choice writes the next page. Pick a spark and make this chapter yours.
          </p>
          <div class="story-compass" aria-hidden="true"><i></i><b></b><span></span></div>
          <router-link class="quiet-link" :to="{ name: 'history' }">
            Open your library <span aria-hidden="true">→</span>
          </router-link>
          <p class="leaf-number">01</p>
        </section>
      </template>

      <template #right>
        <section class="home-prompt-page">
          <p class="home-kicker">START A CHAPTER</p>
          <h2>What would you like to explore?</h2>
          <form class="story-form" @submit.prevent="startWithPrompt()">
            <label for="prompt">Begin with an idea</label>
            <div class="prompt-input">
              <input
                id="prompt"
                v-model="prompt"
                placeholder="A place, a feeling, a first line..."
              />
              <button type="submit" aria-label="Start a story">→</button>
            </div>
          </form>

          <div class="prompt-seeds" aria-label="Chapter prompt ideas">
            <p>Try a prompt</p>
            <button v-for="seed in seeds" :key="seed" type="button" @click="useSeed(seed)">
              {{ seed }}
            </button>
          </div>

          <router-link
            v-if="continueStory"
            class="continue-card"
            :to="`/game/${continueStory.id}`"
          >
            <span class="continue-mark">··</span>
            <span>
              <small>CONTINUE READING</small>
              <strong>{{ continueStory.title || 'Untitled story' }}</strong>
              <em>Pick up where you left off.</em>
            </span>
            <i aria-hidden="true">→</i>
          </router-link>
        </section>
      </template>
    </BookFrame>
  </main>
</template>
