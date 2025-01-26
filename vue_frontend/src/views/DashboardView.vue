<template>
  <Card class="max-w-4xl mx-auto">
    <CardHeader>
      <CardTitle>Evaluate your essay</CardTitle>
      <CardDescription> Enter your text directly or upload a Word document </CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit="handleSubmit" class="space-y-4">
        <FormField
          v-slot="{ componentField }"
          name="model_name"
        >
          <FormItem>
            <Select
              v-bind="componentField"
              :disabled="isProcessing || isPending"
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem
                    v-for="model in modelOptions"
                    :key="model.name"
                    :value="model.name"
                  >
                    {{ model.display_name }}
                    <span
                      v-if="model.daily_limit"
                      :class="{
                        'text-red-500': model.used_quota >= model.daily_limit,
                        'text-muted-foreground': model.used_quota < model.daily_limit
                      }"
                      class="ml-2"
                    >
                      ({{ model.used_quota }}/{{ model.daily_limit }})
                    </span>
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        </FormField>

        <FileUpload accept=".docx,.doc" :loading="isProcessing" :disabled="isLoading"
          @file-selected="handleFileSelected" />

        <FormField
          v-slot="{ componentField }"
          name="essay"
        >
          <FormItem>
            <FormControl>
              <Textarea
                v-bind="componentField"
                :rows="20"
                placeholder="Enter your text here or upload a document..."
                :disabled="isProcessing || isPending"
              />
            </FormControl>
            <FormMessage />
            <div class="flex justify-between items-center text-sm">
              <p class="text-muted-foreground" :class="{ invisible: !currentRequest }">
                Status:
                <span :class="{
                  'text-yellow-500': isPending,
                  'text-green-500': isCompleted,
                  'text-red-500': isFailed,
                }">
                  {{ currentRequest?.status }}
                </span>
              </p>
              <p class="text-muted-foreground" :class="{ 'text-destructive': isOverLimit }">
                {{ charCount }}/{{ MAX_CHARS }}
              </p>
            </div>
          </FormItem>
        </FormField>

        <div v-if="currentRequest">
          <p v-if="isCompleted" class="text-4xl font-semibold text-green-600 mt-2">
            Score: {{ currentRequest?.score }}
          </p>
          <p v-if="isFailed" class="text-sm text-destructive mt-2">
            {{ currentRequest?.error }}
          </p>
        </div>

        <p v-if="generalError" class="text-destructive text-sm">{{ generalError }}</p>

        <Button
          type="submit"
          class="w-full"
          :disabled="isLoading || isProcessing || isPending || !form.meta.value.valid"
        >
          <Loader2 v-if="isLoading || isPending" class="mr-2 h-4 w-4 animate-spin" />
          {{ isLoading ? 'Submitting...' : isPending ? 'Processing...' : 'Submit' }}
        </Button>

        <router-link :to="{ name: 'history' }"
          class="text-sm text-muted-foreground hover:text-primary mt-2 block text-right underline">View
          History</router-link>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Loader2 } from 'lucide-vue-next'
import FileUpload from '@/components/FileUpload.vue'
import { useDocumentProcessor } from '@/composables/useDocumentProcessor'
import { useToast } from '@/components/ui/toast/use-toast'
import { EssayService } from '@/services/essayService'
import type { EssayRequest } from '@/types/essay'
import { AxiosError } from 'axios'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { LLMModelService } from '@/services/llmModelService'
import type { LLMModel } from '@/types/llm'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import * as z from 'zod'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { essayFormSchema, MAX_CHARS } from '@/lib/validations'

const form = useForm({
  validationSchema: toTypedSchema(essayFormSchema),
  initialValues: {
    essay: '',
    model_name: '',
  },
})

const { toast } = useToast()
const { processDocument, isProcessing } = useDocumentProcessor()

const generalError = ref('')
const isLoading = ref(false)
const charCount = computed(() => form.values.essay?.length || 0)
const isOverLimit = computed(() => charCount.value > MAX_CHARS)
const isPending = computed(() => currentRequest.value?.status === 'PENDING')
const isCompleted = computed(() => currentRequest.value?.status === 'COMPLETED')
const isFailed = computed(() => currentRequest.value?.status === 'FAILED')

const currentRequest = ref<EssayRequest | null>(null)
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

const selectedModel = ref('')
const modelOptions = ref<LLMModel[]>([])

const updateModelQuotas = async () => {
  try {
    const models = await LLMModelService.getActiveModels()
    modelOptions.value = models
    // Keep the same selected model but with updated quota
    const updatedSelectedModel = models.find(model => model.name === selectedModel.value)
    if (!updatedSelectedModel) {
      // If current selected model is no longer available, select default or first
      const defaultModel = models.find(model => model.is_default)
      selectedModel.value = defaultModel?.name || models[0]?.name || ''
      form.setFieldValue('model_name', selectedModel.value)
    }
  } catch (err) {
    console.error('Error updating models:', err)
  }
}

onMounted(async () => {
  await updateModelQuotas()
})

const handleFileSelected = async (file: File) => {
  generalError.value = ''
  isLoading.value = true

  try {
    const text = await processDocument(file)
    if (text.length > MAX_CHARS) {
      toast({
        description: `The uploaded document exceeds ${MAX_CHARS} characters. Only the first ${MAX_CHARS} characters will be used.`,
        variant: 'destructive',
      })
      form.setFieldValue('essay', text.slice(0, MAX_CHARS))
    } else {
      form.setFieldValue('essay', text)
    }
  } catch (err) {
    toast({
      description: "Failed to process document. Please make sure it's a valid Word document.",
      variant: 'destructive',
    })
    console.error('Error processing document:', err)
  } finally {
    isLoading.value = false
  }
}

const startPolling = (requestId: number) => {
  // Clear any existing polling
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }

  let attempts = 0
  const baseDelay = 500 // Start with 0.5 second
  const maxDelay = 10000 // Max delay of 10 seconds

  const poll = async () => {
    try {
      const data = await EssayService.getEssay(requestId)
      currentRequest.value = data

      if (data.status !== 'PENDING') {
        // Stop polling if we're no longer pending
        if (pollingInterval.value) {
          clearInterval(pollingInterval.value)
          pollingInterval.value = null
        }

        // Show result or error and update quotas when request completes
        if (data.status === 'COMPLETED') {
          await updateModelQuotas()
          toast({
            title: 'Evaluation Complete',
            description: `Your essay score: ${data.score}`,
          })
        } else if (data.error) {
          toast({
            title: 'Evaluation Failed',
            description: data.error,
            variant: 'destructive',
          })
        }
        return
      }

      // Calculate next delay with exponential backoff
      const delay = Math.min(baseDelay * Math.pow(2, attempts), maxDelay)
      attempts++
      console.debug('Polling again in', delay, 'ms')

      // Schedule next poll
      pollingInterval.value = setTimeout(poll, delay)
    } catch (err) {
      console.error('Error polling status:', err)
      if (pollingInterval.value) {
        clearTimeout(pollingInterval.value)
        pollingInterval.value = null
      }
      toast({
        description: 'Failed to get evaluation status',
        variant: 'destructive',
      })
    }
  }

  // Start first poll immediately
  poll()
}

const handleSubmit = form.handleSubmit(async (values) => {
  generalError.value = ''
  isLoading.value = true

  currentRequest.value = null
  try {
    const response = await EssayService.submitEssay({
      essay: values.essay,
      model_name: values.model_name
    })
    currentRequest.value = response

    // Start polling for status
    startPolling(response.id)

    toast({
      description: 'Essay submitted successfully. Processing...',
    })
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError
    }
  } finally {
    isLoading.value = false
  }
})

// Clean up polling when component is unmounted
onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
})
</script>
