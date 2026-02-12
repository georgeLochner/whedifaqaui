/**
 * DocumentViewer component tests.
 *
 * S10-F03  test_document_viewer_renders — Markdown rendered as HTML
 * S10-F04  test_download_button_triggers_fetch — Download button click calls onDownload
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DocumentViewer from '../../../components/documents/DocumentViewer'
import type { DocumentDetail } from '../../../types/document'

const sampleDocument: DocumentDetail = {
  id: 'doc-123',
  title: 'Authentication Discussion Summary',
  content: '# Summary\n\nThis document covers the **authentication** discussion.\n\n- OAuth2 flow\n- JWT tokens',
  source_video_ids: ['vid-1'],
  created_at: '2026-02-12T10:00:00Z',
}

// ---------------------------------------------------------------------------
// S10-F03: DocumentViewer renders markdown as HTML
// ---------------------------------------------------------------------------

describe('S10-F03: DocumentViewer renders', () => {
  it('renders document-viewer container', () => {
    render(<DocumentViewer document={sampleDocument} onDownload={() => {}} />)
    expect(screen.getByTestId('document-viewer')).toBeTruthy()
  })

  it('displays document title', () => {
    render(<DocumentViewer document={sampleDocument} onDownload={() => {}} />)
    expect(screen.getByText('Authentication Discussion Summary')).toBeTruthy()
  })

  it('renders markdown as HTML', () => {
    render(<DocumentViewer document={sampleDocument} onDownload={() => {}} />)

    const content = screen.getByTestId('document-content')
    expect(content.innerHTML).toContain('<h1>')
    expect(content.innerHTML).toContain('<strong>')
    expect(content.innerHTML).toContain('<li>')
  })

  it('renders bold text from markdown', () => {
    render(<DocumentViewer document={sampleDocument} onDownload={() => {}} />)

    const content = screen.getByTestId('document-content')
    const strong = content.querySelector('strong')
    expect(strong).toBeTruthy()
    expect(strong!.textContent).toBe('authentication')
  })
})

// ---------------------------------------------------------------------------
// S10-F04: Download button triggers callback
// ---------------------------------------------------------------------------

describe('S10-F04: Download button triggers fetch', () => {
  it('renders download button', () => {
    render(<DocumentViewer document={sampleDocument} onDownload={() => {}} />)
    expect(screen.getByTestId('document-download')).toBeTruthy()
    expect(screen.getByTestId('document-download').textContent).toBe('Download')
  })

  it('calls onDownload when download button is clicked', () => {
    const onDownload = vi.fn()
    render(<DocumentViewer document={sampleDocument} onDownload={onDownload} />)

    fireEvent.click(screen.getByTestId('document-download'))
    expect(onDownload).toHaveBeenCalledOnce()
  })
})
