import apiClient from './client'
import type { ChatResponse } from '../types/chat'

export async function sendChatMessage(
  message: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  const payload: { message: string; conversation_id?: string } = { message }
  if (conversationId) {
    payload.conversation_id = conversationId
  }
  const { data } = await apiClient.post<ChatResponse>('/chat', payload)
  return data
}
