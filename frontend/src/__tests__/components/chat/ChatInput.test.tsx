/**
 * ChatInput component tests.
 *
 * S7-F01  test_chat_input_renders — ChatInput component renders
 * S7-F02  test_chat_message_submit — Message submitted on enter/click
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChatInput from '../../../components/chat/ChatInput'

// ---------------------------------------------------------------------------
// S7-F01: ChatInput component renders
// ---------------------------------------------------------------------------

describe('S7-F01: ChatInput renders', () => {
  it('renders the chat input field', () => {
    render(<ChatInput onSend={vi.fn()} isLoading={false} />)
    expect(screen.getByTestId('chat-input')).toBeTruthy()
  })

  it('renders the send button', () => {
    render(<ChatInput onSend={vi.fn()} isLoading={false} />)
    expect(screen.getByTestId('send-button')).toBeTruthy()
  })

  it('disables input and button when loading', () => {
    render(<ChatInput onSend={vi.fn()} isLoading={true} />)
    const input = screen.getByTestId('chat-input') as HTMLInputElement
    const button = screen.getByTestId('send-button') as HTMLButtonElement
    expect(input.disabled).toBe(true)
    expect(button.disabled).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// S7-F02: Message submitted on enter/click
// ---------------------------------------------------------------------------

describe('S7-F02: ChatInput submits message', () => {
  it('calls onSend with message when form is submitted', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} isLoading={false} />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'What features were added?' } })
    fireEvent.submit(input.closest('form')!)

    expect(onSend).toHaveBeenCalledWith('What features were added?')
  })

  it('calls onSend when send button is clicked', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} isLoading={false} />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByTestId('send-button'))

    expect(onSend).toHaveBeenCalledWith('Hello')
  })

  it('clears input after submission', () => {
    render(<ChatInput onSend={vi.fn()} isLoading={false} />)

    const input = screen.getByTestId('chat-input') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.submit(input.closest('form')!)

    expect(input.value).toBe('')
  })

  it('does not call onSend when input is empty', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} isLoading={false} />)

    fireEvent.submit(screen.getByTestId('chat-input').closest('form')!)

    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not call onSend when loading', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} isLoading={true} />)

    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.submit(input.closest('form')!)

    expect(onSend).not.toHaveBeenCalled()
  })
})
