/**
 * VideoPlayer component tests.
 *
 * P1-F01  test_video_player_renders - video element present
 * P1-F02  test_player_controls_visible - Video.js controls enabled
 * P1-F03  test_player_loads_source - source set to /api/videos/{id}/stream
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// Track videojs calls
const mockReady = vi.fn()
const mockOn = vi.fn()
const mockDispose = vi.fn()
const mockCurrentTime = vi.fn()
let capturedOptions: Record<string, unknown> | null = null

const mockPlayer = {
  ready: mockReady,
  on: mockOn,
  dispose: mockDispose,
  currentTime: mockCurrentTime,
  isDisposed: vi.fn().mockReturnValue(false),
}

vi.mock('video.js', () => ({
  default: (el: HTMLVideoElement, options: Record<string, unknown>) => {
    capturedOptions = options
    return mockPlayer
  },
}))

vi.mock('video.js/dist/video-js.css', () => ({}))

import VideoPlayer from '../../components/video/VideoPlayer'

beforeEach(() => {
  capturedOptions = null
  vi.clearAllMocks()
})

describe('P1-F01: VideoPlayer renders', () => {
  it('renders a video element with data-testid', () => {
    render(<VideoPlayer videoId="test-123" />)
    const video = screen.getByTestId('video-player')
    expect(video).toBeInTheDocument()
    expect(video.tagName).toBe('VIDEO-JS')
  })
})

describe('P1-F02: Player controls visible', () => {
  it('initializes Video.js with controls: true', () => {
    render(<VideoPlayer videoId="test-123" />)
    expect(capturedOptions).toBeTruthy()
    expect(capturedOptions!.controls).toBe(true)
  })
})

describe('P1-F03: Player loads source', () => {
  it('sets video source to /api/videos/{id}/stream', () => {
    render(<VideoPlayer videoId="abc-456" />)
    expect(capturedOptions).toBeTruthy()
    const sources = capturedOptions!.sources as Array<{ src: string; type: string }>
    expect(sources).toHaveLength(1)
    expect(sources[0].src).toBe('/api/videos/abc-456/stream')
    expect(sources[0].type).toBe('video/mp4')
  })
})
