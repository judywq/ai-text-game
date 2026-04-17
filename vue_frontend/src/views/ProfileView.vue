<template>
  <div class="container mx-auto py-8 px-4">
    <Card class="w-full mx-auto sm:max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">Profile</CardTitle>
        <CardDescription>
          Set your explanation language. Word explanations in the game will be written in this language.
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">Explanation language</label>
          <Select v-model="nativeLanguageModel">
            <SelectTrigger class="w-full">
              <SelectValue placeholder="Not set" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="NATIVE_LANGUAGE_UNSET">Not set</SelectItem>
              <SelectItem
                v-for="opt in NATIVE_LANGUAGE_OPTIONS"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div v-if="generalError" class="text-destructive text-sm">
          {{ generalError }}
        </div>

        <Button
          class="w-full"
          :disabled="isSubmitting"
          @click="handleSave"
        >
          {{ isSubmitting ? 'Saving...' : 'Save' }}
        </Button>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/components/ui/toast/use-toast'
import { AuthService } from '@/services/authService'
import { useAuthStore } from '@/stores/auth'
import {
  NATIVE_LANGUAGE_OPTIONS,
  NATIVE_LANGUAGE_UNSET,
} from '@/constants/nativeLanguage'

const authStore = useAuthStore()
const { toast } = useToast()

const nativeLanguageModel = ref<string>(
  authStore.user?.native_language ?? NATIVE_LANGUAGE_UNSET,
)
const isSubmitting = ref(false)
const generalError = ref<string | null>(null)

watch(
  () => authStore.user?.native_language,
  (v) => {
    nativeLanguageModel.value = v ?? NATIVE_LANGUAGE_UNSET
  },
)

async function handleSave() {
  isSubmitting.value = true
  generalError.value = null
  try {
    const payload =
      nativeLanguageModel.value === NATIVE_LANGUAGE_UNSET
        ? { native_language: null as null }
        : { native_language: nativeLanguageModel.value }
    const user = await AuthService.updateUser(payload)
    authStore.user = user
    authStore.saveState()
    toast({
      title: 'Saved',
      description: 'Your profile has been updated.',
    })
  } catch (err: unknown) {
    generalError.value =
      err && typeof err === 'object' && 'message' in err
        ? String((err as { message: string }).message)
        : 'Failed to save profile'
    toast({
      title: 'Error',
      description: generalError.value,
      variant: 'destructive',
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>
