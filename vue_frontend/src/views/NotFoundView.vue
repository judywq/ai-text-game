<template>
  <div class="doc-shell" style="padding-top: 0">
    <article class="document error-document">
      <p class="error-code" aria-hidden="true">404</p>
      <h1>Lost between chapters</h1>
      <p>This page isn’t on the shelf. Head home and open a story that is.</p>
      <router-link :to="{ name: 'home' }">
        Return home <span aria-hidden="true">→</span>
      </router-link>
    </article>
  </div>
</template>
