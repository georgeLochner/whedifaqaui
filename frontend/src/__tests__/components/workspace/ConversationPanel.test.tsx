/**
 * ConversationPanel component tests.
 *
 * S7-F04  test_chat_loading_state — Loading indicator shown during request
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ConversationPanel from '../../../components/workspace/ConversationPanel'
import { sendChatMessage } from '../../../api/chat'

vi.mock('../../../api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

const mockSendChatMessage = vi.mocked(sendChatMessage)

describe('ConversationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders conversation-panel container', () => {
    render(<ConversationPanel />)
    expect(screen.getByTestId('conversation-panel')).toBeTruthy()
  })

  it('renders ChatHistory and ChatInput', () => {
    render(<ConversationPanel />)
    expect(screen.getByTestId('chat-history')).toBeTruthy()
    expect(screen.getByTestId('chat-input')).toBeTruthy()
    expect(screen.getByTestId('send-button')).toBeTruthy()
  })

  it('sends message and displays user + AI messages', async () => {
    mockSendChatMessage.mockResolvedValue({
      message: 'AI reply',
      conversation_id: 'conv-1',
      citations: [],
    })

    render(<ConversationPanel />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByTestId('user-message')).toBeTruthy()
    })

    await waitFor(() => {
      expect(screen.getByTestId('ai-message')).toBeTruthy()
    })

    expect(screen.getByTestId('user-message').textContent).toContain('Hello')
    expect(screen.getByTestId('ai-message').textContent).toContain('AI reply')
  })
})

// ---------------------------------------------------------------------------
// S7-F04: Loading indicator during request (component-level)
// ---------------------------------------------------------------------------

describe('S7-F04: ConversationPanel loading state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading indicator while waiting for response', async () => {
    let resolveApi: (value: unknown) => void
    const apiPromise = new Promise((resolve) => {
      resolveApi = resolve
    })
    mockSendChatMessage.mockReturnValue(apiPromise as ReturnType<typeof sendChatMessage>)

    render(<ConversationPanel />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByTestId('chat-loading')).toBeTruthy()
    })

    // Resolve the API
    resolveApi!({
      message: 'Done',
      conversation_id: 'conv-1',
      citations: [],
    })

    await waitFor(() => {
      expect(screen.queryByTestId('chat-loading')).toBeNull()
    })
  })

  it('shows error message on failure', async () => {
    mockSendChatMessage.mockRejectedValue(new Error('Server error'))

    render(<ConversationPanel />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByTestId('chat-error')).toBeTruthy()
    })

    expect(screen.getByTestId('chat-error').textContent).toContain('Server error')
  })
})
