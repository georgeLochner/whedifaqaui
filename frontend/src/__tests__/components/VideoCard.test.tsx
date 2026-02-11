/**
 * VideoCard component tests.
 *
 * M1-F02  test_video_card_displays_metadata
 * M1-F05  test_thumbnail_displayed
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import VideoCard from '../../components/library/VideoCard'
import type { Video } from '../../types/video'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => mockNavigate }
})

const sampleVideo: Video = {
  id: '11111111-1111-1111-1111-111111111111',
  title: 'Authentication Review',
  file_path: '/data/videos/original/test.mkv',
  processed_path: null,
  thumbnail_path: '/data/videos/thumbnails/test.jpg',
  duration: 300,
  recording_date: '2024-01-15',
  participants: ['Alice', 'Bob'],
  context_notes: null,
  status: 'ready',
  error_message: null,
  created_at: '2024-01-15T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
}

function renderCard(video: Video = sampleVideo) {
  return render(
    <MemoryRouter>
      <VideoCard video={video} />
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// M1-F02: VideoCard shows title, date, status
// ---------------------------------------------------------------------------

describe('M1-F02: VideoCard displays metadata', () => {
  it('shows video title', () => {
    renderCard()
    expect(screen.getByText('Authentication Review')).toBeTruthy()
  })

  it('shows recording date', () => {
    renderCard()
    expect(screen.getByText('2024-01-15')).toBeTruthy()
  })

  it('shows status badge', () => {
    renderCard()
    expect(screen.getByTestId('status-badge-ready')).toBeTruthy()
  })

  it('shows participant count', () => {
    renderCard()
    expect(screen.getByText('2 participants')).toBeTruthy()
  })

  it('navigates to video page on click', () => {
    renderCard()
    fireEvent.click(screen.getByTestId('video-card'))
    expect(mockNavigate).toHaveBeenCalledWith(
      '/videos/11111111-1111-1111-1111-111111111111'
    )
  })
})

// ---------------------------------------------------------------------------
// M1-F05: Thumbnail <img> rendered with correct src
// ---------------------------------------------------------------------------

describe('M1-F05: Thumbnail displayed', () => {
  it('renders an img element with thumbnail src', () => {
    renderCard()
    const img = screen.getByRole('img', { name: 'Authentication Review' })
    expect(img).toBeTruthy()
    expect(img.getAttribute('src')).toBe(
      '/api/videos/11111111-1111-1111-1111-111111111111/thumbnail'
    )
  })
})
