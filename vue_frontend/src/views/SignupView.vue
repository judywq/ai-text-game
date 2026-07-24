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
  <BookFrame variant="auth-sheet">
    <template #left>
      <aside class="auth-aside">
        <p>
          <strong>Join the shelf.</strong>
          Create an account to save stories, track progress, and pick up any chapter later.
        </p>
      </aside>
    </template>
    <template #right>
      <section class="auth-content">
        <p class="auth-kicker">NEW READER</p>
        <h1>Sign up</h1>
        <p class="auth-lede">Enter your details to start your first adventure.</p>

        <form class="auth-form" @submit="onSubmit">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem class="auth-field">
              <label>Name</label>
              <FormControl>
                <input v-bind="componentField" type="text" placeholder="Your name" :disabled="loading" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="email">
            <FormItem class="auth-field">
              <label>Email</label>
              <FormControl>
                <input
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
            <FormItem class="auth-field">
              <label>Password</label>
              <FormControl>
                <input
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
            <FormItem class="auth-field">
              <label>Confirm password</label>
              <FormControl>
                <input
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

          <button type="submit" class="auth-submit" :disabled="loading || !form.meta.value.valid">
            {{ loading ? 'Creating…' : 'Create account' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="auth-helper">
          Already have an account?
          <router-link :to="{ name: 'login' }">Sign in</router-link>
        </p>
      </section>
    </template>
  </BookFrame>
</template>
