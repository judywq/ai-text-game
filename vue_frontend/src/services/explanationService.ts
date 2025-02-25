import api from '@/services/api'
import type { TextExplanation } from '@/types/game'

export class ExplanationService {
  // Get the lookup history for a specific game story
  public static async getLookupHistory(storyId: number) {
    const response = await api.get<TextExplanation[]>(`/game-stories/${storyId}/explanations/`)
    return response.data
  }

  // Get a single explanation
  public static async getExplanation(storyId: number, explanationId: number) {
    const response = await api.get<TextExplanation>(
      `/game-stories/${storyId}/explanations/${explanationId}/`
    )
    return response.data
  }
}
