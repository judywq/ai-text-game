<template>
  <div id="app">
      <router-view></router-view>
  </div>
  <Toaster />
</template>

<script setup lang="ts">
import Toaster from '@/components/ui/toast/Toaster.vue'
</script>
