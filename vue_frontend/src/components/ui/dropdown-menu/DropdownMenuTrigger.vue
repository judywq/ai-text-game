<script setup lang="ts">
import { DropdownMenuTrigger, type DropdownMenuTriggerProps, useForwardProps } from 'radix-vue'

const props = defineProps<DropdownMenuTriggerProps>()

const forwardedProps = useForwardProps(props)
</script>

<template>
  <!-- Avoid Tailwind outline-none (transparent 2px outline) — it fights circular chrome borders -->
  <DropdownMenuTrigger v-bind="forwardedProps">
    <slot />
  </DropdownMenuTrigger>
</template>
