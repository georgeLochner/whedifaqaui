import { Link } from 'react-router-dom'
import type { SearchResult } from '../../types/search'
import { formatTimestamp } from '../../utils/timestamp'

interface SearchResultsProps {
  results: SearchResult[]
}

export default function SearchResults({ results }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <div data-testid="no-results" className="text-center py-8">
        <p className="text-gray-500">
          No results found. Try different search terms.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <div
          key={result.segment_id}
          data-testid="search-result"
          className="bg-white rounded-lg shadow p-4"
        >
          <div className="flex items-start justify-between">
            <h3 className="font-semibold text-gray-900">
              {result.video_title}
            </h3>
            <Link
              to={`/videos/${result.video_id}?t=${result.start_time}`}
              data-testid="timestamp-link"
              className="text-blue-600 hover:text-blue-800 hover:underline font-mono text-sm whitespace-nowrap ml-4"
            >
              at {formatTimestamp(result.start_time)}
            </Link>
          </div>
          <p className="mt-1 text-sm text-gray-700">{result.text}</p>
          {result.speaker && (
            <p className="mt-1 text-xs text-gray-500">
              Speaker: {result.speaker}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
