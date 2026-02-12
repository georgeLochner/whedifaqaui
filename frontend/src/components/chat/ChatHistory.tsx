import { useEffect, useRef } from 'react'
import type { ChatMessage as ChatMessageType, Citation } from '../../types/chat'
import ChatMessage from './ChatMessage'

interface ChatHistoryProps {
  messages: ChatMessageType[]
  onCitationClick?: (citation: Citation) => void
}

export default function ChatHistory({ messages, onCitationClick }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <div data-testid="chat-history" className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onCitationClick={onCitationClick}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
