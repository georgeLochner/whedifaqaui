/**
 * DocumentCard component tests.
 *
 * S10-F01  test_document_card_renders — Card visible with title
 * S10-F02  test_document_card_shows_preview — First ~100 chars shown
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DocumentCard from '../../../components/documents/DocumentCard'

// ---------------------------------------------------------------------------
// S10-F01: DocumentCard renders with title
// ---------------------------------------------------------------------------

describe('S10-F01: DocumentCard renders', () => {
  it('renders card with title visible', () => {
    render(
      <DocumentCard title="Meeting Summary" preview="This is a summary..." onClick={() => {}} />
    )

    const card = screen.getByTestId('result-item-document')
    expect(card).toBeTruthy()
    expect(card.textContent).toContain('Meeting Summary')
  })

  it('shows document icon', () => {
    render(
      <DocumentCard title="Meeting Summary" preview="This is a summary..." onClick={() => {}} />
    )

    const card = screen.getByTestId('result-item-document')
    expect(card.querySelector('[aria-label="document icon"]')).toBeTruthy()
  })

  it('triggers onClick when clicked', () => {
    const onClick = vi.fn()
    render(
      <DocumentCard title="Meeting Summary" preview="This is a summary..." onClick={onClick} />
    )

    fireEvent.click(screen.getByTestId('result-item-document'))
    expect(onClick).toHaveBeenCalledOnce()
  })
})

// ---------------------------------------------------------------------------
// S10-F02: DocumentCard shows preview
// ---------------------------------------------------------------------------

describe('S10-F02: DocumentCard shows preview', () => {
  it('displays preview text', () => {
    render(
      <DocumentCard title="Summary" preview="This document covers authentication." onClick={() => {}} />
    )

    const preview = screen.getByTestId('document-preview')
    expect(preview.textContent).toContain('This document covers authentication.')
  })

  it('truncates preview text longer than 100 chars', () => {
    const longPreview = 'A'.repeat(150)

    render(
      <DocumentCard title="Summary" preview={longPreview} onClick={() => {}} />
    )

    const preview = screen.getByTestId('document-preview')
    expect(preview.textContent).toBe('A'.repeat(100) + '...')
  })

  it('does not truncate preview text shorter than 100 chars', () => {
    const shortPreview = 'Short preview text'

    render(
      <DocumentCard title="Summary" preview={shortPreview} onClick={() => {}} />
    )

    const preview = screen.getByTestId('document-preview')
    expect(preview.textContent).toBe('Short preview text')
  })
})
