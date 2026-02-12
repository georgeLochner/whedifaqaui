import apiClient from './client'
import type { DocumentRequest, DocumentResponse, DocumentDetail } from '../types/document'

export async function createDocument(request: DocumentRequest): Promise<DocumentResponse> {
  const { data } = await apiClient.post<DocumentResponse>('/documents', request)
  return data
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  const { data } = await apiClient.get<DocumentDetail>(`/documents/${id}`)
  return data
}

export async function downloadDocument(id: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/documents/${id}/download`, {
    responseType: 'blob',
  })
  return data
}
