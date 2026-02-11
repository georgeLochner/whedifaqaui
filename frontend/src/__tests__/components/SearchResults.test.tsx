/**
 * SearchResults component tests.
 *
 * S3-F01  test_search_result_shows_timestamp
 * S3-F02  test_search_result_link_navigates
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import SearchResults from '../../components/search/SearchResults'
import type { SearchResult } from '../../types/search'

const sampleResults: SearchResult[] = [
  {
    video_id: '11111111-1111-1111-1111-111111111111',
    video_title: 'Authentication Review',
    segment_id: 'seg-001',
    start_time: 83,
    end_time: 95,
    text: 'We discussed the OAuth token flow.',
    speaker: 'SPEAKER_00',
    score: 0.92,
    highlights: [],
    timestamp_formatted: '1:23',
  },
  {
    video_id: '22222222-2222-2222-2222-222222222222',
    video_title: 'Database Migration',
    segment_id: 'seg-002',
    start_time: 245,
    end_time: 260,
    text: 'The migration plan covers three phases.',
    speaker: null,
    score: 0.85,
    highlights: [],
    timestamp_formatted: '4:05',
  },
]

function renderResults(results: SearchResult[] = sampleResults) {
  return render(
    <MemoryRouter>
      <SearchResults results={results} />
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// S3-F01: Formatted timestamp visible in result
// ---------------------------------------------------------------------------

describe('S3-F01: Search result shows timestamp', () => {
  it('displays "at 1:23" for the first result', () => {
    renderResults()
    expect(screen.getByText('at 1:23')).toBeTruthy()
  })

  it('displays "at 4:05" for the second result', () => {
    renderResults()
    expect(screen.getByText('at 4:05')).toBeTruthy()
  })

  it('shows video title and text snippet', () => {
    renderResults()
    expect(screen.getByText('Authentication Review')).toBeTruthy()
    expect(
      screen.getByText('We discussed the OAuth token flow.')
    ).toBeTruthy()
  })

  it('shows speaker label when present', () => {
    renderResults()
    expect(screen.getByText('Speaker: SPEAKER_00')).toBeTruthy()
  })

  it('shows no-results message when results are empty', () => {
    renderResults([])
    expect(screen.getByTestId('no-results')).toBeTruthy()
    expect(
      screen.getByText('No results found. Try different search terms.')
    ).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// S3-F02: Link href points to /videos/{id}?t=
// ---------------------------------------------------------------------------

describe('S3-F02: Search result link navigates', () => {
  it('links to /videos/{video_id}?t={start_time}', () => {
    renderResults()
    const links = screen.getAllByTestId('timestamp-link')
    expect(links[0].getAttribute('href')).toBe(
      '/videos/11111111-1111-1111-1111-111111111111?t=83'
    )
    expect(links[1].getAttribute('href')).toBe(
      '/videos/22222222-2222-2222-2222-222222222222?t=245'
    )
  })
})
