import apiClient from './client'
import type { Video } from '../types/video'

export interface VideoStatusResponse {
  id: string
  status: Video['status']
  error_message: string | null
}

export interface VideoListResponse {
  videos: Video[]
  total: number
}

export async function uploadVideo(
  file: File,
  metadata: {
    title: string
    recording_date: string
    participants?: string
    context_notes?: string
  },
  onProgress?: (pct: number) => void
): Promise<Video> {
  const form = new FormData()
  form.append('file', file)
  form.append('title', metadata.title)
  form.append('recording_date', metadata.recording_date)
  form.append('participants', metadata.participants ?? '')
  form.append('context_notes', metadata.context_notes ?? '')

  const { data } = await apiClient.post<Video>('/videos', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress(event: { loaded: number; total?: number }) {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total))
      }
    },
  })
  return data
}

export async function getVideos(
  skip = 0,
  limit = 20
): Promise<VideoListResponse> {
  const { data } = await apiClient.get<VideoListResponse>('/videos', {
    params: { skip, limit },
  })
  return data
}

export async function getVideo(id: string): Promise<Video> {
  const { data } = await apiClient.get<Video>(`/videos/${id}`)
  return data
}

export async function getVideoStatus(
  id: string
): Promise<VideoStatusResponse> {
  const { data } = await apiClient.get<VideoStatusResponse>(
    `/videos/${id}/status`
  )
  return data
}
