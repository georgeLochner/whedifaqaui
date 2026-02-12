import { useCallback, useState } from 'react'
import type { ChatMessage } from '../types/chat'
import { sendChatMessage } from '../api/chat'

export interface UseChatReturn {
  messages: ChatMessage[]
  conversationId: string | null
  isLoading: boolean
  error: string | null
  sendMessage: (text: string) => Promise<void>
}

let messageCounter = 0

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      setError(null)
      setIsLoading(true)

      const userMessage: ChatMessage = {
        id: `user-${++messageCounter}`,
        role: 'user',
        content: text,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])

      try {
        const response = await sendChatMessage(text, conversationId)

        setConversationId(response.conversation_id)

        const aiMessage: ChatMessage = {
          id: `assistant-${++messageCounter}`,
          role: 'assistant',
          content: response.message,
          citations: response.citations,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, aiMessage])
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'An error occurred'
        setError(errorMessage)
      } finally {
        setIsLoading(false)
      }
    },
    [conversationId]
  )

  return { messages, conversationId, isLoading, error, sendMessage }
}
