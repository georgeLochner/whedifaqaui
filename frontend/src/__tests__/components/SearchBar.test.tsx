/**
 * SearchBar component tests.
 *
 * S1-F01  test_search_bar_renders
 * S1-F02  test_search_submits_query
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import SearchBar from '../../components/search/SearchBar'

// ---------------------------------------------------------------------------
// S1-F01: SearchBar input field present
// ---------------------------------------------------------------------------

describe('S1-F01: SearchBar renders', () => {
  it('renders the search input field', () => {
    render(<SearchBar onSearch={vi.fn()} />)
    expect(screen.getByTestId('search-input')).toBeTruthy()
  })

  it('renders the search button', () => {
    render(<SearchBar onSearch={vi.fn()} />)
    expect(screen.getByTestId('search-button')).toBeTruthy()
  })

  it('disables the button when input is empty', () => {
    render(<SearchBar onSearch={vi.fn()} />)
    const button = screen.getByTestId('search-button') as HTMLButtonElement
    expect(button.disabled).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// S1-F02: Enter key submits, onSearch called with query text
// ---------------------------------------------------------------------------

describe('S1-F02: SearchBar submits query', () => {
  it('calls onSearch with query when form is submitted', () => {
    const onSearch = vi.fn()
    render(<SearchBar onSearch={onSearch} />)

    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'authentication' } })
    fireEvent.submit(input.closest('form')!)

    expect(onSearch).toHaveBeenCalledWith('authentication')
  })

  it('calls onSearch when Enter key is pressed', () => {
    const onSearch = vi.fn()
    render(<SearchBar onSearch={onSearch} />)

    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'migration' } })
    fireEvent.submit(input.closest('form')!)

    expect(onSearch).toHaveBeenCalledWith('migration')
  })

  it('does not call onSearch when query is empty', () => {
    const onSearch = vi.fn()
    render(<SearchBar onSearch={onSearch} />)

    fireEvent.submit(screen.getByTestId('search-input').closest('form')!)

    expect(onSearch).not.toHaveBeenCalled()
  })
})
