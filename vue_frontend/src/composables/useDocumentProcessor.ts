import { ref } from 'vue'
import mammoth from 'mammoth'

export function useDocumentProcessor() {
  const isProcessing = ref(false)

  const processDocument = async (file: File): Promise<string> => {
    isProcessing.value = true
    try {
      const arrayBuffer = await file.arrayBuffer()
      const result = await mammoth.extractRawText({ arrayBuffer })
      return result.value
    } finally {
      isProcessing.value = false
    }
  }

  return {
    processDocument,
    isProcessing,
  }
}
