/**
 * StatusBadge and status-polling tests.
 *
 * V3-F01  test_status_badge_colors
 * V3-F02  test_status_polling
 * V3-F03  test_ready_notification
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'

import StatusBadge from '../../components/common/StatusBadge'

// We import UploadPage for the polling test.  Mock the API and router
// so the page can mount in isolation.
vi.mock('../../api/videos', () => ({
  uploadVideo: vi.fn(),
  getVideoStatus: vi.fn(),
}))

vi.mock('react-router-dom', () => ({
  // UploadPage doesn't use router directly, but its parent (App) does.
  // Provide a no-op in case it's pulled in transitively.
  BrowserRouter: ({ children }: { children: React.ReactNode }) => children,
}))

import * as videosApi from '../../api/videos'

// ---------------------------------------------------------------------------
// V3-F01: Different CSS classes per status
// ---------------------------------------------------------------------------

describe('V3-F01: StatusBadge colors', () => {
  it('uploaded has gray styling', () => {
    render(<StatusBadge status="uploaded" />)
    const badge = screen.getByTestId('status-badge-uploaded')
    expect(badge.className).toContain('bg-gray-100')
  })

  it('processing has yellow styling', () => {
    render(<StatusBadge status="processing" />)
    const badge = screen.getByTestId('status-badge-processing')
    expect(badge.className).toContain('bg-yellow-100')
  })

  it('transcribing has blue styling', () => {
    render(<StatusBadge status="transcribing" />)
    const badge = screen.getByTestId('status-badge-transcribing')
    expect(badge.className).toContain('bg-blue-100')
  })

  it('ready has green styling', () => {
    render(<StatusBadge status="ready" />)
    const badge = screen.getByTestId('status-badge-ready')
    expect(badge.className).toContain('bg-green-100')
  })

  it('error has red styling', () => {
    render(<StatusBadge status="error" />)
    const badge = screen.getByTestId('status-badge-error')
    expect(badge.className).toContain('bg-red-100')
  })
})

// ---------------------------------------------------------------------------
// V3-F02: Status polling calls getVideoStatus at interval
// ---------------------------------------------------------------------------

describe('V3-F02: Status polling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('polls getVideoStatus after upload completes', async () => {
    // Lazy-import UploadPage so mocks are already in place
    const { default: UploadPage } = await import('../../pages/UploadPage')

    const fakeVideo = {
      id: 'abc-123',
      title: 'Test',
      file_path: '/data/videos/original/abc-123.mkv',
      processed_path: null,
      thumbnail_path: null,
      duration: null,
      recording_date: '2024-01-15',
      participants: [],
      context_notes: null,
      status: 'uploaded' as const,
      error_message: null,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }

    // uploadVideo resolves immediately
    vi.mocked(videosApi.uploadVideo).mockResolvedValue(fakeVideo)

    // getVideoStatus returns 'processing' on each call
    vi.mocked(videosApi.getVideoStatus).mockResolvedValue({
      id: 'abc-123',
      status: 'processing',
      error_message: null,
    })

    render(<UploadPage />)

    // Fill form fields and submit
    const { fireEvent } = await import('@testing-library/react')

    fireEvent.change(screen.getByTestId('title-input'), {
      target: { value: 'Test Video' },
    })
    fireEvent.change(screen.getByTestId('date-input'), {
      target: { value: '2024-01-15' },
    })

    // Simulate file selection
    const file = new File(['content'], 'test.mkv', {
      type: 'video/x-matroska',
    })
    const fileInput = screen.getByTestId('file-input')
    Object.defineProperty(fileInput, 'files', { value: [file] })
    fireEvent.change(fileInput)

    // Submit
    await act(async () => {
      fireEvent.click(screen.getByTestId('submit-btn'))
    })

    // Flush the uploadVideo promise microtask
    await act(async () => {
      await Promise.resolve()
    })

    // Advance past one poll interval (5000ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })

    expect(videosApi.getVideoStatus).toHaveBeenCalledWith('abc-123')

    // Advance another interval
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })

    expect(videosApi.getVideoStatus).toHaveBeenCalledTimes(2)
  })
})

// ---------------------------------------------------------------------------
// V3-F03: Ready status shows 'ready' text with green styling
// ---------------------------------------------------------------------------

describe('V3-F03: Ready notification', () => {
  it('displays "ready" with green styling', () => {
    render(<StatusBadge status="ready" />)
    const badge = screen.getByTestId('status-badge-ready')
    expect(badge).toHaveTextContent('ready')
    expect(badge.className).toContain('bg-green-100')
    expect(badge.className).toContain('text-green-800')
  })
})
