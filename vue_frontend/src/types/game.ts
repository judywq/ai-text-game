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
  client_id: number
  story: number
  role: 'user' | 'system' | 'assistant'
  content: string
  status: 'pending' | 'streaming' | 'completed' | 'failed' | 'aborted'
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
