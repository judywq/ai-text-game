import api from '@/services/api'
import type {
  TextExplanation,
  VocabularyQuizAnswerPayload,
  VocabularyQuizSubmitResponse,
} from '@/types/game'

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

  public static async submitVocabularyQuiz(
    storyId: number,
    answers: VocabularyQuizAnswerPayload[]
  ) {
    const response = await api.post<VocabularyQuizSubmitResponse>(
      `/game-stories/${storyId}/vocabulary-quiz/submit/`,
      { answers },
      { timeout: 120000 }
    )
    return response.data
  }
}
