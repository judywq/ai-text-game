export interface LLMModel {
  order: number
  is_default: boolean
  name: string
  display_name: string
  used_quota: number
  daily_limit: number
}
