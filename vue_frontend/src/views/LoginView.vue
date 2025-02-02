<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-vue-next';
import { storeToRefs } from 'pinia';
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
import { loginFormSchema } from '@/lib/validations'

const authStore = useAuthStore();
const { loading } = storeToRefs(authStore);
const router = useRouter();
const route = useRoute();

const form = useForm({
  validationSchema: toTypedSchema(loginFormSchema),
  initialValues: {
    email: '',
    password: '',
  },
});

const generalError = ref<string | null>(null);

const onSubmit = form.handleSubmit(async (values) => {
  try {
    generalError.value = null;
    await authStore.login(values.email, values.password);

    if (authStore.isAuthenticated) {
      const redirectPath = typeof route.query.redirect === 'string'
        ? route.query.redirect
        : { name: 'game-scenarios' };
      router.push(redirectPath);
    }
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError;
    }
  }
});
</script>

<template>
  <Card class="w-full mx-auto sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">
        Login
      </CardTitle>
      <CardDescription>
        Enter your email below to login to your account
      </CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit="onSubmit" class="grid gap-4">
        <FormField
          v-slot="{ componentField }"
          name="email"
        >
          <FormItem>
            <FormLabel>Email</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="email"
                placeholder="name@example.com"
                :disabled="loading"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField
          v-slot="{ componentField }"
          name="password"
        >
          <FormItem>
            <div class="flex items-center">
              <FormLabel>Password</FormLabel>
              <router-link
                :to="{ name: 'forgot-password'}"
                class="ml-auto inline-block text-sm underline"
                :tabindex="loading ? -1 : 0"
              >
                Forgot your password?
              </router-link>
            </div>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                placeholder="Enter your password"
                :disabled="loading"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <Button
          type="submit"
          class="w-full"
          :disabled="loading || !form.meta.value.valid"
        >
          <Loader2
            v-if="loading"
            class="mr-2 h-4 w-4 animate-spin"
          />
          {{ loading ? 'Logging in...' : 'Login' }}
        </Button>

        <div v-if="generalError" class="text-destructive text-sm">
          {{ generalError }}
        </div>

        <div class="mt-4 text-center text-sm">
          Don't have an account?
          <router-link
            :to="{ name: 'signup' }"
            class="underline"
            :tabindex="loading ? -1 : 0"
          >
            Sign up
          </router-link>
        </div>
      </form>
    </CardContent>
  </Card>
</template>
