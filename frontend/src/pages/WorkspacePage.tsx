import { useCallback } from 'react'
import type { Citation } from '../types/chat'
import ConversationPanel from '../components/workspace/ConversationPanel'

export default function WorkspacePage() {
  const handleCitationClick = useCallback((_citation: Citation) => {
    // Will be implemented when ResultsPanel is built (w-dnx)
  }, [])

  return (
    <div
      className="h-[calc(100vh-4rem)] grid grid-cols-[30%_25%_45%] -mx-4 sm:-mx-6 lg:-mx-8 -my-6"
      data-testid="workspace-layout"
    >
      <ConversationPanel onCitationClick={handleCitationClick} />
      <div data-testid="results-panel" className="border-l border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-700">Results</h2>
      </div>
      <div data-testid="content-pane" className="border-l border-gray-200 p-4">
        <p className="text-gray-500">Select a result to view content</p>
      </div>
    </div>
  )
}
