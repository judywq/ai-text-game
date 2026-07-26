<script setup lang="ts">
defineProps<{
  to?: string | object
}>()
</script>

<template>
  <router-link :to="to ?? { name: 'home' }" class="la-brand" aria-label="GenQuest home">
    <img class="la-mark" src="/favicon.svg" alt="" width="39" height="39" aria-hidden="true" />
    <span>GenQuest</span>
  </router-link>
</template>
