import { useState } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [text, setText] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = text.trim()
    if (trimmed && !isLoading) {
      onSend(trimmed)
      setText('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t border-gray-200">
      <input
        data-testid="chat-input"
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask a question..."
        disabled={isLoading}
        className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2 border disabled:opacity-50"
      />
      <button
        data-testid="send-button"
        type="submit"
        disabled={!text.trim() || isLoading}
        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </form>
  )
}
