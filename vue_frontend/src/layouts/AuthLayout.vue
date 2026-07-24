<script setup lang="ts">
import BrandMark from '@/components/line-art/BrandMark.vue'
import ThemeToggle from '@/components/line-art/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

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
      <div class="auth-header-actions">
        <ThemeToggle />
        <router-link :to="rightLink.to" class="la-quiet-link">{{ rightLink.label }}</router-link>
      </div>
    </header>

    <main class="auth-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in" appear>
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.auth-header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
