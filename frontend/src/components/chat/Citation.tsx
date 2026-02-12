import type { Citation as CitationType } from '../../types/chat'
import { formatTimestamp } from '../../utils/timestamp'

interface CitationProps {
  citation: CitationType
  onClick: (citation: CitationType) => void
}

export default function Citation({ citation, onClick }: CitationProps) {
  return (
    <button
      data-testid="citation"
      type="button"
      onClick={() => onClick(citation)}
      className="inline text-blue-600 hover:text-blue-800 underline cursor-pointer font-medium"
    >
      [{citation.video_title} @ {formatTimestamp(citation.timestamp)}]
    </button>
  )
}
