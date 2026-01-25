import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface HealthStatus {
  status: string
  services: {
    postgres: string
    opensearch: string
    redis: string
  }
}

function HomePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiClient.getHealth()
      .then(setHealth)
      .catch(err => setError(err.message))
  }, [])

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Video Knowledge Management System
        </h1>
        <p className="text-gray-600 mb-8">
          Upload technical meeting recordings, search by natural language, and find exactly what was discussed.
        </p>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">System Status</h2>
          {error ? (
            <p className="text-red-600">Error: {error}</p>
          ) : health ? (
            <div className="space-y-2">
              <p className="flex items-center">
                <span className={`inline-block w-3 h-3 rounded-full mr-2 ${health.status === 'ok' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                <span className="font-medium">Overall:</span>
                <span className="ml-2">{health.status}</span>
              </p>
              <ul className="ml-5 space-y-1 text-sm text-gray-600">
                <li>PostgreSQL: {health.services.postgres}</li>
                <li>OpenSearch: {health.services.opensearch}</li>
                <li>Redis: {health.services.redis}</li>
              </ul>
            </div>
          ) : (
            <p className="text-gray-500">Loading...</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default HomePage
