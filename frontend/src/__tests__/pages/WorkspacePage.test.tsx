/**
 * WorkspacePage tests.
 *
 * - Three-panel layout renders with correct data-testid attributes
 * - /workspace route accessible from App router
 * - Navigation shows Workspace link
 */

import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// jsdom does not implement scrollIntoView
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

beforeEach(() => {
  sessionStorage.clear()
})

vi.mock('../../api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

vi.mock('../../api/videos', () => ({
  getTranscript: vi.fn().mockResolvedValue({
    video_id: 'vid-1',
    segments: [],
    count: 0,
  }),
}))

vi.mock('../../components/video/VideoPlayer', () => ({
  default: () => <div data-testid="video-player">VideoPlayer mock</div>,
}))

vi.mock('video.js', () => ({ default: vi.fn() }))
vi.mock('video.js/dist/video-js.css', () => ({}))

import WorkspacePage from '../../pages/WorkspacePage'
import App from '../../App'

function renderPage() {
  return render(
    <MemoryRouter>
      <WorkspacePage />
    </MemoryRouter>
  )
}

describe('WorkspacePage: Three-panel layout', () => {
  it('renders workspace-layout container', () => {
    renderPage()
    expect(screen.getByTestId('workspace-layout')).toBeTruthy()
  })

  it('renders conversation-panel', () => {
    renderPage()
    expect(screen.getByTestId('conversation-panel')).toBeTruthy()
  })

  it('renders results-panel', () => {
    renderPage()
    const panel = screen.getByTestId('results-panel')
    expect(panel).toBeTruthy()
    expect(panel.textContent).toContain('Results')
  })

  it('renders content-pane with empty state', () => {
    renderPage()
    const pane = screen.getByTestId('content-pane')
    expect(pane).toBeTruthy()
    expect(pane.textContent).toContain('Select a result to view content')
  })

  it('uses grid layout with three columns', () => {
    renderPage()
    const layout = screen.getByTestId('workspace-layout')
    expect(layout.className).toContain('grid')
    expect(layout.className).toContain('grid-cols-')
  })
})

describe('WorkspacePage: Routing', () => {
  it('/workspace route renders WorkspacePage', () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByTestId('workspace-layout')).toBeTruthy()
  })
})

describe('WorkspacePage: Navigation', () => {
  it('shows Workspace link in navigation', () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <App />
      </MemoryRouter>
    )
    const navLink = screen.getByTestId('nav-workspace')
    expect(navLink).toBeTruthy()
    expect(navLink.textContent).toBe('Workspace')
  })
})
