import api from '@/services/api'
import type { GameScenario, GameStory, GameInteraction } from '@/types/game'

export class GameService {
  public static async getScenarios(): Promise<GameScenario[]> {
    const response = await api.get<GameScenario[]>('/game-scenarios/')
    return response.data
  }

  public static async createStory(scenarioId: number, modelName: string): Promise<GameStory> {
    const response = await api.post<GameStory>('/game-stories/', {
      scenario_id: scenarioId,
      model_name: modelName,
    })
    return response.data
  }

  public static async getStory(storyId: number): Promise<GameStory> {
    const response = await api.get<GameStory>(`/game-stories/${storyId}/`)
    return response.data
  }

  public static async interact(storyId: number, userInput: string): Promise<GameInteraction> {
    const response = await api.post<GameInteraction>(
      `/game-stories/${storyId}/interact/`,
      { user_input: userInput }
    )
    return response.data
  }

  public static async getStoryHistory(): Promise<GameStory[]> {
    const response = await api.get<GameStory[]>('/game-stories/')
    return response.data
  }
}
