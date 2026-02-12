export interface Citation {
  video_id: string
  video_title: string
  timestamp: number
  text: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  timestamp: Date
}

export interface ChatRequest {
  message: string
  conversation_id?: string | null
}

export interface ChatResponse {
  message: string
  conversation_id: string
  citations: Citation[]
}
