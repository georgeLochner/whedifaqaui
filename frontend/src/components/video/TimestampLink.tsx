import { formatTimestamp } from '../../utils/timestamp'

interface TimestampLinkProps {
  seconds: number
  onClick: () => void
}

export default function TimestampLink({ seconds, onClick }: TimestampLinkProps) {
  return (
    <button
      data-testid="timestamp-link"
      type="button"
      className="text-blue-600 hover:text-blue-800 hover:underline font-mono text-sm"
      onClick={onClick}
    >
      {formatTimestamp(seconds)}
    </button>
  )
}
