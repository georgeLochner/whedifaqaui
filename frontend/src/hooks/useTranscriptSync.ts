import { useMemo } from 'react'
import type { TranscriptSegment } from '../types/transcript'

export function useTranscriptSync(
  segments: TranscriptSegment[],
  currentTime: number
): string | null {
  const activeSegmentId = useMemo(() => {
    const active = segments.find(
      (seg) => seg.start_time <= currentTime && currentTime < seg.end_time
    )
    return active?.id ?? null
  }, [segments, currentTime])

  return activeSegmentId
}
