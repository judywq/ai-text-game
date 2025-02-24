import { ref, onUnmounted } from 'vue'
import type { GameInteraction, TextExplanation, ExplanationStatus } from '@/types/game'

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
// const WS_BASE_URL = 'ws://localhost:8000/ws'
console.debug('useGameWebSocket.ts initialization - WS_BASE_URL:', { WS_BASE_URL })

export function useGameWebSocket() {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const onInteractionCreated = ref<((interaction: any) => void) | null>(null)
  const onInteractionCompleted = ref<((interaction: GameInteraction) => void) | null>(null)
  const onStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCreated = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCompleted = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStatus = ref<((id: number, status: ExplanationStatus) => void) | null>(null)
  const onStoryUpdate = ref<((update: any) => void) | null>(null)

  const connect = (storyId: number) => {
    socket.value = new WebSocket(`${WS_BASE_URL}/game/${storyId}/`)

    socket.value.onopen = () => {
      isConnected.value = true
    }

    socket.value.onclose = () => {
      isConnected.value = false
    }

    socket.value.onmessage = handleMessage
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }

  const startStory = (storyId: number): Promise<GameInteraction> => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }

    return new Promise((resolve, reject) => {
      let currentInteraction: GameInteraction | null = null

      socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('data', data)

        switch (data.type) {
          case 'interaction_created':
            currentInteraction = data.interaction
            if (onInteractionCreated.value && data.interaction) {
              onInteractionCreated.value(data.interaction)
            }
            break

          case 'stream':
            if (currentInteraction && data.interaction_id === currentInteraction.id) {
              if (onStream.value) {
                onStream.value(currentInteraction.id, data.content)
              }
            }
            break

          case 'interaction_completed':
            if (currentInteraction && data.interaction.id === currentInteraction.id) {
              if (onInteractionCompleted.value) {
                onInteractionCompleted.value(data.interaction)
              }
            }
            resolve(data.interaction)
            break

          case 'error':
            reject(new Error(data.error))
            break
        }
      }

      socket.value.send(JSON.stringify({
        type: 'start_story'
      }))
    })
  }

  function handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data)

    switch (data.type) {
      case 'story_update':
        if (onStoryUpdate.value) {
          onStoryUpdate.value(data)
        }
        break
      case 'interaction_created':
        if (onInteractionCreated.value && data.interaction) {
          onInteractionCreated.value(data.interaction)
        }
        break
      case 'stream':
        if (data.interaction_id && data.content) {
          if (onStream.value) {
            onStream.value(data.interaction_id, data.content)
          }
        }
        break
      case 'interaction_completed':
        if (data.interaction && onInteractionCompleted.value) {
          onInteractionCompleted.value(data.interaction)
        }
        break
      case 'error':
        console.error('WebSocket error:', data.error)
        break
    }
  }

  async function startInteraction(storyId: number, data: any) {
    if (!socket.value || !isConnected.value) {
      throw new Error('WebSocket not connected')
    }

    socket.value.send(JSON.stringify({
      type: 'interact',
      ...data
    }))
  }

  const lookupExplanation = (
    storyId: number,
    selectedText: string,
    contextText: string,
    clientExplanationId: number
  ): Promise<TextExplanation> => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }

    return new Promise((resolve, reject) => {
      let currentExplanation: TextExplanation | null = null

      socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('explanation data', data)

        switch (data.type) {
          case 'explanation_created':
            if (data.client_id === clientExplanationId) {
              currentExplanation = data.explanation
              if (onExplanationCreated.value) {
                onExplanationCreated.value(data.explanation)
              }
            }
            break

          case 'explanation_status':
            if (currentExplanation && data.explanation_id === currentExplanation.id) {
              if (onExplanationStatus.value) {
                onExplanationStatus.value(currentExplanation.id, data.status)
              }
            }
            break

          case 'explanation_stream':
            if (currentExplanation && data.explanation_id === currentExplanation.id) {
              if (onExplanationStream.value) {
                onExplanationStream.value(currentExplanation.id, data.content)
              }
            }
            break

          case 'explanation_completed':
            if (currentExplanation && data.explanation.id === currentExplanation.id) {
              if (onExplanationCompleted.value) {
                onExplanationCompleted.value(data.explanation)
              }
              resolve(data.explanation)
            }
            break

          case 'error':
            reject(new Error(data.error))
            break
        }
      }

      socket.value.send(JSON.stringify({
        type: 'explain_text',
        selected_text: selectedText,
        context_text: contextText,
        explanation_id: clientExplanationId
      }))
    })
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    connect,
    disconnect,
    startInteraction,
    startStory,
    onInteractionCreated,
    onInteractionCompleted,
    onStream,
    lookupExplanation,
    onExplanationCreated,
    onExplanationStream,
    onExplanationCompleted,
    onExplanationStatus,
    onStoryUpdate
  }
}
