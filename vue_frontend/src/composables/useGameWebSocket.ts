import { ref, onUnmounted } from 'vue'
import type { GameInteraction, TextExplanation, ExplanationStatus, StoryUpdate } from '@/types/game'

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
  const onStoryUpdate = ref<((update: StoryUpdate) => void) | null>(null)

  // Add these new refs to track promises
  const pendingStoryPromise = ref<{
    resolve: (value: GameInteraction) => void;
    reject: (reason: Error) => void;
    currentInteraction: GameInteraction | null;
  } | null>(null)

  const pendingExplanationPromise = ref<{
    resolve: (value: TextExplanation) => void;
    reject: (reason: Error) => void;
    currentExplanation: TextExplanation | null;
    clientExplanationId: number;
  } | null>(null)

  function handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data)
    console.log('WebSocket message:', data)

    switch (data.type) {
      case 'story_update':
        if (onStoryUpdate.value) {
          onStoryUpdate.value(data as StoryUpdate)
        }
        break

      case 'interaction_created':
        if (pendingStoryPromise.value) {
          pendingStoryPromise.value.currentInteraction = data.interaction
        }
        if (onInteractionCreated.value && data.interaction) {
          onInteractionCreated.value(data.interaction)
        }
        break

      case 'stream':
        if (data.interaction_id && onStream.value) {
          onStream.value(data.interaction_id, data.content)
        }
        break

      case 'interaction_completed':
        if (pendingStoryPromise.value &&
            pendingStoryPromise.value.currentInteraction?.id === data.interaction.id) {
          pendingStoryPromise.value.resolve(data.interaction)
          pendingStoryPromise.value = null
        }
        if (onInteractionCompleted.value) {
          onInteractionCompleted.value(data.interaction)
        }
        break

      case 'explanation_created':
        if (pendingExplanationPromise.value &&
            data.client_id === pendingExplanationPromise.value.clientExplanationId) {
          pendingExplanationPromise.value.currentExplanation = data.explanation
          if (onExplanationCreated.value) {
            onExplanationCreated.value(data.explanation)
          }
        }
        break

      case 'explanation_status':
        if (pendingExplanationPromise.value?.currentExplanation?.id === data.explanation_id) {
          if (onExplanationStatus.value) {
            onExplanationStatus.value(data.explanation_id, data.status)
          }
        }
        break

      case 'explanation_stream':
        if (pendingExplanationPromise.value?.currentExplanation?.id === data.explanation_id) {
          if (onExplanationStream.value) {
            onExplanationStream.value(data.explanation_id, data.content)
          }
        }
        break

      case 'explanation_completed':
        if (pendingExplanationPromise.value?.currentExplanation?.id === data.explanation.id) {
          if (onExplanationCompleted.value) {
            onExplanationCompleted.value(data.explanation)
          }
          pendingExplanationPromise.value.resolve(data.explanation)
          pendingExplanationPromise.value = null
        }
        break

      case 'error':
        const error = new Error(data.error)
        if (pendingStoryPromise.value) {
          pendingStoryPromise.value.reject(error)
          pendingStoryPromise.value = null
        }
        if (pendingExplanationPromise.value) {
          pendingExplanationPromise.value.reject(error)
          pendingExplanationPromise.value = null
        }
        console.error('WebSocket error:', error)
        break
    }
  }

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
      pendingStoryPromise.value = {
        resolve,
        reject,
        currentInteraction: null
      }

      socket.value?.send(JSON.stringify({
        type: 'start_story'
      }))
    })
  }

  const selectOption = (optionId: string) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }

    socket.value.send(JSON.stringify({
      type: 'interact',
      option_id: optionId
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
      pendingExplanationPromise.value = {
        resolve,
        reject,
        currentExplanation: null,
        clientExplanationId
      }

      socket.value?.send(JSON.stringify({
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
    selectOption,
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
