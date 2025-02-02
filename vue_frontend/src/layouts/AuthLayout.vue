<script setup lang="ts">
import Footer from '@/components/Footer.vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import { onMounted } from 'vue';

const authStore = useAuthStore();
const router = useRouter();

// Redirect authenticated users to game-scenarios instead of dashboard
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push({ name: 'game-scenarios' });
  }
});
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <!-- NavBar (simplified version) -->
    <nav class="w-full py-4 border-b">
      <div class="container mx-auto px-4">
        <router-link :to="{ name: 'home' }" class="flex items-center justify-center">
          <!-- Replace with your actual logo -->
          <span class="text-2xl font-bold text-primary">ATG</span>
        </router-link>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow flex items-start justify-center px-4 py-8">
      <div class="w-full mt-0 sm:mt-20">
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
            appear
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- Footer -->
    <Footer />
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
</style>
