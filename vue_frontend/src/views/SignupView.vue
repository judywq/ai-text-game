<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { signupFormSchema } from '@/lib/validations'
import BookFrame from '@/components/line-art/BookFrame.vue'

const authStore = useAuthStore()
const { loading } = storeToRefs(authStore)
const router = useRouter()
const generalError = ref<string | null>(null)

const form = useForm({
  validationSchema: toTypedSchema(signupFormSchema),
  initialValues: { name: '', email: '', password: '', confirmPassword: '' },
})

const onSubmit = form.handleSubmit(async (values) => {
  try {
    generalError.value = null
    await authStore.signup(values.email, values.password, values.name, router)
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
          <span class="chapter-label">New reader</span>
          <h1>Join the shelf.</h1>
          <p class="story-description">
            Create an account to save stories, track progress, and pick up any chapter later.
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
      <section class="form-page form-page--signup">
        <div class="form-heading">
          <p class="eyebrow">NEW READER</p>
          <h2>Sign up</h2>
          <p>Enter your details to start your first adventure.</p>
        </div>

        <form class="login-form login-form--dense" @submit="onSubmit">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem class="field">
              <label for="signup-name">Name</label>
              <FormControl>
                <input
                  id="signup-name"
                  v-bind="componentField"
                  type="text"
                  placeholder="Your name"
                  :disabled="loading"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="email">
            <FormItem class="field">
              <label for="signup-email">Email</label>
              <FormControl>
                <input
                  id="signup-email"
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
              <label for="signup-password">Password</label>
              <FormControl>
                <input
                  id="signup-password"
                  v-bind="componentField"
                  type="password"
                  placeholder="Create a password"
                  :disabled="loading"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="confirmPassword">
            <FormItem class="field">
              <label for="signup-confirm">Confirm password</label>
              <FormControl>
                <input
                  id="signup-confirm"
                  v-bind="componentField"
                  type="password"
                  placeholder="Confirm your password"
                  :disabled="loading"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <p v-if="generalError" class="la-error">{{ generalError }}</p>

          <button type="submit" class="la-btn" :disabled="loading || !form.meta.value.valid">
            {{ loading ? 'Creating…' : 'Create account' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="signup-prompt">
          Already have an account?
          <router-link :to="{ name: 'login' }" :tabindex="loading ? -1 : 0">Sign in</router-link>
        </p>
        <p class="mobile-note">Your shelf is waiting on every device.</p>
      </section>
    </template>
  </BookFrame>
</template>
