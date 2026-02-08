import type { Video } from '../../types/video'

type VideoStatus = Video['status']

const STATUS_STYLES: Record<VideoStatus, string> = {
  uploaded: 'bg-gray-100 text-gray-700',
  processing: 'bg-yellow-100 text-yellow-800',
  transcribing: 'bg-blue-100 text-blue-800',
  chunking: 'bg-blue-100 text-blue-800',
  indexing: 'bg-blue-100 text-blue-800',
  ready: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
}

interface StatusBadgeProps {
  status: VideoStatus
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-700'

  return (
    <span
      data-testid={`status-badge-${status}`}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {status}
    </span>
  )
}
