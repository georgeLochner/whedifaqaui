function UploadPage() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Upload Video</h1>
        <p className="text-gray-600 mb-8">
          Upload MKV recordings for transcription and indexing.
        </p>

        <div className="max-w-xl">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <p className="text-gray-500">
              Drag and drop MKV file here, or click to browse
            </p>
            <p className="mt-4 text-sm text-gray-400">
              Upload functionality will be implemented in Phase 1.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadPage
