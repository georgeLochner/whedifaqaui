import { useParams } from 'react-router-dom'

function VideoPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Video Details</h1>
        <p className="text-gray-600 mb-8">
          Video ID: {id}
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-900 aspect-video rounded-lg flex items-center justify-center">
            <span className="text-gray-500">Video player placeholder</span>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Transcript</h2>
            <p className="text-gray-500 text-sm">
              Transcript viewer will be implemented in Phase 3.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VideoPage
