<template>
  <div class="container mx-auto text-center mt-20">
    <h1 class="text-4xl font-bold mb-4">Welcome to GenQuest</h1>
    <p class="text-lg mb-6">A generative text adventure for language learning</p>
    <router-link :to="{name: 'login'}"><Button>Get Started</Button></router-link>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue';
</script>
