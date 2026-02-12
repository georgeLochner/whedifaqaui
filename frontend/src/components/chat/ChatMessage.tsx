import type { ChatMessage as ChatMessageType, Citation as CitationType } from '../../types/chat'
import { parseTimestamp } from '../../utils/timestamp'
import Citation from './Citation'

interface ChatMessageProps {
  message: ChatMessageType
  onCitationClick?: (citation: CitationType) => void
}

/**
 * Parse message content for [Video Title @ MM:SS] citation patterns.
 * Returns an array of string segments and Citation components.
 */
function renderContentWithCitations(
  content: string,
  citations: CitationType[],
  onCitationClick?: (citation: CitationType) => void
): React.ReactNode[] {
  const citationPattern = /\[([^\]]+?)\s*@\s*(\d+:\d{2})\]/g
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = citationPattern.exec(content)) !== null) {
    // Add text before the citation
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index))
    }

    const videoTitle = match[1]
    const timestampStr = match[2]
    const timestampSeconds = parseTimestamp(timestampStr)

    // Find matching citation from the citations array, or create one from the parsed text
    const citationData: CitationType = citations.find(
      (c) => c.video_title === videoTitle && Math.abs(c.timestamp - timestampSeconds) < 2
    ) ?? {
      video_id: '',
      video_title: videoTitle,
      timestamp: timestampSeconds,
      text: match[0],
    }

    parts.push(
      <Citation
        key={`citation-${match.index}`}
        citation={citationData}
        onClick={onCitationClick ?? (() => {})}
      />
    )

    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex))
  }

  return parts
}

export default function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      data-testid={isUser ? 'user-message' : 'ai-message'}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        {isUser ? (
          message.content
        ) : (
          <span className="whitespace-pre-wrap">
            {renderContentWithCitations(
              message.content,
              message.citations ?? [],
              onCitationClick
            )}
          </span>
        )}
      </div>
    </div>
  )
}
