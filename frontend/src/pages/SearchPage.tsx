function SearchPage() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Search</h1>
        <p className="text-gray-600 mb-8">
          Search across all video transcripts using natural language.
        </p>

        <div className="max-w-2xl">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="What was discussed about..."
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2 border"
              disabled
            />
            <button
              className="bg-blue-600 text-white px-6 py-2 rounded-md opacity-50 cursor-not-allowed"
              disabled
            >
              Search
            </button>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            Search functionality will be implemented in Phase 2.
          </p>
        </div>
      </div>
    </div>
  )
}

export default SearchPage
