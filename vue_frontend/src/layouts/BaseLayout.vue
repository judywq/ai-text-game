<script setup lang="ts">
import AppHeader from '@/components/line-art/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const hideChrome = computed(() => route.name === 'game-play')

onMounted(() => {
  if (!authStore.isAuthenticated && router.currentRoute.value.meta.requiresAuth) {
    router.push({ name: 'login' })
  }
})
</script>

<template>
  <div class="min-h-dvh">
    <div v-if="!hideChrome" class="la-shell" style="padding-bottom: 0; min-height: 0">
      <AppHeader />
    </div>

    <main>
      <router-view v-slot="{ Component }">
        <transition name="la-fade" mode="out-in" appear>
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>
