<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { AuthService } from '@/services/authService'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { forgotPasswordFormSchema } from '@/lib/validations'
import BookFrame from '@/components/line-art/BookFrame.vue'

const router = useRouter()
const isSubmitting = ref(false)
const generalError = ref<string | null>(null)

const form = useForm({
  validationSchema: toTypedSchema(forgotPasswordFormSchema),
  initialValues: { email: '' },
})

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true
  generalError.value = null
  try {
    await AuthService.passwordReset(values.email)
    router.push({ name: 'password-reset-sent' })
  } catch (err: any) {
    if (err.fieldErrors) form.setErrors(err.fieldErrors)
    if (err.nonFieldError) generalError.value = err.nonFieldError
  } finally {
    isSubmitting.value = false
  }
})
</script>

<template>
  <BookFrame variant="auth-sheet">
    <template #left>
      <aside class="auth-aside">
        <p>
          <strong>Lost the key?</strong>
          Tell us your email and we’ll send a reset link.
        </p>
      </aside>
    </template>
    <template #right>
      <section class="auth-content">
        <p class="auth-kicker">PASSWORD</p>
        <h1>Forgot password</h1>
        <p class="auth-lede">We’ll email you a secure link to choose a new one.</p>

        <form class="auth-form" @submit="handleSubmit">
          <FormField v-slot="{ componentField }" name="email">
            <FormItem class="auth-field">
              <label>Email</label>
              <FormControl>
                <input
                  v-bind="componentField"
                  type="email"
                  placeholder="name@example.com"
                  :disabled="isSubmitting"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <p v-if="generalError" class="la-error">{{ generalError }}</p>

          <button
            type="submit"
            class="auth-submit"
            :disabled="isSubmitting || !form.meta.value.valid"
          >
            {{ isSubmitting ? 'Sending…' : 'Send reset link' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="auth-helper">
          Remembered it?
          <router-link :to="{ name: 'login' }">Back to sign in</router-link>
        </p>
      </section>
    </template>
  </BookFrame>
</template>
