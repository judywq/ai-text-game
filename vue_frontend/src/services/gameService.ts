import api from '@/services/api'
import type { GameScenario, GameStory } from '@/types/game'

export class GameService {
  public static async getScenarios(): Promise<GameScenario[]> {
    const response = await api.get<GameScenario[]>('/game-scenarios/')
    return response.data
  }

  public static async createStory(
    genre: string,
    modelName: string,
    sceneText?: string,
    cefrLevel?: string,
    details?: string
  ): Promise<GameStory> {
    const response = await api.post<GameStory>(
      '/game-stories/',
      {
        genre,
        model_name: modelName,
        scene_text: sceneText,
        cefr_level: cefrLevel,
        details: details
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

  public static async generateScenes(genre: string, details?: string) {
    const response = await api.post<{
      scenes: Array<{
        level: string;
        text: string;
      }>;
    }>('/generate-scenes/', {
      genre,
      details
    }, {
      timeout: 10000 // 10 second timeout
    });
    return response.data;
  }
}
