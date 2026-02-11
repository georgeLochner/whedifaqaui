/**
 * VideoList component tests.
 *
 * M1-F03  test_filter_controls_present
 * M1-F04  test_sort_controls_present
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import VideoList from '../../components/library/VideoList'
import type { Video } from '../../types/video'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => vi.fn() }
})

const sampleVideos: Video[] = [
  {
    id: 'aaa',
    title: 'Video A',
    file_path: '/data/a.mkv',
    processed_path: null,
    thumbnail_path: null,
    duration: 60,
    recording_date: '2024-01-01',
    participants: [],
    context_notes: null,
    status: 'ready',
    error_message: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'bbb',
    title: 'Video B',
    file_path: '/data/b.mkv',
    processed_path: null,
    thumbnail_path: null,
    duration: 120,
    recording_date: '2024-02-01',
    participants: [],
    context_notes: null,
    status: 'processing',
    error_message: null,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-01T00:00:00Z',
  },
]

function renderList(videos: Video[] = sampleVideos) {
  return render(
    <MemoryRouter>
      <VideoList videos={videos} />
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// M1-F03: Status filter dropdown present
// ---------------------------------------------------------------------------

describe('M1-F03: Filter controls present', () => {
  it('renders the status filter dropdown', () => {
    renderList()
    const filter = screen.getByTestId('status-filter')
    expect(filter).toBeTruthy()
    expect(filter.tagName).toBe('SELECT')
  })

  it('has All, Ready, Processing, Error options', () => {
    renderList()
    const filter = screen.getByTestId('status-filter') as HTMLSelectElement
    const options = Array.from(filter.options).map((o) => o.value)
    expect(options).toContain('all')
    expect(options).toContain('ready')
    expect(options).toContain('processing')
    expect(options).toContain('error')
  })
})

// ---------------------------------------------------------------------------
// M1-F04: Sort controls present
// ---------------------------------------------------------------------------

describe('M1-F04: Sort controls present', () => {
  it('renders the sort dropdown', () => {
    renderList()
    const sortSelect = screen.getByTestId('sort-select')
    expect(sortSelect).toBeTruthy()
    expect(sortSelect.tagName).toBe('SELECT')
  })

  it('has Date and Title sort options', () => {
    renderList()
    const sortSelect = screen.getByTestId('sort-select') as HTMLSelectElement
    const options = Array.from(sortSelect.options).map((o) => o.value)
    expect(options).toContain('date')
    expect(options).toContain('title')
  })
})
