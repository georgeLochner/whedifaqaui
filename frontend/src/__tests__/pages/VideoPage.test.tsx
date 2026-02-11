/**
 * VideoPage integration tests.
 *
 * P2-F03  test_url_with_timestamp - URL includes ?t=seconds after segment click
 * P2-F04  test_url_timestamp_auto_seeks - Page load with ?t= passes initialTime to VideoPlayer
 */

import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// jsdom does not implement scrollIntoView
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

// ---------- Mocks ----------

const fakeVideo = {
  id: 'vid-001',
  title: 'Sprint Planning Meeting',
  file_path: '/data/videos/original/vid-001.mkv',
  processed_path: '/data/videos/processed/vid-001.mp4',
  thumbnail_path: null,
  duration: 3600,
  recording_date: '2024-06-15',
  participants: ['Alice', 'Bob'],
  context_notes: null,
  status: 'ready' as const,
  error_message: null,
  created_at: '2024-06-15T00:00:00Z',
  updated_at: '2024-06-15T00:00:00Z',
}

const fakeTranscript = {
  video_id: 'vid-001',
  segments: [
    {
      id: 'seg-1',
      start_time: 0,
      end_time: 15,
      text: 'Welcome to the meeting.',
      speaker: 'SPEAKER_00',
      timestamp_formatted: '0:00',
    },
    {
      id: 'seg-2',
      start_time: 15,
      end_time: 30,
      text: 'Let us review the backlog.',
      speaker: 'SPEAKER_01',
      timestamp_formatted: '0:15',
    },
  ],
  count: 2,
}

vi.mock('../../api/videos', () => ({
  getVideo: vi.fn(),
  getTranscript: vi.fn(),
  uploadVideo: vi.fn(),
  getVideoStatus: vi.fn(),
}))

// Track what props VideoPlayer receives
let capturedVideoPlayerProps: Record<string, unknown> = {}

vi.mock('../../components/video/VideoPlayer', () => ({
  default: (props: Record<string, unknown>) => {
    capturedVideoPlayerProps = props
    return <div data-testid="video-player">VideoPlayer mock</div>
  },
}))

vi.mock('video.js', () => ({ default: vi.fn() }))
vi.mock('video.js/dist/video-js.css', () => ({}))

import * as videosApi from '../../api/videos'
import VideoPage from '../../pages/VideoPage'

beforeEach(() => {
  vi.clearAllMocks()
  capturedVideoPlayerProps = {}
  vi.mocked(videosApi.getVideo).mockResolvedValue(fakeVideo)
  vi.mocked(videosApi.getTranscript).mockResolvedValue(fakeTranscript)
})

function renderWithRouter(initialEntry = '/videos/vid-001') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <VideoPage />
    </MemoryRouter>
  )
}

// We need to use Routes to provide :id param
import { Routes, Route } from 'react-router-dom'

function renderWithRoutes(initialEntry = '/videos/vid-001') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/videos/:id" element={<VideoPage />} />
      </Routes>
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// Basic rendering
// ---------------------------------------------------------------------------

describe('VideoPage renders', () => {
  it('displays loading state initially', () => {
    // Never resolve the promises to keep loading
    vi.mocked(videosApi.getVideo).mockReturnValue(new Promise(() => {}))
    vi.mocked(videosApi.getTranscript).mockReturnValue(new Promise(() => {}))

    renderWithRoutes()
    expect(screen.getByTestId('video-page-loading')).toBeInTheDocument()
  })

  it('displays video title and transcript after loading', async () => {
    renderWithRoutes()

    await waitFor(() => {
      expect(screen.getByTestId('video-page')).toBeInTheDocument()
    })

    expect(screen.getByText('Sprint Planning Meeting')).toBeInTheDocument()
    expect(screen.getByTestId('video-player')).toBeInTheDocument()
    expect(screen.getByTestId('transcript-panel')).toBeInTheDocument()
  })

  it('displays error state when API fails', async () => {
    vi.mocked(videosApi.getVideo).mockRejectedValue(new Error('Not found'))

    renderWithRoutes()

    await waitFor(() => {
      expect(screen.getByTestId('video-page-error')).toBeInTheDocument()
    })
  })
})

// ---------------------------------------------------------------------------
// P2-F03: URL with timestamp - clicking segment updates URL ?t=
// ---------------------------------------------------------------------------

describe('P2-F03: URL with timestamp', () => {
  it('updates URL with ?t=seconds when transcript segment is clicked', async () => {
    renderWithRoutes()

    await waitFor(() => {
      expect(screen.getByTestId('video-page')).toBeInTheDocument()
    })

    const segments = screen.getAllByTestId('transcript-segment')
    fireEvent.click(segments[1]) // Click second segment (start_time=15)

    // The URL should now contain t=15 - we can verify via the rendered VideoPlayer
    // getting the right initialTime on next render, but more directly we check
    // that setSearchParams was called by verifying the component re-renders
    // with the correct search param reflected
    await waitFor(() => {
      // After clicking, the VideoPlayer should receive initialTime=15
      expect(capturedVideoPlayerProps.initialTime).toBe(15)
    })
  })
})

// ---------------------------------------------------------------------------
// P2-F04: URL timestamp auto-seeks
// ---------------------------------------------------------------------------

describe('P2-F04: URL timestamp auto-seeks', () => {
  it('passes initialTime to VideoPlayer when ?t= is in URL', async () => {
    renderWithRoutes('/videos/vid-001?t=125')

    await waitFor(() => {
      expect(screen.getByTestId('video-page')).toBeInTheDocument()
    })

    expect(capturedVideoPlayerProps.initialTime).toBe(125)
  })

  it('does not pass initialTime when ?t= is absent', async () => {
    renderWithRoutes('/videos/vid-001')

    await waitFor(() => {
      expect(screen.getByTestId('video-page')).toBeInTheDocument()
    })

    expect(capturedVideoPlayerProps.initialTime).toBeUndefined()
  })
})
