<script setup lang="ts">
import BookFrame from '@/components/line-art/BookFrame.vue'
</script>

<template>
  <BookFrame variant="auth-sheet">
    <template #left>
      <aside class="auth-aside">
        <p>
          <strong>Check your mail.</strong>
          A reset link is on its way if that address is registered.
        </p>
      </aside>
    </template>
    <template #right>
      <section class="auth-content">
        <div class="status-mark" aria-hidden="true">✓</div>
        <p class="auth-kicker">SENT</p>
        <h1>Reset link sent</h1>
        <p class="auth-lede">Please check your email for a link to reset your password.</p>
        <router-link :to="{ name: 'login' }" class="auth-submit">
          Back to sign in <span aria-hidden="true">→</span>
        </router-link>
        <p class="auth-helper">Didn’t get it? Check spam, or try again in a few minutes.</p>
      </section>
    </template>
  </BookFrame>
</template>
