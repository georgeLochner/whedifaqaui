import { useState } from 'react'
import { searchVideos } from '../api/search'
import type { SearchResult } from '../types/search'
import SearchBar from '../components/search/SearchBar'
import SearchResults from '../components/search/SearchResults'

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  async function handleSearch(query: string) {
    setLoading(true)
    setError(null)
    try {
      const response = await searchVideos(query)
      setResults(response.results)
      setHasSearched(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Search</h1>
      <p className="text-gray-600 mb-6">
        Search across all video transcripts using natural language.
      </p>

      <SearchBar onSearch={handleSearch} />

      <div className="mt-8">
        {loading && (
          <div data-testid="search-loading" className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {error && (
          <div data-testid="search-error" className="py-4">
            <p className="text-red-600">Error: {error}</p>
          </div>
        )}

        {!loading && hasSearched && <SearchResults results={results} />}
      </div>
    </div>
  )
}
