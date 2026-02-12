/**
 * Upload form and upload progress tests.
 *
 * V1-F01  test_upload_form_renders
 * V1-F02  test_upload_form_validation
 * V1-F03  test_file_type_restriction
 * V1-F04  test_upload_progress_display
 * V4-F01  test_date_field_required_in_upload
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import UploadForm from '../../components/upload/UploadForm'
import UploadProgress from '../../components/upload/UploadProgress'

// ---------------------------------------------------------------------------
// V1-F01: UploadForm renders all expected fields
// ---------------------------------------------------------------------------

describe('V1-F01: UploadForm renders', () => {
  it('shows all required fields', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    expect(screen.getByTestId('upload-form')).toBeInTheDocument()
    expect(screen.getByTestId('file-input')).toBeInTheDocument()
    expect(screen.getByTestId('title-input')).toBeInTheDocument()
    expect(screen.getByTestId('date-input')).toBeInTheDocument()
    expect(screen.getByTestId('participants-input')).toBeInTheDocument()
    expect(screen.getByTestId('notes-input')).toBeInTheDocument()
    expect(screen.getByTestId('submit-btn')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// V1-F02: Client-side validation errors
// ---------------------------------------------------------------------------

describe('V1-F02: UploadForm validation', () => {
  it('shows error when title is missing', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    fireEvent.click(screen.getByTestId('submit-btn'))

    expect(screen.getByText('Title is required')).toBeInTheDocument()
  })

  it('shows error when file is missing', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    // Fill title and date but not file
    fireEvent.change(screen.getByTestId('title-input'), {
      target: { value: 'Sprint Review' },
    })
    fireEvent.change(screen.getByTestId('date-input'), {
      target: { value: '2024-03-01' },
    })
    fireEvent.click(screen.getByTestId('submit-btn'))

    expect(screen.getByText('File is required')).toBeInTheDocument()
  })

  it('does not call onSubmit when validation fails', () => {
    const onSubmit = vi.fn()
    render(<UploadForm onSubmit={onSubmit} />)

    fireEvent.click(screen.getByTestId('submit-btn'))

    expect(onSubmit).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// V1-F03: File input restricted to .mkv
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// V4-F01: Recording date field is required
// ---------------------------------------------------------------------------

describe('V4-F01: Date field required in upload', () => {
  it('shows validation error when recording date is empty', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    // Fill title but leave date empty
    fireEvent.change(screen.getByTestId('title-input'), {
      target: { value: 'Sprint Review' },
    })
    fireEvent.click(screen.getByTestId('submit-btn'))

    expect(screen.getByText('Recording date is required')).toBeInTheDocument()
  })

  it('does not show date error when date is provided', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    fireEvent.change(screen.getByTestId('title-input'), {
      target: { value: 'Sprint Review' },
    })
    fireEvent.change(screen.getByTestId('date-input'), {
      target: { value: '2023-01-05' },
    })
    fireEvent.click(screen.getByTestId('submit-btn'))

    expect(screen.queryByText('Recording date is required')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// V1-F03: File input restricted to .mkv
// ---------------------------------------------------------------------------

describe('V1-F03: File type restriction', () => {
  it('file input has accept=".mkv" attribute', () => {
    render(<UploadForm onSubmit={vi.fn()} />)

    const fileInput = screen.getByTestId('file-input')
    expect(fileInput).toHaveAttribute('accept', '.mkv')
  })
})

// ---------------------------------------------------------------------------
// V1-F04: Upload progress display
// ---------------------------------------------------------------------------

describe('V1-F04: UploadProgress display', () => {
  it('renders progress bar when uploading', () => {
    render(<UploadProgress progress={45} isUploading={true} />)

    const bar = screen.getByTestId('progress-bar')
    expect(bar).toBeInTheDocument()
    expect(screen.getByText('45%')).toBeInTheDocument()
  })

  it('does not render when not uploading', () => {
    render(<UploadProgress progress={0} isUploading={false} />)

    expect(screen.queryByTestId('progress-bar')).not.toBeInTheDocument()
  })

  it('updates displayed percentage', () => {
    const { rerender } = render(
      <UploadProgress progress={10} isUploading={true} />
    )
    expect(screen.getByText('10%')).toBeInTheDocument()

    rerender(<UploadProgress progress={75} isUploading={true} />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })
})
