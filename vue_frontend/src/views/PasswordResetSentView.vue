<template>
  <Card class="w-full mx-auto sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Password Reset Sent</CardTitle>
      <CardDescription>
        Please check your email for a link to reset your password.
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div class="grid gap-4">
        <router-link :to="{ name: 'login' }">
          <Button class="w-full"> Back to Login </Button>
        </router-link>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>
