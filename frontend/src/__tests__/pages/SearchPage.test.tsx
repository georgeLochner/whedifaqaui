/**
 * SearchPage tests.
 *
 * S1-F03  test_search_loading_state
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../../api/search', () => ({
  searchVideos: vi.fn(),
}))

import * as searchApi from '../../api/search'
import SearchPage from '../../pages/SearchPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// S1-F03: Loading spinner shown during API call
// ---------------------------------------------------------------------------

describe('S1-F03: Search loading state', () => {
  it('shows loading spinner while search is in progress', async () => {
    // Make searchVideos hang so we can observe loading state
    vi.mocked(searchApi.searchVideos).mockReturnValue(new Promise(() => {}))

    renderPage()

    // Type a query and submit
    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'test query' } })
    fireEvent.submit(input.closest('form')!)

    // Loading spinner should appear
    expect(screen.getByTestId('search-loading')).toBeTruthy()
  })

  it('hides loading spinner and shows results after search completes', async () => {
    vi.mocked(searchApi.searchVideos).mockResolvedValue({
      count: 1,
      results: [
        {
          video_id: 'aaa',
          video_title: 'Test Video',
          segment_id: 'seg-1',
          start_time: 10,
          end_time: 20,
          text: 'Some text',
          speaker: null,
          score: 0.9,
          highlights: [],
          timestamp_formatted: '0:10',
        },
      ],
    })

    renderPage()

    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'test query' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.queryByTestId('search-loading')).toBeNull()
    })

    expect(screen.getByTestId('search-result')).toBeTruthy()
    expect(screen.getByText('Test Video')).toBeTruthy()
  })

  it('shows no-results message when search returns empty', async () => {
    vi.mocked(searchApi.searchVideos).mockResolvedValue({
      count: 0,
      results: [],
    })

    renderPage()

    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'nonexistent xyz' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByTestId('no-results')).toBeTruthy()
    })
  })
})
