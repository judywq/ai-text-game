export interface GameScenario {
  id: number
  title: string
  description: string
  created_at: string
}

export interface GameInteraction {
  id: number
  user_input: string
  system_response: string
  created_at: string
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
