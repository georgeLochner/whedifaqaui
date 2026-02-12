import { useCallback, useEffect, useState } from 'react'
import type { ChatMessage } from '../types/chat'
import { sendChatMessage } from '../api/chat'

export interface UseChatReturn {
  messages: ChatMessage[]
  conversationId: string | null
  isLoading: boolean
  error: string | null
  sendMessage: (text: string) => Promise<void>
}

const MESSAGES_KEY = 'chat-messages'
const CONV_ID_KEY = 'chat-conversation-id'

function loadMessages(): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(MESSAGES_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return parsed.map((m: ChatMessage) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    }))
  } catch {
    return []
  }
}

function loadConversationId(): string | null {
  return sessionStorage.getItem(CONV_ID_KEY)
}

let messageCounter = Date.now()

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages)
  const [conversationId, setConversationId] = useState<string | null>(loadConversationId)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    sessionStorage.setItem(MESSAGES_KEY, JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    if (conversationId) {
      sessionStorage.setItem(CONV_ID_KEY, conversationId)
    }
  }, [conversationId])

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
