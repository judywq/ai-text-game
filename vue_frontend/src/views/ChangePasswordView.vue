<script setup lang="ts">
import { ref } from 'vue'
import { AuthService } from '@/services/authService'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { useToast } from '@/components/ui/toast/use-toast'
import { changePasswordFormSchema } from '@/lib/validations'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import BookFrame from '@/components/line-art/BookFrame.vue'
import PasswordInput from '@/components/PasswordInput.vue'

const isSubmitting = ref(false)
const generalError = ref<string | null>(null)
const success = ref(false)
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const { toast } = useToast()
const authStore = useAuthStore()
const router = useRouter()

const form = useForm({
  validationSchema: toTypedSchema(changePasswordFormSchema),
  initialValues: { old_password: '', new_password1: '', new_password2: '' },
})

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true
  generalError.value = null
  try {
    await AuthService.changePassword(
      values.old_password,
      values.new_password1,
      values.new_password2,
    )
    success.value = true
    authStore.setMustChangePasswordFalse()
    toast({
      title: 'Success',
      description: 'Your password has been changed successfully.',
    })
    setTimeout(() => router.push({ name: 'game-scenarios' }), 3000)
  } catch (err: any) {
    if (err.fieldErrors) form.setErrors(err.fieldErrors)
    if (err.nonFieldError) generalError.value = err.nonFieldError
  } finally {
    isSubmitting.value = false
  }
})
</script>

<template>
  <div class="auth-shell" style="padding-top: 0; min-height: 0">
    <BookFrame variant="auth-sheet">
      <template #left>
        <aside class="auth-aside">
          <p>
            <strong>Keep it safe.</strong>
            Update your password, then return to your stories.
          </p>
        </aside>
      </template>
      <template #right>
        <section class="auth-content">
          <p class="auth-kicker">ACCOUNT</p>
          <h1>Change password</h1>
          <p class="auth-lede">Enter your current password and choose a new one.</p>

          <form class="auth-form" @submit="handleSubmit">
            <FormField v-slot="{ componentField }" name="old_password">
              <FormItem class="auth-field">
                <label>Current password</label>
                <FormControl>
                  <PasswordInput
                    v-bind="componentField"
                    v-model:visible="showOldPassword"
                    placeholder="Current password"
                    :disabled="isSubmitting || success"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>
            <FormField v-slot="{ componentField }" name="new_password1">
              <FormItem class="auth-field">
                <label>New password</label>
                <FormControl>
                  <PasswordInput
                    v-bind="componentField"
                    v-model:visible="showNewPassword"
                    placeholder="New password"
                    :disabled="isSubmitting || success"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>
            <FormField v-slot="{ componentField }" name="new_password2">
              <FormItem class="auth-field">
                <label>Confirm new password</label>
                <FormControl>
                  <PasswordInput
                    v-bind="componentField"
                    v-model:visible="showNewPassword"
                    placeholder="Confirm new password"
                    :disabled="isSubmitting || success"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <p v-if="generalError" class="la-error">{{ generalError }}</p>
            <p v-if="success" style="color: var(--blue-deep); font-weight: 700">
              Password changed! Redirecting…
            </p>

            <button
              type="submit"
              class="auth-submit"
              :disabled="isSubmitting || !form.meta.value.valid || success"
            >
              {{ isSubmitting ? 'Saving…' : 'Change password' }}
              <span aria-hidden="true">→</span>
            </button>
          </form>
        </section>
      </template>
    </BookFrame>
  </div>
</template>
