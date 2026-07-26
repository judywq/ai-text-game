<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Menu, User } from 'lucide-vue-next'
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

withDefaults(
  defineProps<{
    showNav?: boolean
  }>(),
  {
    showNav: true,
  },
)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isSheetOpen = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || '')
const isAdmin = computed(() => !!authStore.user?.is_staff)

const navItems = [
  { label: 'Stories', name: 'game-scenarios' },
  { label: 'My library', name: 'history' },
]

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
      <a v-if="isAdmin" href="/admin/">Admin</a>
    </nav>

    <div class="la-header-actions">
      <Sheet v-model:open="isSheetOpen">
        <SheetTrigger as-child>
          <button type="button" class="la-mobile-menu" aria-label="Open menu">
            <Menu :size="18" :stroke-width="2" aria-hidden="true" />
          </button>
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
            <a v-if="isAdmin" href="/admin/" @click="isSheetOpen = false">Admin</a>
            <template v-if="isAuthenticated">
              <p class="m-0 text-sm font-bold text-[var(--ink-soft)]">{{ username }}</p>
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
            <div class="flex items-center justify-between gap-3">
              <span>Theme</span>
              <ThemeToggle />
            </div>
          </nav>
        </SheetContent>
      </Sheet>

      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button type="button" class="la-account-trigger" aria-label="Account menu">
            <span class="la-btn la-btn--icon la-account-face" aria-hidden="true">
              <User class="la-account-icon" :stroke-width="1.75" />
            </span>
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
          <DropdownMenuSeparator />
          <div class="flex items-center justify-between gap-3 px-2 py-1.5 text-sm">
            <span>Theme</span>
            <ThemeToggle />
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>
