import { useCallback, useEffect, useState } from 'react'
import type { ResultItem } from '../../hooks/useWorkspace'
import type { TranscriptSegment } from '../../types/transcript'
import { getTranscript } from '../../api/videos'
import { useTranscriptSync } from '../../hooks/useTranscriptSync'
import VideoPlayer from '../video/VideoPlayer'
import TranscriptPanel from '../video/TranscriptPanel'

interface ContentPaneProps {
  selectedResult: ResultItem | null
}

export default function ContentPane({ selectedResult }: ContentPaneProps) {
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [currentTime, setCurrentTime] = useState(0)
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined)

  const activeSegmentId = useTranscriptSync(segments, currentTime)

  useEffect(() => {
    if (selectedResult?.type !== 'video' || !selectedResult.videoId) {
      setSegments([])
      return
    }

    let cancelled = false
    getTranscript(selectedResult.videoId)
      .then((data) => {
        if (!cancelled) setSegments(data.segments)
      })
      .catch(() => {
        if (!cancelled) setSegments([])
      })

    return () => { cancelled = true }
  }, [selectedResult?.videoId, selectedResult?.type])

  useEffect(() => {
    if (selectedResult?.type === 'video' && selectedResult.timestamp != null) {
      setSeekTime(selectedResult.timestamp)
    }
  }, [selectedResult])

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time)
  }, [])

  const handleSegmentClick = useCallback((segment: TranscriptSegment) => {
    setCurrentTime(segment.start_time)
    setSeekTime(segment.start_time)
  }, [])

  return (
    <div data-testid="content-pane" className="flex flex-col h-full border-l border-gray-200 overflow-y-auto">
      {!selectedResult && (
        <div data-testid="content-pane-empty" className="flex items-center justify-center h-full text-gray-400 text-sm">
          Select a result to view content
        </div>
      )}

      {selectedResult?.type === 'video' && selectedResult.videoId && (
        <div className="flex flex-col h-full">
          <div className="p-4">
            <VideoPlayer
              videoId={selectedResult.videoId}
              onTimeUpdate={handleTimeUpdate}
              seekTo={seekTime}
            />
          </div>
          <div className="flex-1 overflow-y-auto">
            <TranscriptPanel
              segments={segments}
              activeSegmentId={activeSegmentId}
              onSegmentClick={handleSegmentClick}
            />
          </div>
        </div>
      )}

      {selectedResult?.type === 'document' && (
        <div data-testid="document-viewer" className="flex flex-col h-full p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {selectedResult.documentTitle}
          </h3>
          <div className="flex-1" />
          <div className="pt-4 border-t border-gray-200">
            <button
              data-testid="document-download"
              type="button"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
            >
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
