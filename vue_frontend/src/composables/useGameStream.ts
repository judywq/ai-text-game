import { ref } from 'vue'
import type { GameInteraction } from '@/types/game'

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL

export function useGameStream() {
  const streamingContent = ref('')
  let eventSource: EventSource | null = null

  const startStream = (storyId: number, userInput: string): Promise<GameInteraction> => {
    streamingContent.value = ''

    return new Promise((resolve, reject) => {
      const interaction: GameInteraction = {
        id: Date.now(),
        story: storyId,
        role: 'user',
        system_input: userInput,
        system_output: '',
        status: 'streaming',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      eventSource = new EventSource(
        `${API_BASE_URL}/game-stories/${storyId}/interact/?system_input=${encodeURIComponent(userInput)}`,
        { withCredentials: true }
      )

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

        interaction.system_output += data.content
        streamingContent.value = interaction.system_output
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
