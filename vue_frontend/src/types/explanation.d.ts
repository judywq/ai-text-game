export interface TextExplanation {
  id: number
  user: number | string
  story: number
  selected_text: string
  context_text: string
  explanation: string
  created_at: string
}
