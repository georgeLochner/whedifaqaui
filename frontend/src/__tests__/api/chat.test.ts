import { describe, it, expect, vi, beforeEach } from 'vitest'
import { sendChatMessage } from '../../api/chat'
import apiClient from '../../api/client'

vi.mock('../../api/client', () => ({
  default: {
    post: vi.fn(),
  },
}))

const mockPost = vi.mocked(apiClient.post)

describe('sendChatMessage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls POST /chat with message payload', async () => {
    const mockResponse = {
      message: 'AI response',
      conversation_id: 'conv-123',
      citations: [],
    }
    mockPost.mockResolvedValue({ data: mockResponse })

    await sendChatMessage('Hello')

    expect(mockPost).toHaveBeenCalledWith('/chat', { message: 'Hello' })
  })

  it('includes conversation_id when provided', async () => {
    const mockResponse = {
      message: 'Follow-up response',
      conversation_id: 'conv-123',
      citations: [],
    }
    mockPost.mockResolvedValue({ data: mockResponse })

    await sendChatMessage('Follow up', 'conv-123')

    expect(mockPost).toHaveBeenCalledWith('/chat', {
      message: 'Follow up',
      conversation_id: 'conv-123',
    })
  })

  it('omits conversation_id when null', async () => {
    const mockResponse = {
      message: 'Response',
      conversation_id: 'conv-new',
      citations: [],
    }
    mockPost.mockResolvedValue({ data: mockResponse })

    await sendChatMessage('Test', null)

    expect(mockPost).toHaveBeenCalledWith('/chat', { message: 'Test' })
  })

  it('returns ChatResponse with message, conversation_id, and citations', async () => {
    const mockResponse = {
      message: 'Backdrop 1.24 features include...',
      conversation_id: 'conv-456',
      citations: [
        {
          video_id: 'vid-1',
          video_title: 'Backdrop CMS Weekly Meeting',
          timestamp: 348.6,
          text: 'permissions filter',
        },
      ],
    }
    mockPost.mockResolvedValue({ data: mockResponse })

    const result = await sendChatMessage('What features?')

    expect(result).toEqual(mockResponse)
    expect(result.conversation_id).toBe('conv-456')
    expect(result.citations).toHaveLength(1)
    expect(result.citations[0].video_title).toBe('Backdrop CMS Weekly Meeting')
  })
})
