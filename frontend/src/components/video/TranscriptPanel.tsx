import { useEffect, useRef } from 'react'
import type { TranscriptSegment } from '../../types/transcript'
import TimestampLink from './TimestampLink'

interface TranscriptPanelProps {
  segments: TranscriptSegment[]
  activeSegmentId: string | null
  onSegmentClick: (segment: TranscriptSegment) => void
}

export default function TranscriptPanel({
  segments,
  activeSegmentId,
  onSegmentClick,
}: TranscriptPanelProps) {
  const activeRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [activeSegmentId])

  return (
    <div
      data-testid="transcript-panel"
      className="overflow-y-auto max-h-[600px] space-y-1 p-4"
    >
      {segments.map((segment) => {
        const isActive = segment.id === activeSegmentId
        return (
          <div
            key={segment.id}
            ref={isActive ? activeRef : null}
            data-testid="transcript-segment"
            className={`p-2 rounded cursor-pointer hover:bg-gray-50 ${isActive ? 'active bg-blue-50 border-l-4 border-blue-500' : ''}`}
            onClick={() => onSegmentClick(segment)}
          >
            <div className="flex items-center gap-2 mb-1">
              {segment.speaker && (
                <span
                  data-testid="speaker-label"
                  className="text-xs font-semibold text-gray-600"
                >
                  {segment.speaker}:
                </span>
              )}
              <TimestampLink
                seconds={segment.start_time}
                onClick={() => onSegmentClick(segment)}
              />
            </div>
            <p className="text-sm text-gray-800">{segment.text}</p>
          </div>
        )
      })}
    </div>
  )
}
