import api from '@/services/api'
import type { TextExplanation } from '@/types/explanation' // create this type as needed

export class ExplanationService {
  // Send selected text and context to the server for explanation
  public static async lookupExplanation(storyId: number, selectedText: string, contextText: string) {
    const response = await api.post<TextExplanation>(`/game-stories/${storyId}/explanations/`, {
      selected_text: selectedText,
      context_text: contextText,
    })
    return response.data
  }

  // Get the lookup history for a specific game story
  public static async getLookupHistory(storyId: number) {
    const response = await api.get<TextExplanation[]>(`/game-stories/${storyId}/explanations/`)
    return response.data
  }
}
