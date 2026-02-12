import type { DocumentDetail } from '../../types/document'

interface DocumentViewerProps {
  document: DocumentDetail
  onDownload: () => void
}

function markdownToHtml(markdown: string): string {
  let html = markdown
    // Code blocks (``` ... ```)
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    // Headings
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold and italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Line breaks to paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')

  // Wrap loose list items
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  // Remove duplicate nested <ul> tags
  html = html.replace(/<\/ul>\s*<ul>/g, '')

  return `<p>${html}</p>`
}

export default function DocumentViewer({ document, onDownload }: DocumentViewerProps) {
  const contentHtml = markdownToHtml(document.content)

  return (
    <div data-testid="document-viewer" className="flex flex-col h-full p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{document.title}</h3>
      <div
        data-testid="document-content"
        className="flex-1 prose prose-sm max-w-none overflow-y-auto"
        dangerouslySetInnerHTML={{ __html: contentHtml }}
      />
      <div className="pt-4 border-t border-gray-200">
        <button
          data-testid="document-download"
          type="button"
          onClick={onDownload}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
        >
          Download
        </button>
      </div>
    </div>
  )
}
