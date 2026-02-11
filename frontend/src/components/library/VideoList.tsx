import { useState, useMemo } from 'react'
import type { Video } from '../../types/video'
import VideoCard from './VideoCard'

interface VideoListProps {
  videos: Video[]
}

const STATUS_OPTIONS = ['all', 'ready', 'processing', 'error'] as const

type SortOption = 'date' | 'title'

export default function VideoList({ videos }: VideoListProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<SortOption>('date')

  const filtered = useMemo(() => {
    let result = videos
    if (statusFilter !== 'all') {
      result = result.filter((v) => v.status === statusFilter)
    }
    result = [...result].sort((a, b) => {
      if (sortBy === 'title') {
        return a.title.localeCompare(b.title)
      }
      // date descending (newest first)
      const dateA = a.recording_date ?? ''
      const dateB = b.recording_date ?? ''
      return dateB.localeCompare(dateA)
    })
    return result
  }, [videos, statusFilter, sortBy])

  return (
    <div data-testid="video-list">
      <div className="flex items-center gap-4 mb-6">
        <div>
          <label htmlFor="status-filter" className="sr-only">
            Filter by status
          </label>
          <select
            id="status-filter"
            data-testid="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm border px-3 py-1.5"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'All statuses' : opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="sort-select" className="sr-only">
            Sort by
          </label>
          <select
            id="sort-select"
            data-testid="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm border px-3 py-1.5"
          >
            <option value="date">Date (newest)</option>
            <option value="title">Title (A–Z)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((video) => (
          <VideoCard key={video.id} video={video} />
        ))}
      </div>
    </div>
  )
}
