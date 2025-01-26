<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { EssayService } from '@/services/essayService'
import { columns } from '@/components/history/columns'
import DataTable from '@/components/history/DataTable.vue'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import type { EssayRequest } from '@/types/essay'
import { ScrollArea } from '@/components/ui/scroll-area'

const router = useRouter()

const ITEMS_TO_RETRIEVE = 1000
const data = ref<EssayRequest[]>([])
const totalItems = ref(0)
const currentPage = ref(1)
const selectedRecord = ref<EssayRequest | null>(null)
const showDialog = ref(false)

async function loadData(page: number) {
  try {
    const response = await EssayService.getEssayHistory(page, ITEMS_TO_RETRIEVE)
    data.value = response.results
    totalItems.value = response.count
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

function handleRowClick(record: EssayRequest) {
  selectedRecord.value = record
  showDialog.value = true
}

function navigateToDashboard() {
  router.push({ name: 'dashboard' })
}

onMounted(() => {
  loadData(1)
})
</script>

<template>
  <div class="container mx-auto">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h1 class="text-2xl font-bold">Evaluation History</h1>
        <p class="text-sm text-muted-foreground">Click on a row to view the details.</p>
      </div>
      <Button @click="navigateToDashboard">
        <Plus class="mr-2 h-4 w-4" />
        New Evaluation
      </Button>
    </div>

    <DataTable :data="data" :columns="columns" @row-click="handleRowClick" />

    <Dialog :open="showDialog" @update:open="showDialog = false">
      <DialogContent class="max-w-2xl max-h-[80vh]">
        <ScrollArea class="h-full max-h-[70vh]">
          <div v-if="selectedRecord" class="space-y-4">
            <h2 class="text-2xl font-bold">Evaluation Details</h2>
            <div>
              <h3 class="font-medium">Essay</h3>
              <p class="mt-1">{{ selectedRecord.essay }}</p>
            </div>
            <div>
              <h3 class="font-medium">Score</h3>
              <p class="mt-1">{{ selectedRecord.score }}</p>
            </div>
            <div>
              <h3 class="font-medium">Status</h3>
              <p class="mt-1">{{ selectedRecord.status }}</p>
            </div>
            <div>
              <h3 class="font-medium">Created At</h3>
              <p class="mt-1">{{ new Date(selectedRecord.created_at).toLocaleString() }}</p>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  </div>
</template>
