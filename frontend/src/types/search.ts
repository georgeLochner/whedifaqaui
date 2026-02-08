export interface SearchRequest {
  query: string
  mode: 'quick' | 'deep'
  filters?: {
    video_id?: string
    speaker?: string
    date_from?: string
    date_to?: string
  }
  limit?: number
  offset?: number
}

export interface SearchResult {
  video_id: string
  video_title: string
  segment_id: string
  start_time: number
  end_time: number
  text: string
  speaker: string | null
  score: number
  highlights: string[]
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
  mode: 'quick' | 'deep'
}
