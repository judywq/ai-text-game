<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { verifyEmailFormSchema } from '@/lib/validations'

const RESEND_COOLDOWN_SECONDS = 60;
const REDIRECT_DELAY_SECONDS = 3;

const authStore = useAuthStore();
const router = useRouter();
const redirectCountdown = ref(REDIRECT_DELAY_SECONDS);
const resendCountdown = ref(0);
const isSubmitting = ref(false);
const isResending = ref(false);
const generalError = ref<string | null>(null);
const generalMessage = ref<string | null>(null);
const success = ref(false);
const pendingEmail = ref<string | null>(null);

let resendInterval: ReturnType<typeof setInterval> | null = null;

const showResendPrompt = computed(() => {
  if (!generalError.value) {
    return false;
  }
  return generalError.value.toLowerCase().includes('resend code');
});

const canResend = computed(() => {
  return resendCountdown.value === 0 && !isResending.value && !success.value;
});

const resendButtonLabel = computed(() => {
  if (isResending.value) {
    return 'Sending...';
  }
  if (resendCountdown.value > 0) {
    return `Resend code (${resendCountdown.value}s)`;
  }
  return 'Resend code';
});

const form = useForm({
  validationSchema: toTypedSchema(verifyEmailFormSchema),
  initialValues: {
    verificationCode: '',
  },
});

const mapApiFieldErrors = (fieldErrors?: Record<string, string>) => {
  if (!fieldErrors) {
    return;
  }

  const mappedErrors: Record<string, string> = {};
  for (const [field, message] of Object.entries(fieldErrors)) {
    mappedErrors[field === 'key' ? 'verificationCode' : field] = message;
  }
  form.setErrors(mappedErrors);
};

const startResendCountdown = () => {
  resendCountdown.value = RESEND_COOLDOWN_SECONDS;
  if (resendInterval) {
    clearInterval(resendInterval);
  }
  resendInterval = setInterval(() => {
    if (resendCountdown.value > 0) {
      resendCountdown.value -= 1;
      return;
    }
    if (resendInterval) {
      clearInterval(resendInterval);
      resendInterval = null;
    }
  }, 1000);
};

onMounted(() => {
  pendingEmail.value = authStore.getPendingVerificationEmail();
  startResendCountdown();
});

onUnmounted(() => {
  if (resendInterval) {
    clearInterval(resendInterval);
  }
});

const handleResend = async () => {
  if (!canResend.value) {
    return;
  }

  if (!pendingEmail.value) {
    generalError.value = 'Enter your email on the sign up page to request a new code.';
    return;
  }

  isResending.value = true;
  generalError.value = null;
  generalMessage.value = null;

  try {
    await authStore.resendVerificationEmail(pendingEmail.value);
    generalMessage.value = 'A new verification code has been sent to your email.';
    form.resetForm();
    startResendCountdown();
  } catch (err: any) {
    mapApiFieldErrors(err.fieldErrors);
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError;
    } else if (!err.fieldErrors) {
      generalError.value = err.message || 'Failed to resend verification code.';
    }
  } finally {
    isResending.value = false;
  }
};

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true;
  generalError.value = null;
  generalMessage.value = null;

  try {
    const response = await authStore.verifyEmail(values.verificationCode);

    if (response?.status === 200) {
      success.value = true;
      redirectCountdown.value = REDIRECT_DELAY_SECONDS;
      generalMessage.value = `Email verification successful! Redirecting to login in ${redirectCountdown.value} seconds...`;

      const countdownInterval = setInterval(() => {
        redirectCountdown.value -= 1;
        generalMessage.value = `Email verification successful! Redirecting to login in ${redirectCountdown.value} seconds...`;

        if (redirectCountdown.value === 0) {
          clearInterval(countdownInterval);
        }
      }, 1000);

      setTimeout(() => {
        router.push({ name: 'login' });
      }, REDIRECT_DELAY_SECONDS * 1000);
    } else {
      generalError.value = 'Email verification failed.';
    }
  } catch (err: any) {
    mapApiFieldErrors(err.fieldErrors);
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError;
    } else if (!err.fieldErrors) {
      generalError.value = err.message || 'Email verification failed.';
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
        <span v-if="pendingEmail">
          Enter the verification code sent to {{ pendingEmail }}
        </span>
        <span v-else>
          Please enter the verification code sent to your email
        </span>
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
          v-if="generalMessage"
          class="text-sm text-center text-success-foreground"
        >
          {{ generalMessage }}
        </div>

        <div
          v-if="generalError"
          class="text-sm text-center text-destructive"
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

        <Button
          v-if="pendingEmail"
          type="button"
          variant="outline"
          class="w-full"
          :disabled="!canResend"
          @click="handleResend"
        >
          {{ resendButtonLabel }}
        </Button>

        <p
          v-if="showResendPrompt && pendingEmail"
          class="text-sm text-center text-muted-foreground"
        >
          Didn't get a code or session expired? Use resend code above.
        </p>

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
