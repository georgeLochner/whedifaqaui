import { useEffect, useState, useCallback } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { getVideo, getTranscript } from '../api/videos'
import { useTranscriptSync } from '../hooks/useTranscriptSync'
import { formatTimestamp } from '../utils/timestamp'
import VideoPlayer from '../components/video/VideoPlayer'
import TranscriptPanel from '../components/video/TranscriptPanel'
import type { Video } from '../types/video'
import type { TranscriptSegment, TranscriptResponse } from '../types/transcript'

function VideoPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()

  const [video, setVideo] = useState<Video | null>(null)
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined)

  const initialTime = searchParams.get('t')
    ? Number(searchParams.get('t'))
    : undefined

  const segments = transcript?.segments ?? []
  const activeSegmentId = useTranscriptSync(segments, currentTime)

  useEffect(() => {
    if (!id) return

    async function fetchData() {
      try {
        setLoading(true)
        const [videoData, transcriptData] = await Promise.all([
          getVideo(id!),
          getTranscript(id!),
        ])
        setVideo(videoData)
        setTranscript(transcriptData)
      } catch {
        setError('Failed to load video')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time)
  }, [])

  const handleSegmentClick = useCallback(
    (segment: TranscriptSegment) => {
      setCurrentTime(segment.start_time)
      setSeekTime(segment.start_time)
      setSearchParams({ t: String(segment.start_time) }, { replace: true })
    },
    [setSearchParams]
  )

  if (loading) {
    return (
      <div data-testid="video-page-loading" className="px-4 py-6 sm:px-0">
        <div className="flex items-center justify-center py-16">
          <span className="text-gray-500 text-lg">Loading video...</span>
        </div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div data-testid="video-page-error" className="px-4 py-6 sm:px-0">
        <div className="flex items-center justify-center py-16">
          <span className="text-red-500 text-lg">
            {error ?? 'Video not found'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div data-testid="video-page" className="px-4 py-6 sm:px-0">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{video.title}</h1>
        <div className="flex gap-4 mt-1 text-sm text-gray-500">
          {video.recording_date && <span>Recorded: {video.recording_date}</span>}
          {video.duration != null && (
            <span>Duration: {formatTimestamp(video.duration)}</span>
          )}
          {video.participants && video.participants.length > 0 && (
            <span>Participants: {video.participants.join(', ')}</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <VideoPlayer
            videoId={video.id}
            onTimeUpdate={handleTimeUpdate}
            initialTime={initialTime}
            seekTo={seekTime}
          />
        </div>

        <div className="bg-white shadow rounded-lg">
          <h2 className="text-lg font-medium text-gray-900 px-4 pt-4 pb-2">
            Transcript
          </h2>
          <TranscriptPanel
            segments={segments}
            activeSegmentId={activeSegmentId}
            onSegmentClick={handleSegmentClick}
          />
        </div>
      </div>
    </div>
  )
}

export default VideoPage
