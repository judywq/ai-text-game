<script setup lang="ts">
import BrandMark from '@/components/line-art/BrandMark.vue'
import ThemeToggle from '@/components/line-art/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const headerNote = computed(() => {
  const map: Record<string, string> = {
    login: 'Sign in to continue your chapter',
    signup: 'Create your reader account',
    'verify-email': 'Confirm your email to begin',
    'forgot-password': 'We’ll send a reset link',
    'reset-password': 'Choose a new password',
    'password-reset-sent': 'Check your inbox',
  }
  return map[String(route.name)] || ''
})

const rightLink = computed(() => {
  if (route.name === 'login' || route.name === 'signup') {
    return route.name === 'login'
      ? { to: { name: 'signup' }, label: 'Sign up' }
      : { to: { name: 'login' }, label: 'Sign in' }
  }
  return { to: { name: 'login' }, label: 'Back to sign in' }
})

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push({ name: 'game-scenarios' })
  }
})
</script>

<template>
  <div :class="route.name === 'login' ? 'line-login' : 'auth-shell'">
    <header :class="route.name === 'login' ? 'site-header' : 'auth-header'">
      <BrandMark />
      <p v-if="headerNote" class="header-note" style="margin: 0; color: var(--ink-soft); font-size: 0.92rem">
        {{ headerNote }}
      </p>
      <div style="display: flex; align-items: center; gap: 14px; margin-left: auto">
        <ThemeToggle />
        <router-link :to="rightLink.to" class="la-quiet-link">{{ rightLink.label }}</router-link>
      </div>
    </header>

    <main>
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in" appear>
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 800px) {
  .header-note {
    display: none;
  }
}
</style>
