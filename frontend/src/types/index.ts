// Shared TypeScript types

export interface Video {
  id: string
  title: string
  filename: string
  duration: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string
  updatedAt: string
}

export interface SearchResult {
  videoId: string
  title: string
  timestamp: number
  text: string
  speaker?: string
  score: number
}

export interface HealthStatus {
  status: 'ok' | 'degraded'
  services: {
    postgres: string
    opensearch: string
    redis: string
  }
}
