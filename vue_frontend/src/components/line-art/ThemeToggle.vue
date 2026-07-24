<script setup lang="ts">
import { onMounted, ref } from 'vue'

const THEME_KEY = 'gq-line-art-theme'
const isDark = ref(false)

function applyTheme(theme: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', theme)
  isDark.value = theme === 'dark'
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    /* ignore */
  }
}

function toggle() {
  applyTheme(isDark.value ? 'light' : 'dark')
}

onMounted(() => {
  const current = document.documentElement.getAttribute('data-theme')
  isDark.value = current === 'dark'
})
</script>

<template>
  <button
    type="button"
    class="la-btn la-btn--icon theme-toggle"
    :aria-label="isDark ? 'Switch to light theme' : 'Switch to dark theme'"
    :aria-pressed="isDark"
    @click="toggle"
  />
</template>
