import { ref } from 'vue'
import type { GameInteraction } from '@/types/game'

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL

export function useGameStream() {
  const streamingContent = ref('')
  let eventSource: EventSource | null = null

  const startStream = (storyId: number, userInput: string, isSystem: boolean = false): Promise<GameInteraction> => {
    streamingContent.value = ''

    return new Promise((resolve, reject) => {
      const interaction: GameInteraction = {
        id: Date.now(),
        story: storyId,
        role: isSystem ? 'system' : 'user',
        content: userInput,
        status: 'streaming',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      const endpoint = isSystem
        ? `${API_BASE_URL}/game-stories/${storyId}/start/`
        : `${API_BASE_URL}/game-stories/${storyId}/interact/?content=${encodeURIComponent(userInput)}`

      eventSource = new EventSource(endpoint, { withCredentials: true })

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource?.close()
          interaction.status = 'completed'
          resolve(interaction)
          return
        }

        const data = JSON.parse(event.data)
        if (data.error) {
          eventSource?.close()
          interaction.status = 'failed'
          reject(new Error(data.error))
          return
        }

        interaction.content += data.content
        streamingContent.value = interaction.content
      }

      eventSource.onerror = (error) => {
        eventSource?.close()
        interaction.status = 'failed'
        reject(error)
      }
    })
  }

  const stopStream = () => {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  return {
    streamingContent,
    startStream,
    stopStream
  }
}
