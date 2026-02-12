/**
 * useWorkspace hook tests.
 *
 * S8-F06  test_results_accumulate — Count increases after chat
 * S8-F07  test_results_persist_during_session — Results survive re-renders
 */

import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWorkspace } from '../../hooks/useWorkspace'
import type { Citation } from '../../types/chat'

const makeCitation = (overrides: Partial<Citation> = {}): Citation => ({
  video_id: 'vid-1',
  video_title: 'Backdrop CMS Weekly Meeting',
  timestamp: 348.6,
  text: 'permissions filter',
  ...overrides,
})

describe('useWorkspace hook', () => {
  it('initializes with empty results and null selectedResult', () => {
    const { result } = renderHook(() => useWorkspace())

    expect(result.current.results).toEqual([])
    expect(result.current.selectedResult).toBeNull()
  })

  it('addResult converts Citation to ResultItem correctly', () => {
    const { result } = renderHook(() => useWorkspace())
    const citation = makeCitation()

    act(() => {
      result.current.addResult(citation)
    })

    const item = result.current.results[0]
    expect(item.id).toBe('vid-1-348')
    expect(item.type).toBe('video')
    expect(item.videoId).toBe('vid-1')
    expect(item.videoTitle).toBe('Backdrop CMS Weekly Meeting')
    expect(item.timestamp).toBe(348.6)
    expect(item.text).toBe('permissions filter')
  })

  it('addResult adds to results array (S8-F06)', () => {
    const { result } = renderHook(() => useWorkspace())

    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-1', timestamp: 100 }))
    })
    expect(result.current.results).toHaveLength(1)

    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-1', timestamp: 200 }))
    })
    expect(result.current.results).toHaveLength(2)

    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-2', timestamp: 100 }))
    })
    expect(result.current.results).toHaveLength(3)
  })

  it('addResult deduplicates by video_id + timestamp', () => {
    const { result } = renderHook(() => useWorkspace())

    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-1', timestamp: 348.6 }))
    })
    expect(result.current.results).toHaveLength(1)

    // Same video_id and same floor(timestamp) — should be deduplicated
    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-1', timestamp: 348.9 }))
    })
    expect(result.current.results).toHaveLength(1)
  })

  it('addResults adds multiple citations at once', () => {
    const { result } = renderHook(() => useWorkspace())

    act(() => {
      result.current.addResults([
        makeCitation({ video_id: 'vid-1', timestamp: 100 }),
        makeCitation({ video_id: 'vid-1', timestamp: 200 }),
        makeCitation({ video_id: 'vid-2', timestamp: 300 }),
      ])
    })

    expect(result.current.results).toHaveLength(3)
  })

  it('addResults deduplicates within batch and against existing', () => {
    const { result } = renderHook(() => useWorkspace())

    // Add one result first
    act(() => {
      result.current.addResult(makeCitation({ video_id: 'vid-1', timestamp: 100 }))
    })
    expect(result.current.results).toHaveLength(1)

    // Batch with a duplicate of the existing, a duplicate within batch, and a new one
    act(() => {
      result.current.addResults([
        makeCitation({ video_id: 'vid-1', timestamp: 100.5 }), // dup of existing (floor=100)
        makeCitation({ video_id: 'vid-2', timestamp: 200 }),    // new
        makeCitation({ video_id: 'vid-2', timestamp: 200.3 }),  // dup within batch (floor=200)
      ])
    })

    expect(result.current.results).toHaveLength(2)
    expect(result.current.results[0].id).toBe('vid-1-100')
    expect(result.current.results[1].id).toBe('vid-2-200')
  })

  it('selectResult sets selectedResult', () => {
    const { result } = renderHook(() => useWorkspace())

    act(() => {
      result.current.addResult(makeCitation())
    })

    act(() => {
      result.current.selectResult(result.current.results[0])
    })

    expect(result.current.selectedResult).not.toBeNull()
    expect(result.current.selectedResult!.id).toBe('vid-1-348')
  })

  it('results persist across re-renders (S8-F07)', () => {
    const { result, rerender } = renderHook(() => useWorkspace())

    act(() => {
      result.current.addResults([
        makeCitation({ video_id: 'vid-1', timestamp: 100 }),
        makeCitation({ video_id: 'vid-2', timestamp: 200 }),
      ])
    })
    expect(result.current.results).toHaveLength(2)

    // Re-render the hook (simulates component re-render)
    rerender()

    expect(result.current.results).toHaveLength(2)
    expect(result.current.results[0].videoId).toBe('vid-1')
    expect(result.current.results[1].videoId).toBe('vid-2')
  })
})
