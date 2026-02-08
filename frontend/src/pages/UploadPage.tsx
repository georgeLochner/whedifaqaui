import { useState, useEffect, useRef } from 'react'
import UploadForm, { type UploadFormData } from '../components/upload/UploadForm'
import UploadProgress from '../components/upload/UploadProgress'
import StatusBadge from '../components/common/StatusBadge'
import { uploadVideo, getVideoStatus } from '../api/videos'
import type { Video } from '../types/video'

const POLL_INTERVAL_MS = 5000

function UploadPage() {
  const [progress, setProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedVideo, setUploadedVideo] = useState<Video | null>(null)
  const [currentStatus, setCurrentStatus] = useState<Video['status'] | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  function startPolling(videoId: string) {
    pollRef.current = setInterval(async () => {
      try {
        const statusResp = await getVideoStatus(videoId)
        setCurrentStatus(statusResp.status)
        if (statusResp.error_message) {
          setErrorMessage(statusResp.error_message)
        }
        if (statusResp.status === 'ready' || statusResp.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current)
        }
      } catch {
        // Polling failure is non-fatal; we'll retry on next tick
      }
    }, POLL_INTERVAL_MS)
  }

  async function handleSubmit(data: UploadFormData) {
    setIsUploading(true)
    setProgress(0)
    setUploadError(null)
    setUploadedVideo(null)
    setCurrentStatus(null)
    setErrorMessage(null)

    try {
      const video = await uploadVideo(
        data.file,
        {
          title: data.title,
          recording_date: data.recording_date,
          participants: data.participants,
          context_notes: data.context_notes,
        },
        (pct) => setProgress(pct)
      )
      setUploadedVideo(video)
      setCurrentStatus(video.status)
      startPolling(video.id)
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Upload failed. Please try again.'
      setUploadError(message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Video</h1>
      <p className="text-gray-600 mb-8">
        Upload MKV recordings for transcription and indexing.
      </p>

      <UploadForm onSubmit={handleSubmit} disabled={isUploading} />

      <UploadProgress progress={progress} isUploading={isUploading} />

      {uploadError && (
        <div className="mt-4 max-w-xl rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{uploadError}</p>
        </div>
      )}

      {uploadedVideo && currentStatus && (
        <div className="mt-6 max-w-xl rounded-md bg-white shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">
                {uploadedVideo.title}
              </p>
              <p className="text-sm text-gray-500">ID: {uploadedVideo.id}</p>
            </div>
            <StatusBadge status={currentStatus} />
          </div>
          {errorMessage && (
            <p className="mt-2 text-sm text-red-600">{errorMessage}</p>
          )}
          {currentStatus === 'ready' && (
            <p data-testid="success-message" className="mt-2 text-sm text-green-600">
              Processing complete! Your video is ready.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default UploadPage
