
export type ExplanationStatus = 'pending' | 'streaming' | 'completed' | 'failed'
export interface TextExplanation {
  id: number
  story: number
  selected_text: string
  context_text: string
  explanation: string
  status: ExplanationStatus
  error?: string
  created_at: string
}
