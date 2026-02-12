/**
 * Citation component tests.
 *
 * S7-F06  test_citation_click_handler — Citation component is clickable
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Citation from '../../../components/chat/Citation'
import type { Citation as CitationType } from '../../../types/chat'

const sampleCitation: CitationType = {
  video_id: 'vid-1',
  video_title: 'Backdrop CMS Weekly Meeting',
  timestamp: 348,
  text: 'permissions filter',
}

// ---------------------------------------------------------------------------
// S7-F06: Citation component is clickable
// ---------------------------------------------------------------------------

describe('S7-F06: Citation click handler', () => {
  it('renders citation with video title and formatted timestamp', () => {
    render(<Citation citation={sampleCitation} onClick={vi.fn()} />)
    const el = screen.getByTestId('citation')
    expect(el.textContent).toContain('Backdrop CMS Weekly Meeting')
    expect(el.textContent).toContain('5:48')
  })

  it('calls onClick with citation data when clicked', () => {
    const onClick = vi.fn()
    render(<Citation citation={sampleCitation} onClick={onClick} />)

    fireEvent.click(screen.getByTestId('citation'))

    expect(onClick).toHaveBeenCalledTimes(1)
    expect(onClick).toHaveBeenCalledWith(sampleCitation)
  })
})
