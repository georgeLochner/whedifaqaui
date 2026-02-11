import apiClient from './client'
import type { SearchResponse } from '../types/search'

export async function searchVideos(
  query: string,
  limit?: number
): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>('/search', {
    params: { q: query, ...(limit !== undefined && { limit }) },
  })
  return data
}
