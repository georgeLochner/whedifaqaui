/**
 * TranscriptPanel component tests.
 *
 * P3-F01  test_transcript_panel_renders - displays segments
 * P3-F02  test_current_segment_highlighted - active segment has 'active' CSS class
 * P3-F03  test_segment_click_seeks - clicking segment calls onSegmentClick
 * P3-F04  test_auto_scroll_to_current - scrollIntoView called when activeSegmentId changes
 * P3-F05  test_speaker_labels_displayed - "SPEAKER_00:" prefix visible
 */

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// jsdom does not implement scrollIntoView
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

import TranscriptPanel from '../../components/video/TranscriptPanel'
import type { TranscriptSegment } from '../../types/transcript'

const mockSegments: TranscriptSegment[] = [
  {
    id: 'seg-1',
    start_time: 0,
    end_time: 10,
    text: 'Hello everyone, welcome to the meeting.',
    speaker: 'SPEAKER_00',
    timestamp_formatted: '0:00',
  },
  {
    id: 'seg-2',
    start_time: 10,
    end_time: 25,
    text: 'Let us discuss the project timeline.',
    speaker: 'SPEAKER_01',
    timestamp_formatted: '0:10',
  },
  {
    id: 'seg-3',
    start_time: 25,
    end_time: 40,
    text: 'The deadline is next Friday.',
    speaker: null,
    timestamp_formatted: '0:25',
  },
]

describe('P3-F01: TranscriptPanel renders', () => {
  it('displays all segments', () => {
    render(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId={null}
        onSegmentClick={() => {}}
      />
    )

    const panel = screen.getByTestId('transcript-panel')
    expect(panel).toBeInTheDocument()

    const segments = screen.getAllByTestId('transcript-segment')
    expect(segments).toHaveLength(3)

    expect(segments[0]).toHaveTextContent('Hello everyone, welcome to the meeting.')
    expect(segments[1]).toHaveTextContent('Let us discuss the project timeline.')
    expect(segments[2]).toHaveTextContent('The deadline is next Friday.')
  })
})

describe('P3-F02: Current segment highlighted', () => {
  it('active segment has "active" CSS class', () => {
    render(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId="seg-2"
        onSegmentClick={() => {}}
      />
    )

    const segments = screen.getAllByTestId('transcript-segment')
    expect(segments[0].className).not.toContain('active')
    expect(segments[1].className).toContain('active')
    expect(segments[2].className).not.toContain('active')
  })
})

describe('P3-F03: Segment click seeks', () => {
  it('clicking a segment calls onSegmentClick with the segment', () => {
    const handleClick = vi.fn()

    render(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId={null}
        onSegmentClick={handleClick}
      />
    )

    const segments = screen.getAllByTestId('transcript-segment')
    fireEvent.click(segments[1])

    expect(handleClick).toHaveBeenCalledOnce()
    expect(handleClick).toHaveBeenCalledWith(mockSegments[1])
  })
})

describe('P3-F04: Auto-scroll to current segment', () => {
  it('calls scrollIntoView when activeSegmentId changes', () => {
    const scrollIntoViewMock = vi.mocked(Element.prototype.scrollIntoView)

    const { rerender } = render(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId={null}
        onSegmentClick={() => {}}
      />
    )

    scrollIntoViewMock.mockClear()

    rerender(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId="seg-2"
        onSegmentClick={() => {}}
      />
    )

    expect(scrollIntoViewMock).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    })
  })
})

describe('P3-F05: Speaker labels displayed', () => {
  it('displays "SPEAKER_00:" prefix via speaker-label testid', () => {
    render(
      <TranscriptPanel
        segments={mockSegments}
        activeSegmentId={null}
        onSegmentClick={() => {}}
      />
    )

    const speakerLabels = screen.getAllByTestId('speaker-label')
    expect(speakerLabels).toHaveLength(2) // seg-1 and seg-2 have speakers, seg-3 does not
    expect(speakerLabels[0]).toHaveTextContent('SPEAKER_00:')
    expect(speakerLabels[1]).toHaveTextContent('SPEAKER_01:')
  })
})
