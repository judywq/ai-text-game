<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function startStory() {
  router.push({ name: 'game-scenarios' })
}
</script>

<template>
  <main class="home-shell">
    <Transition name="la-fade" appear>
      <section class="home-hero">
        <h1>An AI-driven Interactive narrative game.</h1>
        <p class="home-lede">Your choice writes the next page.</p>
        <button type="button" class="la-btn" @click="startStory">Begin a story</button>
      </section>
    </Transition>
  </main>
</template>
