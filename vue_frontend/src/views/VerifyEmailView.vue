<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { verifyEmailFormSchema } from '@/lib/validations'
import BookFrame from '@/components/line-art/BookFrame.vue'

const authStore = useAuthStore()
const router = useRouter()
const countdown = ref(3)
const isSubmitting = ref(false)
const generalError = ref<string | null>(null)
const success = ref(false)

const form = useForm({
  validationSchema: toTypedSchema(verifyEmailFormSchema),
  initialValues: { verificationCode: '' },
})

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true
  generalError.value = null
  try {
    const response = await authStore.verifyEmail(values.verificationCode)
    if (response?.status === 200) {
      success.value = true
      generalError.value = `Email verified! Redirecting in ${countdown.value}s…`
      const countdownInterval = setInterval(() => {
        countdown.value -= 1
        generalError.value = `Email verified! Redirecting in ${countdown.value}s…`
        if (countdown.value === 0) clearInterval(countdownInterval)
      }, 1000)
      setTimeout(() => router.push({ name: 'login' }), 3000)
    } else {
      generalError.value = 'Email verification failed.'
    }
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
          <strong>One more step.</strong>
          Enter the code from your inbox to unlock your shelf.
        </p>
      </aside>
    </template>
    <template #right>
      <section class="auth-content">
        <p class="auth-kicker">VERIFY</p>
        <h1>Confirm email</h1>
        <p class="auth-lede">Paste the verification code we sent you.</p>

        <form class="auth-form" @submit="handleSubmit">
          <FormField v-slot="{ componentField }" name="verificationCode">
            <FormItem class="auth-field">
              <label>Verification code</label>
              <FormControl>
                <input
                  v-bind="componentField"
                  class="code-input"
                  type="text"
                  placeholder="••••••••"
                  :disabled="isSubmitting || success"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <p v-if="generalError" :class="success ? '' : 'la-error'" :style="success ? 'color: var(--blue-deep)' : undefined">
            {{ generalError }}
          </p>

          <button
            type="submit"
            class="auth-submit"
            :disabled="isSubmitting || !form.meta.value.valid || success"
          >
            {{ isSubmitting ? 'Verifying…' : 'Verify email' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="auth-helper">
          <router-link :to="{ name: 'login' }">Back to sign in</router-link>
        </p>
      </section>
    </template>
  </BookFrame>
</template>
