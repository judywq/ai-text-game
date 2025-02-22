import { ref, onUnmounted } from 'vue'
import type { GameInteraction, TextExplanation, ExplanationStatus } from '@/types/game'

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
// const WS_BASE_URL = 'ws://localhost:8000/ws'
console.debug('useGameWebSocket.ts initialization - WS_BASE_URL:', { WS_BASE_URL })

export function useGameWebSocket() {
  const isConnected = ref(false)
  let socket: WebSocket | null = null
  const onInteractionCreated = ref<((interaction: GameInteraction) => void) | null>(null)
  const onInteractionCompleted = ref<((interaction: GameInteraction) => void) | null>(null)
  const onStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCreated = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStream = ref<((id: number, content: string) => void) | null>(null)
  const onExplanationCompleted = ref<((explanation: TextExplanation) => void) | null>(null)
  const onExplanationStatus = ref<((id: number, status: ExplanationStatus) => void) | null>(null)
  const connect = (storyId: number) => {
    socket = new WebSocket(`${WS_BASE_URL}/game/${storyId}/`)

    socket.onopen = () => {
      isConnected.value = true
    }

    socket.onclose = () => {
      isConnected.value = false
    }

    // socket.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   console.log('interaction_created', data.interaction)
    //   if (data.type === 'interaction_created' && onInteractionCreated.value) {

    //     onInteractionCreated.value(data.interaction)
    //   }
    // }
  }

  const disconnect = () => {
    if (socket) {
      socket.close()
      socket = null
    }
  }

  const startStory = (storyId: number): Promise<GameInteraction> => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }


    return new Promise((resolve, reject) => {
      let currentInteraction: GameInteraction | null = null

      socket!.onmessage = (event) => {
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

      socket!.send(JSON.stringify({
        type: 'start_story'
      }))
    })
  }


  const startInteraction = (storyId: number, userInput: string, clientInteractionId: number): Promise<GameInteraction> => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }


    return new Promise((resolve, reject) => {
      let currentInteraction: GameInteraction | null = null

      socket!.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('data', data)

        switch (data.type) {
          case 'interaction_created':
            if (data.client_id === clientInteractionId) {
              // This is our user interaction
              data.interaction.client_id = clientInteractionId
            } else {
              // This is the assistant's interaction
              currentInteraction = data.interaction
            }
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

      socket!.send(JSON.stringify({
        type: 'interact',
        content: userInput,
        interaction_id: clientInteractionId
      }))
    })
  }

  const lookupExplanation = (
    storyId: number,
    selectedText: string,
    contextText: string,
    clientExplanationId: number
  ): Promise<TextExplanation> => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'))
    }

    return new Promise((resolve, reject) => {
      let currentExplanation: TextExplanation | null = null

      socket!.onmessage = (event) => {
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

      socket!.send(JSON.stringify({
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
  }
}
