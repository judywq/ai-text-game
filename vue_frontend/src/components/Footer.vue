<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="py-6 border-t">
    <div class="container mx-auto px-4">
      <div class="text-center text-sm text-muted-foreground">
        <p>&copy; {{ currentYear }} Your Company. All rights reserved.</p>
        <div class="mt-2 space-x-4">
          <router-link :to="{ name: 'terms' }" class="hover:text-primary transition-colors">
            Terms of Service
          </router-link>
          <router-link :to="{ name: 'privacy' }" class="hover:text-primary transition-colors">
            Privacy Policy
          </router-link>
          <a href="mailto:support@yourcompany.com" class="hover:text-primary transition-colors">
            Contact Us
          </a>
        </div>
      </div>
    </div>
  </footer>
</template>
