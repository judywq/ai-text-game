<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { verifyEmailFormSchema } from '@/lib/validations'

// Define the form schema using Zod
const formSchema = toTypedSchema(z.object({
  verificationCode: z.string()
    .min(1, 'Verification code is required'),
}));

const authStore = useAuthStore();
const router = useRouter();
const countdown = ref(3);
const isSubmitting = ref(false);
const generalError = ref<string | null>(null);
const success = ref(false);

const form = useForm({
  validationSchema: toTypedSchema(verifyEmailFormSchema),
  initialValues: {
    verificationCode: '',
  },
});

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true;
  generalError.value = null;

  try {
    const response = await authStore.verifyEmail(values.verificationCode);

    if (response?.status === 200) {
      success.value = true;
      const message = `Email verification successful! Redirecting to login in ${countdown.value} seconds...`;
      generalError.value = message;

      const countdownInterval = setInterval(() => {
        countdown.value -= 1;
        generalError.value = `Email verification successful! Redirecting to login in ${countdown.value} seconds...`;

        if (countdown.value === 0) {
          clearInterval(countdownInterval);
        }
      }, 1000);

      setTimeout(() => {
        router.push({ name: 'login' });
      }, 3000);
    } else {
      generalError.value = 'Email verification failed.';
    }
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError
    }
  } finally {
    isSubmitting.value = false;
  }
});
</script>

<template>
  <Card class="w-full mx-auto sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">
        Email Verification
      </CardTitle>
      <CardDescription>
        Please enter the verification code sent to your email
      </CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit="handleSubmit" class="grid gap-4">
        <FormField
          v-slot="{ componentField }"
          name="verificationCode"
        >
          <FormItem>
            <FormLabel>Verification Code</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="text"
                placeholder="Enter verification code"
                :disabled="isSubmitting || success"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <div
          v-if="generalError"
          :class="{
            'text-success-foreground': success,
            'text-destructive': !success,
            'text-sm text-center': true
          }"
        >
          {{ generalError }}
        </div>

        <Button
          type="submit"
          class="w-full"
          :disabled="isSubmitting || !form.meta.value.valid || success"
        >
          {{ isSubmitting ? 'Verifying...' : 'Verify Email' }}
        </Button>

        <div class="mt-4 text-center text-sm">
          <router-link
            :to="{ name: 'login' }"
            class="underline"
            :tabindex="isSubmitting || success ? -1 : 0"
          >
            Back to Login
          </router-link>
        </div>
      </form>
    </CardContent>
  </Card>
</template>
