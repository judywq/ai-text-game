export interface GameScenario {
  id: number
  category: 'genre' | 'theme'
  parent: number | null
  name: string
  description: string
  example: string
  order: number
  created_at?: string
}

export interface StoryProgress {
  id: number
  content: string
  image_url?: string
  decision_point_id: string
  chosen_option_id: string
  chosen_option_text: string
  is_end_point: boolean
  created_at: string
  updated_at: string
  options: StoryOption[]
}

export interface GameStory {
  id: number
  title: string
  /** API returns a string genre; scenario kept for older clients. */
  genre?: string
  scenario?: GameScenario
  details?: string
  status: 'INIT' | 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'
  created_at: string
  updated_at: string
  progress?: StoryProgress[]
  theme?: string
}

export interface GameStoryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: GameStory[]
}

export interface StoryOption {
  option_id: string
  option_name: string
}

export interface StoryUpdate {
  type: 'story_update'
  content: string
  status: string
  current_decision: string | null
  options: StoryOption[]
}

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

export interface VocabularyQuizAnswerPayload {
  explanation_id: number
  user_explanation: string
}

export interface VocabularyQuizResultItem {
  explanation_id: number
  selected_text: string
  score: number
  reason: string
  user_explanation?: string
}

export interface VocabularyQuizSubmitResponse {
  results: VocabularyQuizResultItem[]
  average_score: number
}
