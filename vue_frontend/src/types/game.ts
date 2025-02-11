export interface GameScenario {
  id: number
  category: 'genre' | 'sub-genre'
  name: string
  example: string
  order: number
  created_at: string
}

export interface GameInteraction {
  id: number
  story: number
  role: string
  system_input: string
  system_output: string
  status: 'pending' | 'completed' | 'failed' | 'streaming'
  created_at: string
  updated_at: string
}

export interface GameStory {
  id: number
  title: string
  scenario: GameScenario
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED'
  created_at: string
  updated_at: string
  interactions: GameInteraction[]
}

export interface GameStoryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: GameStory[]
}
