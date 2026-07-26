<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function startStory() {
  router.push({ name: 'game-scenarios' })
}
</script>

<template>
  <main class="home-shell">
    <section class="home-hero">
      <h1>Every choice writes the next page. Pick a spark and make this chapter yours.</h1>
      <button type="button" class="la-btn" @click="startStory">Begin a story</button>
    </section>
  </main>
</template>
