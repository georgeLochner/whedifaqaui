interface DocumentCardProps {
  title: string
  preview: string
  onClick: () => void
}

export default function DocumentCard({ title, preview, onClick }: DocumentCardProps) {
  return (
    <button
      data-testid="result-item-document"
      type="button"
      onClick={onClick}
      className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 text-gray-400" aria-label="document icon">&#128196;</span>
        <div className="min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">{title}</div>
          <div data-testid="document-preview" className="text-xs text-gray-500 mt-0.5 truncate">
            {preview.length > 100 ? preview.slice(0, 100) + '...' : preview}
          </div>
        </div>
      </div>
    </button>
  )
}
