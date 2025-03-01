import api from '@/services/api'
import type { GameScenario, GameStory, GameStoryListResponse, StoryProgress } from '@/types/game'
import { EnhancedEventSource } from '@/services/sse'

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL;

export class GameService {
  public static async getScenarios(): Promise<GameScenario[]> {
    const response = await api.get<GameScenario[]>('/game-scenarios/')
    return response.data
  }

  public static async createStory(
    genre: string,
    sceneText?: string,
    cefrLevel?: string,
    details?: string
  ): Promise<GameStory> {
    const response = await api.post<GameStory>(
      '/game-stories/',
      {
        genre,
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
      timeout: 5 * 60 * 1000 // 5 minutes timeout
    });
    return response.data;
  }

  public static async generateScenesStream(genre: string, details?: string): Promise<EnhancedEventSource> {
    // Create URL with query parameters
    const params = new URLSearchParams();
    params.append('genre', genre);
    if (details) {
      params.append('details', details);
    }

    console.log('params', params.toString())

    // Create and return EventSource for SSE
    const eventSource = new EnhancedEventSource(`/generate-scenes-stream/?${params.toString()}`);
    return eventSource;
  }

  public static async getRecentStories(
    page: number = 1,
    pageSize: number = 10,
  ): Promise<GameStoryListResponse> {
    const response = await api.get<GameStoryListResponse>(`/game-stories/`, {
      params: {
        page,
        page_size: pageSize
      }
    })
    return response.data
  }

  static async getStoryProgress(storyId: number): Promise<StoryProgress[]> {
    const response = await api.get(`/game-stories/${storyId}/progress/`)

    // console.log('response', response)
    return response.data
  }
}
