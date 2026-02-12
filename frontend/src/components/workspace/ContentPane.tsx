import { useCallback, useEffect, useState } from 'react'
import type { ResultItem } from '../../hooks/useWorkspace'
import type { TranscriptSegment } from '../../types/transcript'
import type { DocumentDetail } from '../../types/document'
import { getTranscript } from '../../api/videos'
import { getDocument, downloadDocument } from '../../api/documents'
import { useTranscriptSync } from '../../hooks/useTranscriptSync'
import VideoPlayer from '../video/VideoPlayer'
import TranscriptPanel from '../video/TranscriptPanel'
import DocumentViewer from '../documents/DocumentViewer'

interface ContentPaneProps {
  selectedResult: ResultItem | null
}

export default function ContentPane({ selectedResult }: ContentPaneProps) {
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [currentTime, setCurrentTime] = useState(0)
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined)
  const [documentDetail, setDocumentDetail] = useState<DocumentDetail | null>(null)

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
    if (selectedResult?.type !== 'document' || !selectedResult.documentId) {
      setDocumentDetail(null)
      return
    }

    let cancelled = false
    getDocument(selectedResult.documentId)
      .then((data) => {
        if (!cancelled) setDocumentDetail(data)
      })
      .catch(() => {
        if (!cancelled) setDocumentDetail(null)
      })

    return () => { cancelled = true }
  }, [selectedResult?.documentId, selectedResult?.type])

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

  const handleDownload = useCallback(() => {
    if (!selectedResult?.documentId) return
    downloadDocument(selectedResult.documentId).then((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${documentDetail?.title ?? 'document'}.md`
      a.click()
      URL.revokeObjectURL(url)
    })
  }, [selectedResult?.documentId, documentDetail?.title])

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

      {selectedResult?.type === 'document' && documentDetail && (
        <DocumentViewer
          document={documentDetail}
          onDownload={handleDownload}
        />
      )}

      {selectedResult?.type === 'document' && !documentDetail && (
        <div data-testid="document-loading" className="flex items-center justify-center h-full text-gray-400 text-sm">
          Loading document...
        </div>
      )}
    </div>
  )
}
