import api from '@/services/api'
import type { LLMModel } from '@/types/llm'

export class LLMModelService {
  public static async getActiveModels(): Promise<LLMModel[]> {
    const response = await api.get<LLMModel[]>('/llm-models/')
    return response.data
  }
}
