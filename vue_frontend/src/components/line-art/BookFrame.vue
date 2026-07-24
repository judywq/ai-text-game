<script setup lang="ts">
withDefaults(
  defineProps<{
    variant: string
    as?: string
  }>(),
  { as: 'section' },
)
</script>

<template>
  <component :is="as" :class="variant">
    <slot name="left" />
    <slot name="right" />
    <slot />
  </component>
</template>
