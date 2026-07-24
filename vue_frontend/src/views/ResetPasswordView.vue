<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { AuthService } from '@/services/authService'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { resetPasswordFormSchema } from '@/lib/validations'
import BookFrame from '@/components/line-art/BookFrame.vue'

const router = useRouter()
const route = useRoute()
const isSubmitting = ref(false)
const generalError = ref<string | null>(null)
const success = ref(false)

const form = useForm({
  validationSchema: toTypedSchema(resetPasswordFormSchema),
  initialValues: { password: '', confirmPassword: '' },
})

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true
  generalError.value = null
  try {
    await AuthService.passwordResetConfirm(
      route.params.uid as string,
      route.params.token as string,
      values.password,
    )
    success.value = true
    setTimeout(() => router.push({ name: 'login' }), 3000)
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
          <strong>Fresh ink.</strong>
          Choose a new password and return to your stories.
        </p>
      </aside>
    </template>
    <template #right>
      <section class="auth-content">
        <p class="auth-kicker">PASSWORD</p>
        <h1>Reset password</h1>
        <p class="auth-lede">Enter and confirm your new password.</p>

        <form class="auth-form" @submit="handleSubmit">
          <FormField v-slot="{ componentField }" name="password">
            <FormItem class="auth-field">
              <label>New password</label>
              <FormControl>
                <input
                  v-bind="componentField"
                  type="password"
                  placeholder="Enter your new password"
                  :disabled="isSubmitting || success"
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
                  placeholder="Confirm your new password"
                  :disabled="isSubmitting || success"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <p v-if="generalError" class="la-error">{{ generalError }}</p>
          <p v-if="success" style="color: var(--blue-deep); font-weight: 700">
            Password reset successful. Redirecting to sign in…
          </p>

          <button
            type="submit"
            class="auth-submit"
            :disabled="isSubmitting || !form.meta.value.valid || success"
          >
            {{ isSubmitting ? 'Resetting…' : 'Reset password' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>
      </section>
    </template>
  </BookFrame>
</template>
