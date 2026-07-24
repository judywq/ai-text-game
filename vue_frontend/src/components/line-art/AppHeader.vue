<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BrandMark from './BrandMark.vue'
import ThemeToggle from './ThemeToggle.vue'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from '@/components/ui/sheet'

const props = withDefaults(
  defineProps<{
    showNav?: boolean
    ctaLabel?: string
    ctaTo?: string | object
  }>(),
  {
    showNav: true,
    ctaLabel: 'New story',
    ctaTo: undefined,
  },
)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isSheetOpen = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || '')

const navItems = [
  { label: 'Stories', name: 'game-scenarios' },
  { label: 'My library', name: 'history' },
]

const resolvedCta = computed(() => props.ctaTo ?? { name: 'game-scenarios' })

function logout() {
  authStore.logout(router)
}

function isCurrent(name: string) {
  return route.name === name
}
</script>

<template>
  <header class="la-header">
    <BrandMark />

    <nav v-if="showNav" class="la-nav" aria-label="Primary navigation">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        :class="{ 'is-current': isCurrent(item.name) }"
      >
        {{ item.label }}
      </router-link>
    </nav>

    <div class="la-header-actions">
      <ThemeToggle />

      <router-link
        v-if="isAuthenticated"
        class="la-header-action"
        :to="resolvedCta"
      >
        {{ ctaLabel }} <span aria-hidden="true">→</span>
      </router-link>

      <Sheet v-model:open="isSheetOpen">
        <SheetTrigger as-child>
          <button type="button" class="la-mobile-menu" aria-label="Open menu">Menu</button>
        </SheetTrigger>
        <SheetContent side="left" class="bg-[var(--paper)] text-[var(--ink)] border-[var(--line)]">
          <SheetDescription class="hidden">Menu</SheetDescription>
          <SheetTitle>
            <BrandMark />
          </SheetTitle>
          <nav class="mt-8 grid gap-5 text-base font-extrabold">
            <router-link
              v-for="item in navItems"
              :key="item.name"
              :to="{ name: item.name }"
              @click="isSheetOpen = false"
            >
              {{ item.label }}
            </router-link>
            <router-link
              v-if="isAuthenticated"
              :to="resolvedCta"
              @click="isSheetOpen = false"
            >
              {{ ctaLabel }}
            </router-link>
            <template v-if="isAuthenticated">
              <router-link :to="{ name: 'history' }" @click="isSheetOpen = false">My library</router-link>
              <router-link :to="{ name: 'change-password' }" @click="isSheetOpen = false">
                Change password
              </router-link>
              <button type="button" class="text-left" @click="logout(); isSheetOpen = false">
                Log out
              </button>
            </template>
            <template v-else>
              <router-link :to="{ name: 'login' }" @click="isSheetOpen = false">Sign in</router-link>
              <router-link :to="{ name: 'signup' }" @click="isSheetOpen = false">Sign up</router-link>
            </template>
          </nav>
        </SheetContent>
      </Sheet>

      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button type="button" class="la-account-trigger" aria-label="Account menu">
            <span aria-hidden="true">{{ isAuthenticated ? (username[0] || 'U').toUpperCase() : '?' }}</span>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <template v-if="isAuthenticated">
            <DropdownMenuLabel>{{ username }}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="router.push({ name: 'history' })">My library</DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'change-password' })">
              Change password
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="logout">Log out</DropdownMenuItem>
          </template>
          <template v-else>
            <DropdownMenuItem @click="router.push({ name: 'login' })">Sign in</DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'signup' })">Sign up</DropdownMenuItem>
          </template>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>
