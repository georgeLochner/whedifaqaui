import { useState, useRef, type FormEvent } from 'react'

export interface UploadFormData {
  file: File
  title: string
  recording_date: string
  participants: string
  context_notes: string
}

interface UploadFormProps {
  onSubmit: (data: UploadFormData) => void
  disabled?: boolean
}

export default function UploadForm({ onSubmit, disabled }: UploadFormProps) {
  const [title, setTitle] = useState('')
  const [recordingDate, setRecordingDate] = useState('')
  const [participants, setParticipants] = useState('')
  const [contextNotes, setContextNotes] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const fileInputRef = useRef<HTMLInputElement>(null)

  function validate(): boolean {
    const newErrors: Record<string, string> = {}
    if (!title.trim()) newErrors.title = 'Title is required'
    if (!recordingDate) newErrors.recording_date = 'Recording date is required'
    if (!file) {
      newErrors.file = 'File is required'
    } else if (!file.name.toLowerCase().endsWith('.mkv')) {
      newErrors.file = 'Only .mkv files are accepted'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate() || !file) return
    onSubmit({
      file,
      title: title.trim(),
      recording_date: recordingDate,
      participants,
      context_notes: contextNotes,
    })
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    if (selected && !selected.name.toLowerCase().endsWith('.mkv')) {
      setErrors((prev) => ({ ...prev, file: 'Only .mkv files are accepted' }))
    } else {
      setErrors((prev) => {
        const { file: _, ...rest } = prev
        return rest
      })
    }
  }

  return (
    <form
      data-testid="upload-form"
      onSubmit={handleSubmit}
      className="space-y-6 max-w-xl"
    >
      {/* File input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Video file (.mkv)
        </label>
        <input
          data-testid="file-input"
          ref={fileInputRef}
          type="file"
          accept=".mkv"
          onChange={handleFileChange}
          disabled={disabled}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {errors.file && (
          <p className="mt-1 text-sm text-red-600">{errors.file}</p>
        )}
      </div>

      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          data-testid="title-input"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={disabled}
          placeholder="e.g. Sprint Review 2024-03-01"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-600">{errors.title}</p>
        )}
      </div>

      {/* Recording date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Recording date
        </label>
        <input
          data-testid="date-input"
          type="date"
          value={recordingDate}
          onChange={(e) => setRecordingDate(e.target.value)}
          disabled={disabled}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        />
        {errors.recording_date && (
          <p className="mt-1 text-sm text-red-600">{errors.recording_date}</p>
        )}
      </div>

      {/* Participants */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Participants (comma-separated, optional)
        </label>
        <input
          data-testid="participants-input"
          type="text"
          value={participants}
          onChange={(e) => setParticipants(e.target.value)}
          disabled={disabled}
          placeholder="e.g. Alice, Bob, Charlie"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        />
      </div>

      {/* Context notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Context notes (optional)
        </label>
        <textarea
          data-testid="notes-input"
          value={contextNotes}
          onChange={(e) => setContextNotes(e.target.value)}
          disabled={disabled}
          rows={3}
          placeholder="Any additional context about the meeting..."
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        />
      </div>

      {/* Submit */}
      <button
        data-testid="submit-btn"
        type="submit"
        disabled={disabled}
        className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Upload
      </button>
    </form>
  )
}
