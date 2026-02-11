/**
 * LibraryPage tests.
 *
 * M1-F01  test_library_page_renders
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import type { Video } from '../../types/video'

// Mock the videos API
vi.mock('../../api/videos', () => ({
  getVideos: vi.fn(),
}))

// Mock useNavigate so VideoCard can mount
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => vi.fn() }
})

import * as videosApi from '../../api/videos'
import LibraryPage from '../../pages/LibraryPage'

const sampleVideos: Video[] = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    title: 'Authentication Review',
    file_path: '/data/a.mkv',
    processed_path: null,
    thumbnail_path: null,
    duration: 300,
    recording_date: '2024-01-15',
    participants: ['Alice', 'Bob'],
    context_notes: null,
    status: 'ready',
    error_message: null,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    title: 'Database Migration',
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

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <LibraryPage />
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// M1-F01: LibraryPage loads, video list displayed
// ---------------------------------------------------------------------------

describe('M1-F01: LibraryPage renders', () => {
  it('shows loading state initially', () => {
    vi.mocked(videosApi.getVideos).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByTestId('library-loading')).toBeTruthy()
  })

  it('renders video list after loading', async () => {
    vi.mocked(videosApi.getVideos).mockResolvedValue({
      videos: sampleVideos,
      total: 2,
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByTestId('library-page')).toBeTruthy()
    })

    expect(screen.getByTestId('video-list')).toBeTruthy()
    expect(screen.getByText('Authentication Review')).toBeTruthy()
    expect(screen.getByText('Database Migration')).toBeTruthy()
  })

  it('shows empty state when no videos', async () => {
    vi.mocked(videosApi.getVideos).mockResolvedValue({
      videos: [],
      total: 0,
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByTestId('library-empty')).toBeTruthy()
    })

    expect(screen.getByText('Upload your first video')).toBeTruthy()
  })

  it('shows error state on fetch failure', async () => {
    vi.mocked(videosApi.getVideos).mockRejectedValue(
      new Error('Network error')
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByTestId('library-error')).toBeTruthy()
    })

    expect(screen.getByText(/Network error/)).toBeTruthy()
  })
})
