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
      <div class="home-page">
        <section class="home-hero">
          <h1>An AI-driven Interactive narrative game.</h1>
          <p class="home-lede">Your choice writes the next page.</p>
          <button type="button" class="la-btn" @click="startStory">Begin a story</button>
          <p class="home-scroll-hint">
            Scroll down to watch the demo video
            <span class="home-scroll-hint-arrow" aria-hidden="true">↓</span>
          </p>
        </section>

        <section class="home-demo" aria-label="Demo video">
          <div class="home-demo-frame">
            <iframe
              src="https://www.youtube-nocookie.com/embed/c-htP27LOeA"
              title="GenQuest demo video"
              loading="lazy"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowfullscreen
              referrerpolicy="strict-origin-when-cross-origin"
            />
          </div>
        </section>
      </div>
    </Transition>
  </main>
</template>
