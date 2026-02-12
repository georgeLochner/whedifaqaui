import { useCallback } from 'react'
import type { Citation } from '../types/chat'
import { useWorkspace } from '../hooks/useWorkspace'
import ConversationPanel from '../components/workspace/ConversationPanel'
import ResultsPanel from '../components/workspace/ResultsPanel'
import ContentPane from '../components/workspace/ContentPane'

export default function WorkspacePage() {
  const { results, selectedResult, addResults, addDocumentResult, selectResult } = useWorkspace()

  const handleCitationClick = useCallback(
    (citation: Citation) => {
      addResults([citation])
      selectResult({
        id: `${citation.video_id}-${Math.floor(citation.timestamp)}`,
        type: 'video',
        videoId: citation.video_id,
        videoTitle: citation.video_title,
        timestamp: citation.timestamp,
        text: citation.text,
      })
    },
    [addResults, selectResult]
  )

  const handleCitationsReceived = useCallback(
    (citations: Citation[]) => {
      addResults(citations)
    },
    [addResults]
  )

  const handleDocumentGenerated = useCallback(
    (doc: { id: string; title: string }) => {
      addDocumentResult(doc)
    },
    [addDocumentResult]
  )

  return (
    <div
      className="h-[calc(100vh-4rem)] grid grid-cols-[30%_25%_45%] -mx-4 sm:-mx-6 lg:-mx-8 -my-6"
      data-testid="workspace-layout"
    >
      <ConversationPanel
        onCitationClick={handleCitationClick}
        onCitationsReceived={handleCitationsReceived}
        onDocumentGenerated={handleDocumentGenerated}
      />
      <ResultsPanel
        results={results}
        selectedResult={selectedResult}
        onResultClick={selectResult}
      />
      <ContentPane selectedResult={selectedResult} />
    </div>
  )
}
