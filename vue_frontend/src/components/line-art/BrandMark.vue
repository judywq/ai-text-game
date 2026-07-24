<script setup lang="ts">
defineProps<{
  to?: string | object
}>()
</script>

<template>
  <router-link :to="to ?? { name: 'home' }" class="la-brand" aria-label="GenQuest home">
    <span class="la-mark" aria-hidden="true"><i></i><i></i></span>
    <span>GenQuest</span>
  </router-link>
</template>
