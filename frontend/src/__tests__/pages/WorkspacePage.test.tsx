/**
 * WorkspacePage tests.
 *
 * - Three-panel layout renders with correct data-testid attributes
 * - /workspace route accessible from App router
 * - Navigation shows Workspace link
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../../api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

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

  it('renders results-panel placeholder', () => {
    renderPage()
    const panel = screen.getByTestId('results-panel')
    expect(panel).toBeTruthy()
    expect(panel.textContent).toContain('Results')
  })

  it('renders content-pane placeholder', () => {
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
