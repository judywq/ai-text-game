<template>
  <div class="container mx-auto max-w-md text-center py-20">
    <h1 class="text-4xl font-bold mb-4">404</h1>
    <p class="text-xl text-muted-foreground mb-8">Page not found</p>
    <router-link :to="{ name: 'home' }">
      <Button>Return Home</Button>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
</script>
