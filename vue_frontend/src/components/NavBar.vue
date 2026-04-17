<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { CircleUser, Menu, Search, Users } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || '')
const logout = () => {
  authStore.logout(router)
}
const menuItems = [
  {
    label: 'Game',
    name: 'game-scenarios',
  },
]
const isSheetOpen = ref(false)
</script>

<template>
  <header
    class="sticky top-0 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6 z-50"
  >
    <nav
      class="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6"
    >
      <router-link :to="{ name: 'home' }" class="items-center text-xl font-semibold"> GenQuest </router-link>
      <router-link
        v-for="item in menuItems"
        :key="item.label"
        :to="{ name: item.name }"
        class="text-muted-foreground transition-colors hover:text-foreground"
        :class="{ 'text-primary': $route.name === item.name }"
      >
        <span>{{ item.label }}</span>
      </router-link>
      <a
        href="/admin"
        target="_blank"
        class="text-muted-foreground transition-colors hover:text-foreground"
      >
        <span>Admin</span>
      </a>
    </nav>
    <Sheet v-model:open="isSheetOpen">
      <SheetTrigger as-child>
        <Button variant="outline" size="icon" class="shrink-0 md:hidden">
          <Menu class="h-5 w-5" />
          <span class="sr-only">Toggle navigation menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <SheetDescription className="hidden">Menu</SheetDescription>
        <SheetTitle><router-link
            :to="{ name: 'home' }"
            class="items-center text-2xl font-semibold"
            @click="isSheetOpen = false"
          >
            GenQuest
          </router-link></SheetTitle>
        <nav class="mt-6 grid gap-6 text-lg font-medium">
          <router-link v-for="item in menuItems" :key="item.label"
            :to="{ name: item.name }"
            class="text-muted-foreground hover:text-foreground"
            :class="{ 'text-primary': $route.name === item.name }"
            @click="isSheetOpen = false"
          >
            <span>{{ item.label }}</span>
          </router-link>
          <a
            href="/admin"
            target="_blank"
            class="text-muted-foreground transition-colors hover:text-foreground"
          >
            <span>Admin</span>
          </a>
        </nav>
      </SheetContent>
    </Sheet>
    <div class="ml-auto flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
      <div class="ml-auto flex-1 sm:flex-initial"></div>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="secondary" size="icon" class="rounded-full">
            <CircleUser class="h-5 w-5" />
            <span class="sr-only">Toggle user menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <template v-if="isAuthenticated">
            <DropdownMenuLabel>{{ username }}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="router.push({ name: 'history' })">History</DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'change-password' })">
              Change Password
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="logout">Logout</DropdownMenuItem>
          </template>
          <template v-else>
            <DropdownMenuItem @click="router.push({ name: 'login' })">Login</DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'signup' })">Sign up</DropdownMenuItem>
          </template>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>
