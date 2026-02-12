/**
 * ChatHistory component tests.
 *
 * S7-F03  test_chat_history_displays — ChatHistory shows messages
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatHistory from '../../../components/chat/ChatHistory'
import type { ChatMessage } from '../../../types/chat'

const messages: ChatMessage[] = [
  {
    id: 'msg-1',
    role: 'user',
    content: 'What features were added to Backdrop 1.24?',
    timestamp: new Date(),
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: 'Backdrop 1.24 introduced a permissions filter and role descriptions.',
    timestamp: new Date(),
  },
  {
    id: 'msg-3',
    role: 'user',
    content: 'Who contributed the back-to-site button?',
    timestamp: new Date(),
  },
]

// ---------------------------------------------------------------------------
// S7-F03: ChatHistory shows user and AI messages
// ---------------------------------------------------------------------------

describe('S7-F03: ChatHistory displays messages', () => {
  it('renders the chat-history container', () => {
    render(<ChatHistory messages={[]} />)
    expect(screen.getByTestId('chat-history')).toBeTruthy()
  })

  it('renders user messages', () => {
    render(<ChatHistory messages={messages} />)
    const userMessages = screen.getAllByTestId('user-message')
    expect(userMessages.length).toBe(2)
  })

  it('renders AI messages', () => {
    render(<ChatHistory messages={messages} />)
    const aiMessages = screen.getAllByTestId('ai-message')
    expect(aiMessages.length).toBe(1)
  })

  it('displays message content', () => {
    render(<ChatHistory messages={messages} />)
    const container = screen.getByTestId('chat-history')
    expect(container.textContent).toContain('What features were added to Backdrop 1.24?')
    expect(container.textContent).toContain('permissions filter and role descriptions')
    expect(container.textContent).toContain('Who contributed the back-to-site button?')
  })

  it('renders empty state with no messages', () => {
    render(<ChatHistory messages={[]} />)
    const container = screen.getByTestId('chat-history')
    expect(container.querySelectorAll('[data-testid="user-message"]').length).toBe(0)
    expect(container.querySelectorAll('[data-testid="ai-message"]').length).toBe(0)
  })

  it('passes onCitationClick to messages', () => {
    const onCitationClick = vi.fn()
    const messagesWithCitation: ChatMessage[] = [
      {
        id: 'msg-1',
        role: 'assistant',
        content: 'Check this [Meeting @ 5:48].',
        citations: [
          {
            video_id: 'v1',
            video_title: 'Meeting',
            timestamp: 348,
            text: 'test',
          },
        ],
        timestamp: new Date(),
      },
    ]

    render(
      <ChatHistory messages={messagesWithCitation} onCitationClick={onCitationClick} />
    )
    expect(screen.getByTestId('citation')).toBeTruthy()
  })
})
