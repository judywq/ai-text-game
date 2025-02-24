export interface GameScenario {
  id: number
  category: 'genre' | 'sub-genre'
  name: string
  example: string
  order: number
  created_at: string
}

export interface StoryProgress {
  id: number
  content: string
  decision_point_id: string
  chosen_option_id: string
  chosen_option_text: string
  is_end_point: boolean
  created_at: string
  options: StoryOption[]
}

export interface GameStory {
  id: number
  title: string
  scenario: GameScenario
  status: 'INIT' | 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'
  created_at: string
  updated_at: string
  progress?: StoryProgress[]
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
