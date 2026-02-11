export interface Video {
  id: string
  title: string
  file_path: string
  processed_path: string | null
  thumbnail_path: string | null
  duration: number | null
  recording_date: string | null
  participants: string[] | null
  context_notes: string | null
  status: 'uploaded' | 'processing' | 'transcribing' | 'chunking' | 'indexing' | 'ready' | 'error'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Transcript {
  id: string
  video_id: string
  full_text: string
  language: string
  word_count: number
  created_at: string
}

export interface Segment {
  id: string
  transcript_id: string
  video_id: string
  start_time: number
  end_time: number
  text: string
  speaker: string | null
  chunking_method: string
  embedding_indexed: boolean
  created_at: string
}
