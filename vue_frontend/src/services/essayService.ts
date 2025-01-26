import api from '@/services/api'
import type { EssayRequest, EssayListResponse } from '@/types/essay'

export class EssayService {
  public static async submitEssay({essay, model_name}: {essay: string, model_name: string}): Promise<EssayRequest> {
    const response = await api.post<EssayRequest>('/requests/', { essay, model_name })
    return response.data
  }

  public static async getEssay(requestId: number): Promise<EssayRequest> {
    const response = await api.get<EssayRequest>(`/requests/${requestId}/`)
    return response.data
  }

  public static async getEssayHistory(
    page: number = 1,
    pageSize: number = 10,
  ): Promise<EssayListResponse> {
    const response = await api.get<EssayListResponse>('/requests/', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }
}
