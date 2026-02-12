/**
 * ContentPane component tests.
 *
 * S9-F01  test_content_pane_renders — Container visible
 * S9-F02  test_content_pane_empty_state — "Select a result" placeholder
 * S9-F03  test_content_pane_video_mode — VideoPlayer rendered
 * S9-F04  test_content_pane_document_mode — DocumentViewer rendered
 * S9-F05  test_video_seeks_to_timestamp — seekTo prop matches timestamp
 * S9-F06  test_transcript_syncs_with_video — TranscriptPanel rendered
 * S9-F07  test_document_download_button — Download button visible
 */

import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ContentPane from '../../../components/workspace/ContentPane'
import type { ResultItem } from '../../../hooks/useWorkspace'

// jsdom does not implement scrollIntoView
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

// ---------- Mocks ----------

const fakeTranscript = {
  video_id: 'vid-1',
  segments: [
    {
      id: 'seg-1',
      start_time: 300,
      end_time: 400,
      text: 'permissions filter discussion',
      speaker: 'SPEAKER_00',
      timestamp_formatted: '5:00',
    },
    {
      id: 'seg-2',
      start_time: 400,
      end_time: 500,
      text: 'role descriptions feature',
      speaker: 'SPEAKER_01',
      timestamp_formatted: '6:40',
    },
  ],
  count: 2,
}

vi.mock('../../../api/videos', () => ({
  getTranscript: vi.fn(),
}))

let capturedVideoPlayerProps: Record<string, unknown> = {}

vi.mock('../../../components/video/VideoPlayer', () => ({
  default: (props: Record<string, unknown>) => {
    capturedVideoPlayerProps = props
    return <div data-testid="video-player">VideoPlayer mock</div>
  },
}))

vi.mock('video.js', () => ({ default: vi.fn() }))
vi.mock('video.js/dist/video-js.css', () => ({}))

import * as videosApi from '../../../api/videos'

const videoResult: ResultItem = {
  id: 'vid-1-348',
  type: 'video',
  videoId: 'vid-1',
  videoTitle: 'Backdrop CMS Weekly Meeting',
  timestamp: 348.6,
  text: 'permissions filter',
}

const documentResult: ResultItem = {
  id: 'doc-1',
  type: 'document',
  documentId: 'doc-1',
  documentTitle: 'Summary.md',
}

beforeEach(() => {
  vi.clearAllMocks()
  capturedVideoPlayerProps = {}
  vi.mocked(videosApi.getTranscript).mockResolvedValue(fakeTranscript)
})

// ---------------------------------------------------------------------------
// S9-F01: ContentPane renders container
// ---------------------------------------------------------------------------

describe('S9-F01: ContentPane renders', () => {
  it('renders content-pane container', () => {
    render(<ContentPane selectedResult={null} />)
    expect(screen.getByTestId('content-pane')).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// S9-F02: Empty state shows placeholder
// ---------------------------------------------------------------------------

describe('S9-F02: Empty state', () => {
  it('shows "Select a result to view content" when no result selected', () => {
    render(<ContentPane selectedResult={null} />)
    expect(screen.getByTestId('content-pane-empty')).toBeTruthy()
    expect(screen.getByTestId('content-pane-empty').textContent).toContain(
      'Select a result to view'
    )
  })
})

// ---------------------------------------------------------------------------
// S9-F03: Video result renders VideoPlayer
// ---------------------------------------------------------------------------

describe('S9-F03: Video mode', () => {
  it('renders VideoPlayer for video result', async () => {
    render(<ContentPane selectedResult={videoResult} />)

    await waitFor(() => {
      expect(screen.getByTestId('video-player')).toBeTruthy()
    })
  })

  it('passes correct videoId to VideoPlayer', async () => {
    render(<ContentPane selectedResult={videoResult} />)

    await waitFor(() => {
      expect(capturedVideoPlayerProps.videoId).toBe('vid-1')
    })
  })
})

// ---------------------------------------------------------------------------
// S9-F04: Document result renders document viewer
// ---------------------------------------------------------------------------

describe('S9-F04: Document mode', () => {
  it('renders document viewer for document result', () => {
    render(<ContentPane selectedResult={documentResult} />)
    expect(screen.getByTestId('document-viewer')).toBeTruthy()
    expect(screen.getByText('Summary.md')).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// S9-F05: Video seeks to timestamp
// ---------------------------------------------------------------------------

describe('S9-F05: Video seeks to timestamp', () => {
  it('passes seekTo prop matching selectedResult.timestamp', async () => {
    render(<ContentPane selectedResult={videoResult} />)

    await waitFor(() => {
      expect(capturedVideoPlayerProps.seekTo).toBe(348.6)
    })
  })
})

// ---------------------------------------------------------------------------
// S9-F06: TranscriptPanel renders alongside video
// ---------------------------------------------------------------------------

describe('S9-F06: Transcript syncs with video', () => {
  it('renders TranscriptPanel alongside VideoPlayer', async () => {
    render(<ContentPane selectedResult={videoResult} />)

    await waitFor(() => {
      expect(screen.getByTestId('transcript-panel')).toBeTruthy()
    })
  })

  it('fetches transcript for the video', async () => {
    render(<ContentPane selectedResult={videoResult} />)

    await waitFor(() => {
      expect(videosApi.getTranscript).toHaveBeenCalledWith('vid-1')
    })
  })
})

// ---------------------------------------------------------------------------
// S9-F07: Download button visible for documents
// ---------------------------------------------------------------------------

describe('S9-F07: Document download button', () => {
  it('shows download button for document results', () => {
    render(<ContentPane selectedResult={documentResult} />)
    expect(screen.getByTestId('document-download')).toBeTruthy()
    expect(screen.getByTestId('document-download').textContent).toBe('Download')
  })
})
