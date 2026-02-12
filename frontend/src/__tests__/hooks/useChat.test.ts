/**
 * useChat hook tests.
 *
 * S7-F04  test_chat_loading_state — Loading indicator during request
 * S7-F05  test_conversation_id_stored — ID stored in hook state
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '../../hooks/useChat'
import { sendChatMessage } from '../../api/chat'

vi.mock('../../api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

const mockSendChatMessage = vi.mocked(sendChatMessage)

describe('useChat hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useChat())

    expect(result.current.messages).toEqual([])
    expect(result.current.conversationId).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('adds user and AI messages after sendMessage', async () => {
    mockSendChatMessage.mockResolvedValue({
      message: 'AI response text',
      conversation_id: 'conv-123',
      citations: [],
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('Hello')
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('AI response text')
  })

  it('includes citations in AI message', async () => {
    const citations = [
      {
        video_id: 'vid-1',
        video_title: 'Meeting',
        timestamp: 348,
        text: 'permissions filter',
      },
    ]
    mockSendChatMessage.mockResolvedValue({
      message: 'Features include [Meeting @ 5:48]',
      conversation_id: 'conv-123',
      citations,
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('What features?')
    })

    expect(result.current.messages[1].citations).toEqual(citations)
  })
})

// ---------------------------------------------------------------------------
// S7-F04: Loading indicator during request
// ---------------------------------------------------------------------------

describe('S7-F04: Chat loading state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('sets isLoading true during API call and false after', async () => {
    let resolveApi: (value: unknown) => void
    const apiPromise = new Promise((resolve) => {
      resolveApi = resolve
    })
    mockSendChatMessage.mockReturnValue(apiPromise as ReturnType<typeof sendChatMessage>)

    const { result } = renderHook(() => useChat())

    // Start sending - don't await
    let sendPromise: Promise<void>
    act(() => {
      sendPromise = result.current.sendMessage('Test')
    })

    // isLoading should be true while API is in flight
    expect(result.current.isLoading).toBe(true)

    // Resolve the API call
    await act(async () => {
      resolveApi!({
        message: 'Response',
        conversation_id: 'conv-1',
        citations: [],
      })
      await sendPromise!
    })

    expect(result.current.isLoading).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// S7-F05: Conversation ID stored in hook state
// ---------------------------------------------------------------------------

describe('S7-F05: Conversation ID stored', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('stores conversationId from first response', async () => {
    mockSendChatMessage.mockResolvedValue({
      message: 'Response',
      conversation_id: 'conv-abc-123',
      citations: [],
    })

    const { result } = renderHook(() => useChat())

    expect(result.current.conversationId).toBeNull()

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(result.current.conversationId).toBe('conv-abc-123')
  })

  it('passes conversationId on subsequent requests', async () => {
    mockSendChatMessage
      .mockResolvedValueOnce({
        message: 'First response',
        conversation_id: 'conv-xyz',
        citations: [],
      })
      .mockResolvedValueOnce({
        message: 'Second response',
        conversation_id: 'conv-xyz',
        citations: [],
      })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('First')
    })

    await act(async () => {
      await result.current.sendMessage('Second')
    })

    expect(mockSendChatMessage).toHaveBeenCalledTimes(2)
    expect(mockSendChatMessage).toHaveBeenNthCalledWith(1, 'First', null)
    expect(mockSendChatMessage).toHaveBeenNthCalledWith(2, 'Second', 'conv-xyz')
  })
})

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('useChat error handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('sets error on API failure', async () => {
    mockSendChatMessage.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Test')
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.isLoading).toBe(false)
  })

  it('clears error on next send', async () => {
    mockSendChatMessage
      .mockRejectedValueOnce(new Error('Temporary error'))
      .mockResolvedValueOnce({
        message: 'Success',
        conversation_id: 'conv-1',
        citations: [],
      })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Fail')
    })
    expect(result.current.error).toBe('Temporary error')

    await act(async () => {
      await result.current.sendMessage('Succeed')
    })
    expect(result.current.error).toBeNull()
  })
})
