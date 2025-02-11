<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { GameService } from '@/services/gameService'
import { columns } from '@/components/history/gameColumns'
import DataTable from '@/components/history/DataTable.vue'
import { Button } from '@/components/ui/button'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import type { GameStory } from '@/types/game'

const router = useRouter()
const data = ref<GameStory[]>([])
const selectedRecord = ref<GameStory | null>(null)

async function loadData() {
  try {
    const response = await GameService.getRecentStories(1, 100)
    data.value = response.results
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

function handleRowClick(record: GameStory) {
  router.push(`/game/${record.id}`)
}

function navigateToGame() {
  router.push({ name: 'game-scenarios' })
}

const handleRefresh = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h1 class="text-2xl font-bold">Game History</h1>
        <p class="text-sm text-muted-foreground">Click on a row to continue the game.</p>
      </div>
      <Button @click="navigateToGame">
        <Plus class="mr-2 h-4 w-4" />
        New Game
      </Button>
    </div>

    <DataTable
      :data="data"
      :columns="columns"
      @row-click="handleRowClick"
      @refresh="handleRefresh"
    />
  </div>
</template>
