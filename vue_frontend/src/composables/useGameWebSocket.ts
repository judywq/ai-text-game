import { ref, onUnmounted } from 'vue'
import type { TextExplanation, ExplanationStatus, StoryUpdate } from '@/types/game'

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
// const WS_BASE_URL = 'ws://localhost:8000/ws'
console.debug('useGameWebSocket.ts initialization - WS_BASE_URL:', { WS_BASE_URL })

export function useGameWebSocket() {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const onStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCreated = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCompleted = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStatus = ref<((id: number, status: ExplanationStatus) => void) | null>(null)
  const onStoryUpdate = ref<((update: StoryUpdate) => void) | null>(null)
  const onError = ref<((error: Error) => void) | null>(null)

  const pendingExplanationPromise = ref<{
    resolve: (value: TextExplanation) => void;
    reject: (reason: Error) => void;
    currentExplanation: TextExplanation | null;
    clientExplanationId: number;
  } | null>(null)

  function handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data)
    // console.log('WebSocket message:', data)

    switch (data.type) {
      case 'story_update':
        if (onStoryUpdate.value) {
          onStoryUpdate.value(data as StoryUpdate)
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
          if (pendingExplanationPromise.value) {
            pendingExplanationPromise.value.resolve(data.explanation)
            pendingExplanationPromise.value = null
          }
        }
        break

      case 'error':
        const error = new Error(data.error)
        if (pendingExplanationPromise.value) {
          pendingExplanationPromise.value.reject(error)
          pendingExplanationPromise.value = null
        }
        if (onError.value) {
          onError.value(error)
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

  const startStory = (storyId: number) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }
    socket.value?.send(JSON.stringify({
      type: 'start_story'
    }))
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
    onStream,
    lookupExplanation,
    onExplanationCreated,
    onExplanationStream,
    onExplanationCompleted,
    onExplanationStatus,
    onStoryUpdate,
    onError,
  }
}
