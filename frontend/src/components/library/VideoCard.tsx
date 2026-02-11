import { useNavigate } from 'react-router-dom'
import type { Video } from '../../types/video'
import StatusBadge from '../common/StatusBadge'

interface VideoCardProps {
  video: Video
}

export default function VideoCard({ video }: VideoCardProps) {
  const navigate = useNavigate()

  return (
    <div
      data-testid="video-card"
      className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
      onClick={() => navigate(`/videos/${video.id}`)}
    >
      <div className="aspect-video bg-gray-200 relative">
        <img
          src={`/api/videos/${video.id}/thumbnail`}
          alt={video.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>
      <div className="p-4">
        <h3 className="text-sm font-semibold text-gray-900 truncate">
          {video.title}
        </h3>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            {video.recording_date ?? '—'}
          </span>
          <StatusBadge status={video.status} />
        </div>
        {video.participants.length > 0 && (
          <p className="mt-1 text-xs text-gray-500">
            {video.participants.length} participant
            {video.participants.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>
    </div>
  )
}
