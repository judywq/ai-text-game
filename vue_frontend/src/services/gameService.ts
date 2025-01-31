import api from '@/services/api'
import type { GameScenario, GameStory } from '@/types/game'

export class GameService {
  public static async getScenarios(): Promise<GameScenario[]> {
    const response = await api.get<GameScenario[]>('/game-scenarios/')
    return response.data
  }

  public static async createStory(genre: string, modelName: string): Promise<GameStory> {
    const response = await api.post<GameStory>(
      '/game-stories/',
      {
        genre,
        model_name: modelName,
      }
    );
    return response.data;
  }

  public static async getStory(storyId: number): Promise<GameStory> {
    const response = await api.get<GameStory>(`/game-stories/${storyId}/`)
    return response.data
  }

  public static async getStoryHistory(): Promise<GameStory[]> {
    const response = await api.get<GameStory[]>('/game-stories/')
    return response.data
  }

  public static async pollStoryUpdates(storyId: number): Promise<GameStory> {
    const response = await api.get<GameStory>(`/game-stories/${storyId}/`);
    return response.data;
  }

  public static async startSystemMessage(storyId: number): Promise<GameStory> {
    const response = await api.post<GameStory>(`/game-stories/${storyId}/start/`);
    return response.data;
  }
}
