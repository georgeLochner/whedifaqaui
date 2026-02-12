import { useCallback, useEffect, useState } from 'react'
import type { Citation } from '../types/chat'

const STORAGE_KEY = 'workspace-results'

function loadResults(): ResultItem[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

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
  addDocumentResult: (doc: { id: string; title: string }) => void
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
  const [results, setResults] = useState<ResultItem[]>(loadResults)
  const [selectedResult, setSelectedResult] = useState<ResultItem | null>(null)

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(results))
  }, [results])

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

  const addDocumentResult = useCallback((doc: { id: string; title: string }) => {
    const item: ResultItem = {
      id: doc.id,
      type: 'document',
      documentId: doc.id,
      documentTitle: doc.title,
    }
    setResults((prev) => {
      if (prev.some((r) => r.id === item.id)) return prev
      return [...prev, item]
    })
  }, [])

  const selectResult = useCallback((result: ResultItem) => {
    setSelectedResult(result)
  }, [])

  return { results, selectedResult, addResult, addResults, addDocumentResult, selectResult }
}
