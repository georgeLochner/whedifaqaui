import type { ResultItem } from '../../hooks/useWorkspace'
import { formatTimestamp } from '../../utils/timestamp'

interface ResultsPanelProps {
  results: ResultItem[]
  selectedResult: ResultItem | null
  onResultClick: (result: ResultItem) => void
}

export default function ResultsPanel({ results, selectedResult, onResultClick }: ResultsPanelProps) {
  return (
    <div data-testid="results-panel" className="flex flex-col h-full overflow-y-auto border-l border-gray-200">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-700">Results</h2>
        {results.length > 0 && (
          <span data-testid="results-count" className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
            {results.length}
          </span>
        )}
      </div>

      {results.length === 0 ? (
        <div data-testid="results-empty" className="px-4 py-8 text-center text-gray-400 text-sm">
          No results yet. Ask a question to get started.
        </div>
      ) : (
        <ul className="divide-y divide-gray-100">
          {results.map((result) => (
            <li key={result.id}>
              <button
                data-testid={result.type === 'video' ? 'result-item-video' : 'result-item-document'}
                type="button"
                onClick={() => onResultClick(result)}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                  selectedResult?.id === result.id ? 'selected bg-blue-50' : ''
                }`}
              >
                {result.type === 'video' ? (
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 text-gray-400" aria-label="video icon">&#9654;</span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {result.videoTitle} @ {formatTimestamp(result.timestamp ?? 0)}
                      </div>
                      {result.recordingDate && (
                        <div data-testid="result-recording-date" className="text-xs text-gray-500 mt-0.5">
                          {result.recordingDate}
                        </div>
                      )}
                      {result.text && (
                        <div className="text-xs text-gray-500 mt-0.5 truncate">{result.text}</div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 text-gray-400" aria-label="document icon">&#128196;</span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {result.documentTitle}
                      </div>
                    </div>
                  </div>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
