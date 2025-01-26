export interface EssayHistoryResponse {
  count: number
  next: string | null
  previous: string | null
  results: EssayRequest[]
}

export interface EssayRequest {
  id: number
  essay: string
  score: number | null
  error: string | null
  status: 'PENDING' | 'COMPLETED' | 'FAILED'
  created_at: string
}

export interface EssayListResponse {
  count: number
  next: string | null
  previous: string | null
  results: EssayRequest[]
}
