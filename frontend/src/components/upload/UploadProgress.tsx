interface UploadProgressProps {
  progress: number
  isUploading: boolean
}

export default function UploadProgress({
  progress,
  isUploading,
}: UploadProgressProps) {
  if (!isUploading) return null

  return (
    <div data-testid="progress-bar" className="w-full max-w-xl mt-4">
      <div className="flex justify-between mb-1 text-sm text-gray-600">
        <span>Uploading…</span>
        <span>{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}
