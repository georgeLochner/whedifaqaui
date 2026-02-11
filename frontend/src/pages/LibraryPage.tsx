import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getVideos } from '../api/videos'
import type { Video } from '../types/video'
import VideoList from '../components/library/VideoList'

export default function LibraryPage() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getVideos()
      .then((res) => {
        setVideos(res.videos)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message ?? 'Failed to load videos')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div data-testid="library-loading" className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div data-testid="library-error" className="px-4 py-6">
        <p className="text-red-600">Error: {error}</p>
      </div>
    )
  }

  return (
    <div data-testid="library-page" className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Video Library</h1>

      {videos.length === 0 ? (
        <div
          data-testid="library-empty"
          className="border-4 border-dashed border-gray-200 rounded-lg p-12 text-center"
        >
          <p className="text-gray-500 mb-4">No videos yet.</p>
          <Link
            to="/upload"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Upload your first video
          </Link>
        </div>
      ) : (
        <VideoList videos={videos} />
      )}
    </div>
  )
}
