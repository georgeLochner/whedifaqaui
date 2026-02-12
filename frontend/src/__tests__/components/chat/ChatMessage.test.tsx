/**
 * ChatMessage component tests.
 *
 * S7-F07  test_message_with_citations — AI message renders with citations
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChatMessage from '../../../components/chat/ChatMessage'
import type { ChatMessage as ChatMessageType, Citation } from '../../../types/chat'

const userMessage: ChatMessageType = {
  id: 'msg-1',
  role: 'user',
  content: 'What features were added?',
  timestamp: new Date(),
}

const aiMessageWithCitations: ChatMessageType = {
  id: 'msg-2',
  role: 'assistant',
  content:
    'Backdrop 1.24 introduced a permissions filter [Backdrop CMS Weekly Meeting @ 5:48] and a back-to-site button [Backdrop CMS Weekly Meeting @ 7:55].',
  citations: [
    {
      video_id: 'vid-1',
      video_title: 'Backdrop CMS Weekly Meeting',
      timestamp: 348,
      text: 'permissions filter',
    },
    {
      video_id: 'vid-1',
      video_title: 'Backdrop CMS Weekly Meeting',
      timestamp: 475,
      text: 'back-to-site button',
    },
  ],
  timestamp: new Date(),
}

const aiMessageNoCitations: ChatMessageType = {
  id: 'msg-3',
  role: 'assistant',
  content: 'I could not find relevant information about that topic.',
  timestamp: new Date(),
}

describe('ChatMessage', () => {
  it('renders user message with user-message testid', () => {
    render(<ChatMessage message={userMessage} />)
    const el = screen.getByTestId('user-message')
    expect(el.textContent).toContain('What features were added?')
  })

  it('renders AI message with ai-message testid', () => {
    render(<ChatMessage message={aiMessageNoCitations} />)
    const el = screen.getByTestId('ai-message')
    expect(el.textContent).toContain('I could not find relevant information')
  })
})

// ---------------------------------------------------------------------------
// S7-F07: AI message renders with citations
// ---------------------------------------------------------------------------

describe('S7-F07: Message with citations', () => {
  it('renders citation components inline in AI message', () => {
    render(<ChatMessage message={aiMessageWithCitations} />)
    const citations = screen.getAllByTestId('citation')
    expect(citations.length).toBe(2)
  })

  it('citation shows video title and formatted timestamp', () => {
    render(<ChatMessage message={aiMessageWithCitations} />)
    const citations = screen.getAllByTestId('citation')
    expect(citations[0].textContent).toContain('Backdrop CMS Weekly Meeting')
    expect(citations[0].textContent).toContain('5:48')
    expect(citations[1].textContent).toContain('7:55')
  })

  it('clicking citation triggers onCitationClick callback', () => {
    const onCitationClick = vi.fn()
    render(
      <ChatMessage message={aiMessageWithCitations} onCitationClick={onCitationClick} />
    )

    const citations = screen.getAllByTestId('citation')
    fireEvent.click(citations[0])

    expect(onCitationClick).toHaveBeenCalledTimes(1)
    expect(onCitationClick).toHaveBeenCalledWith(
      expect.objectContaining({
        video_title: 'Backdrop CMS Weekly Meeting',
      })
    )
  })

  it('renders surrounding text alongside citations', () => {
    render(<ChatMessage message={aiMessageWithCitations} />)
    const el = screen.getByTestId('ai-message')
    expect(el.textContent).toContain('Backdrop 1.24 introduced a permissions filter')
    expect(el.textContent).toContain('and a back-to-site button')
  })
})
