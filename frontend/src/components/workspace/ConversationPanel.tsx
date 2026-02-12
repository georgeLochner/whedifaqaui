import { useCallback, useEffect, useRef } from 'react'
import type { Citation } from '../../types/chat'
import { useChat } from '../../hooks/useChat'
import { createDocument } from '../../api/documents'
import ChatHistory from '../chat/ChatHistory'
import ChatInput from '../chat/ChatInput'

const SUMMARIZE_PATTERN = /\b(summarize|summarise|summary|generate\s+a?\s*document|create\s+a?\s*document|write\s+a?\s*(summary|report))\b/i

interface ConversationPanelProps {
  onCitationClick?: (citation: Citation) => void
  onCitationsReceived?: (citations: Citation[]) => void
  onDocumentGenerated?: (doc: { id: string; title: string }) => void
}

export default function ConversationPanel({ onCitationClick, onCitationsReceived, onDocumentGenerated }: ConversationPanelProps) {
  const { messages, isLoading, error, sendMessage } = useChat()
  const prevMessageCountRef = useRef(0)
  const pendingSummarizeRef = useRef<string | null>(null)

  const handleSend = useCallback(
    async (text: string) => {
      if (SUMMARIZE_PATTERN.test(text)) {
        pendingSummarizeRef.current = text
      }
      await sendMessage(text)
    },
    [sendMessage]
  )

  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      const newMessages = messages.slice(prevMessageCountRef.current)
      for (const msg of newMessages) {
        if (msg.role === 'assistant' && msg.citations && msg.citations.length > 0) {
          onCitationsReceived?.(msg.citations)
        }
      }

      // If the latest assistant message arrived after a summarize request, generate a document
      const lastMsg = messages[messages.length - 1]
      if (lastMsg?.role === 'assistant' && pendingSummarizeRef.current) {
        const request = pendingSummarizeRef.current
        pendingSummarizeRef.current = null
        createDocument({ request, source_video_ids: [], format: 'markdown' })
          .then((doc) => onDocumentGenerated?.({ id: doc.id, title: doc.title }))
          .catch(() => { /* document generation is best-effort */ })
      }
    }
    prevMessageCountRef.current = messages.length
  }, [messages, onCitationsReceived, onDocumentGenerated])

  return (
    <div data-testid="conversation-panel" className="flex flex-col h-full border-r border-gray-200">
      <ChatHistory messages={messages} onCitationClick={onCitationClick} />
      {error && (
        <div data-testid="chat-error" className="px-4 py-2 text-sm text-red-600 bg-red-50">
          {error}
        </div>
      )}
      {isLoading && (
        <div data-testid="chat-loading" className="px-4 py-2 text-sm text-gray-500">
          Thinking...
        </div>
      )}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  )
}
