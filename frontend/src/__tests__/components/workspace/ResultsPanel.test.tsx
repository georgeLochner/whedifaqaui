/**
 * ResultsPanel component tests.
 *
 * S8-F01  test_results_panel_renders — Panel visible with heading
 * S8-F02  test_results_list_scrollable — Scrollbar on overflow
 * S8-F03  test_result_item_clickable — onClick callback triggered
 * S8-F04  test_result_shows_video_info — "Video Title @ MM:SS" displayed
 * S8-F05  test_result_shows_document_info — Document title with icon
 * S8-F08  test_selected_result_highlighted — CSS class 'selected' applied
 * V4-F02  test_date_displayed_in_results — Recording date visible
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ResultsPanel from '../../../components/workspace/ResultsPanel'
import type { ResultItem } from '../../../hooks/useWorkspace'

const videoResult: ResultItem = {
  id: 'vid-1-348',
  type: 'video',
  videoId: 'vid-1',
  videoTitle: 'Backdrop CMS Weekly Meeting',
  timestamp: 348.6,
  text: 'permissions filter',
  recordingDate: '2023-01-05',
}

const documentResult: ResultItem = {
  id: 'doc-1',
  type: 'document',
  documentId: 'doc-1',
  documentTitle: 'Summary.md',
}

// ---------------------------------------------------------------------------
// S8-F01: Panel renders with heading
// ---------------------------------------------------------------------------

describe('S8-F01: ResultsPanel renders', () => {
  it('renders panel with heading', () => {
    render(
      <ResultsPanel results={[]} selectedResult={null} onResultClick={() => {}} />
    )

    const panel = screen.getByTestId('results-panel')
    expect(panel).toBeTruthy()
    expect(screen.getByText('Results')).toBeTruthy()
  })

  it('shows empty state when no results', () => {
    render(
      <ResultsPanel results={[]} selectedResult={null} onResultClick={() => {}} />
    )

    expect(screen.getByTestId('results-empty')).toBeTruthy()
  })

  it('shows count badge when results exist', () => {
    render(
      <ResultsPanel results={[videoResult]} selectedResult={null} onResultClick={() => {}} />
    )

    expect(screen.getByTestId('results-count').textContent).toBe('1')
  })
})

// ---------------------------------------------------------------------------
// S8-F02: Results list scrollable
// ---------------------------------------------------------------------------

describe('S8-F02: Results list scrollable', () => {
  it('has overflow-y-auto class for scrolling', () => {
    render(
      <ResultsPanel results={[videoResult]} selectedResult={null} onResultClick={() => {}} />
    )

    const panel = screen.getByTestId('results-panel')
    expect(panel.className).toContain('overflow-y-auto')
  })
})

// ---------------------------------------------------------------------------
// S8-F03: Result item clickable
// ---------------------------------------------------------------------------

describe('S8-F03: Result item clickable', () => {
  it('triggers onResultClick when clicked', () => {
    const onResultClick = vi.fn()

    render(
      <ResultsPanel results={[videoResult]} selectedResult={null} onResultClick={onResultClick} />
    )

    fireEvent.click(screen.getByTestId('result-item-video'))
    expect(onResultClick).toHaveBeenCalledOnce()
    expect(onResultClick).toHaveBeenCalledWith(videoResult)
  })
})

// ---------------------------------------------------------------------------
// S8-F04: Video result shows title and timestamp
// ---------------------------------------------------------------------------

describe('S8-F04: Video result shows video info', () => {
  it('displays "Video Title @ MM:SS" format', () => {
    render(
      <ResultsPanel results={[videoResult]} selectedResult={null} onResultClick={() => {}} />
    )

    const item = screen.getByTestId('result-item-video')
    expect(item.textContent).toContain('Backdrop CMS Weekly Meeting')
    expect(item.textContent).toContain('5:48')
  })
})

// ---------------------------------------------------------------------------
// S8-F05: Document result shows title with icon
// ---------------------------------------------------------------------------

describe('S8-F05: Document result shows document info', () => {
  it('displays document title with document icon', () => {
    render(
      <ResultsPanel results={[documentResult]} selectedResult={null} onResultClick={() => {}} />
    )

    const item = screen.getByTestId('result-item-document')
    expect(item.textContent).toContain('Summary.md')
    expect(item.querySelector('[aria-label="document icon"]')).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// S8-F08: Selected result highlighted
// ---------------------------------------------------------------------------

describe('S8-F08: Selected result highlighted', () => {
  it('applies selected class to the active result', () => {
    render(
      <ResultsPanel results={[videoResult]} selectedResult={videoResult} onResultClick={() => {}} />
    )

    const item = screen.getByTestId('result-item-video')
    expect(item.className).toContain('selected')
  })

  it('does not apply selected class to non-selected results', () => {
    const otherResult: ResultItem = { ...videoResult, id: 'vid-2-100', videoId: 'vid-2', timestamp: 100 }

    render(
      <ResultsPanel results={[videoResult, otherResult]} selectedResult={otherResult} onResultClick={() => {}} />
    )

    const items = screen.getAllByTestId('result-item-video')
    expect(items[0].className).not.toContain('selected')
    expect(items[1].className).toContain('selected')
  })
})

// ---------------------------------------------------------------------------
// V4-F02: Recording date visible in result item
// ---------------------------------------------------------------------------

describe('V4-F02: Recording date displayed in results', () => {
  it('shows recording date for video results', () => {
    render(
      <ResultsPanel results={[videoResult]} selectedResult={null} onResultClick={() => {}} />
    )

    expect(screen.getByTestId('result-recording-date').textContent).toBe('2023-01-05')
  })

  it('does not show recording date when not provided', () => {
    const resultWithoutDate: ResultItem = { ...videoResult, recordingDate: undefined }

    render(
      <ResultsPanel results={[resultWithoutDate]} selectedResult={null} onResultClick={() => {}} />
    )

    expect(screen.queryByTestId('result-recording-date')).toBeNull()
  })
})
