<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { loginFormSchema } from '@/lib/validations'
import BookFrame from '@/components/line-art/BookFrame.vue'

const authStore = useAuthStore()
const { loading } = storeToRefs(authStore)
const router = useRouter()
const route = useRoute()

const form = useForm({
  validationSchema: toTypedSchema(loginFormSchema),
  initialValues: { email: '', password: '' },
})

const generalError = ref<string | null>(null)

const onSubmit = form.handleSubmit(async (values) => {
  try {
    generalError.value = null
    await authStore.login(values.email, values.password)
    if (authStore.isAuthenticated) {
      const redirectPath =
        typeof route.query.redirect === 'string'
          ? route.query.redirect
          : { name: 'game-scenarios' }
      router.push(redirectPath)
    }
  } catch (err: any) {
    if (err.fieldErrors) form.setErrors(err.fieldErrors)
    if (err.nonFieldError) generalError.value = err.nonFieldError
  }
})
</script>

<template>
  <BookFrame variant="auth-book">
    <template #left>
      <section class="story-page">
        <p class="eyebrow">CHAPTER 00</p>
        <div class="story-copy">
          <span class="chapter-label">Welcome back</span>
          <h1>Open the next page.</h1>
          <p class="story-description">
            Sign in to continue your stories, save new chapters, and keep learning through choice.
          </p>
        </div>
        <div class="trail" aria-hidden="true">
          <span class="trail-line line-one"></span>
          <span class="trail-line line-two"></span>
          <span class="trail-node node-one"></span>
          <span class="trail-node node-two"></span>
          <span class="trail-node node-three"></span>
        </div>
      </section>
    </template>

    <template #right>
      <section class="form-page">
        <div class="form-heading">
          <p class="eyebrow">ACCOUNT</p>
          <h2>Sign in</h2>
          <p>Enter your email and password to continue.</p>
        </div>

        <form class="login-form" @submit="onSubmit">
          <FormField v-slot="{ componentField }" name="email">
            <FormItem class="field">
              <label for="email">Email</label>
              <FormControl>
                <input
                  id="email"
                  v-bind="componentField"
                  type="email"
                  placeholder="name@example.com"
                  :disabled="loading"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="password">
            <FormItem class="field">
              <div class="field-label-row">
                <label for="password">Password</label>
                <router-link :to="{ name: 'forgot-password' }" :tabindex="loading ? -1 : 0">
                  Forgot password?
                </router-link>
              </div>
              <FormControl>
                <input
                  id="password"
                  v-bind="componentField"
                  type="password"
                  placeholder="Enter your password"
                  :disabled="loading"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <p v-if="generalError" class="la-error">{{ generalError }}</p>

          <button type="submit" class="la-btn" :disabled="loading || !form.meta.value.valid">
            {{ loading ? 'Signing in…' : 'Sign in' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="signup-prompt">
          Don't have an account?
          <router-link :to="{ name: 'signup' }" :tabindex="loading ? -1 : 0">Sign up</router-link>
        </p>
        <p class="mobile-note">Your shelf is waiting on every device.</p>
      </section>
    </template>
  </BookFrame>
</template>
