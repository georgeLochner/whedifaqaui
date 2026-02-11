export interface TranscriptSegment {
  id: string
  start_time: number
  end_time: number
  text: string
  speaker: string | null
  timestamp_formatted: string
}

export interface TranscriptResponse {
  video_id: string
  segments: TranscriptSegment[]
  count: number
}
