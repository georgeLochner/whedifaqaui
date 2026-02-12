export interface DocumentRequest {
  request: string
  source_video_ids?: string[]
  format?: string
}

export interface DocumentResponse {
  id: string
  title: string
  preview: string
  source_count: number
  created_at: string
}

export interface DocumentDetail {
  id: string
  title: string
  content: string
  source_video_ids: string[]
  created_at: string
}
