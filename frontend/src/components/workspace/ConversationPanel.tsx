import { useEffect, useRef } from 'react'
import type { Citation } from '../../types/chat'
import { useChat } from '../../hooks/useChat'
import ChatHistory from '../chat/ChatHistory'
import ChatInput from '../chat/ChatInput'

interface ConversationPanelProps {
  onCitationClick?: (citation: Citation) => void
  onCitationsReceived?: (citations: Citation[]) => void
}

export default function ConversationPanel({ onCitationClick, onCitationsReceived }: ConversationPanelProps) {
  const { messages, isLoading, error, sendMessage } = useChat()
  const prevMessageCountRef = useRef(0)

  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      const newMessages = messages.slice(prevMessageCountRef.current)
      for (const msg of newMessages) {
        if (msg.role === 'assistant' && msg.citations && msg.citations.length > 0) {
          onCitationsReceived?.(msg.citations)
        }
      }
    }
    prevMessageCountRef.current = messages.length
  }, [messages, onCitationsReceived])

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
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
