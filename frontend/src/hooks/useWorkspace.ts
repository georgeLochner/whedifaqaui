import { useCallback, useState } from 'react'
import type { Citation } from '../types/chat'

export interface ResultItem {
  id: string
  type: 'video' | 'document'
  videoId?: string
  videoTitle?: string
  timestamp?: number
  text?: string
  documentId?: string
  documentTitle?: string
  recordingDate?: string
}

export interface UseWorkspaceReturn {
  results: ResultItem[]
  selectedResult: ResultItem | null
  addResult: (citation: Citation) => void
  addResults: (citations: Citation[]) => void
  selectResult: (result: ResultItem) => void
}

function citationToResultItem(citation: Citation): ResultItem {
  return {
    id: `${citation.video_id}-${Math.floor(citation.timestamp)}`,
    type: 'video',
    videoId: citation.video_id,
    videoTitle: citation.video_title,
    timestamp: citation.timestamp,
    text: citation.text,
  }
}

export function useWorkspace(): UseWorkspaceReturn {
  const [results, setResults] = useState<ResultItem[]>([])
  const [selectedResult, setSelectedResult] = useState<ResultItem | null>(null)

  const addResult = useCallback((citation: Citation) => {
    const item = citationToResultItem(citation)
    setResults((prev) => {
      if (prev.some((r) => r.id === item.id)) {
        return prev
      }
      return [...prev, item]
    })
  }, [])

  const addResults = useCallback((citations: Citation[]) => {
    const newItems = citations.map(citationToResultItem)
    setResults((prev) => {
      const existingIds = new Set(prev.map((r) => r.id))
      const unique: ResultItem[] = []
      for (const item of newItems) {
        if (!existingIds.has(item.id)) {
          existingIds.add(item.id)
          unique.push(item)
        }
      }
      return unique.length > 0 ? [...prev, ...unique] : prev
    })
  }, [])

  const selectResult = useCallback((result: ResultItem) => {
    setSelectedResult(result)
  }, [])

  return { results, selectedResult, addResult, addResults, selectResult }
}
