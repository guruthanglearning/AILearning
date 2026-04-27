import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SessionsList } from './SessionsList'
import * as sessionApi from '../services/sessionApi'

describe('SessionsList', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('shows loading initially', () => {
    vi.spyOn(sessionApi, 'listSessions').mockReturnValue(new Promise(() => {}))
    render(<SessionsList />)
    expect(screen.getByTestId('loading')).toBeInTheDocument()
  })

  it('shows empty message when no sessions', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([])
    render(<SessionsList />)
    await waitFor(() => expect(screen.getByTestId('no-sessions')).toBeInTheDocument())
  })

  it('renders sessions table with data', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([
      { sessionId: 'abc-123', requirement: 'Build API', success: true, artifactCount: 5, totalDuration: '00:01:00', startedAt: new Date().toISOString() }
    ])
    render(<SessionsList />)
    await waitFor(() => expect(screen.getByTestId('sessions-table')).toBeInTheDocument())
    expect(screen.getAllByTestId('session-row')).toHaveLength(1)
  })

  it('shows error when API fails', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockRejectedValue(new Error('Network error'))
    render(<SessionsList />)
    await waitFor(() => expect(screen.getByTestId('sessions-error')).toBeInTheDocument())
  })

  it('shows success badge for successful sessions', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([
      { sessionId: 'abc', requirement: 'Build API', success: true, artifactCount: 3, totalDuration: '00:01:00', startedAt: new Date().toISOString() }
    ])
    render(<SessionsList />)
    await waitFor(() => expect(screen.getByText(/Success/)).toBeInTheDocument())
  })

  it('shows failure badge for failed sessions', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([
      { sessionId: 'abc', requirement: 'Build API', success: false, artifactCount: 0, totalDuration: '00:00:10', startedAt: new Date().toISOString() }
    ])
    render(<SessionsList />)
    await waitFor(() => expect(screen.getByText(/Failed/)).toBeInTheDocument())
  })
})
