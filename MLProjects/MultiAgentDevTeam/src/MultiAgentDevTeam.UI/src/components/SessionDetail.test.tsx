import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { SessionDetail } from './SessionDetail'
import * as sessionApi from '../services/sessionApi'
import type { SessionRecord } from '../types/api'

const SESSION_ID = '68b58a96-3422-4ec9-a870-6a392930e392'

function record(overrides: Partial<SessionRecord> = {}): SessionRecord {
  return {
    sessionId: SESSION_ID,
    requirement: 'Hello World in C#',
    startedAt: '2026-10-28T22:53:25Z',
    success: true,
    artifacts: { SourceCode: 'class Program {}', VerificationReport: '| id |' },
    agentLog: ['🤖 PM started', '✅ All requirements met'],
    totalDuration: '00:03:48',
    requirements: [
      { id: 'FR-1', text: 'Print Hello, World!', kind: 'Code', status: 'Passed', coveredBy: ['Software Developer'], source: 'Product Manager' },
      { id: 'FR-3', text: 'Run the app', kind: 'Action', status: 'Manual', coveredBy: [], source: 'Product Manager' }
    ],
    ...overrides
  }
}

describe('SessionDetail', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('shows loading initially', () => {
    vi.spyOn(sessionApi, 'getSession').mockReturnValue(new Promise(() => {}))
    render(<SessionDetail sessionId={SESSION_ID} onBack={() => {}} />)
    expect(screen.getByTestId('loading')).toBeInTheDocument()
  })

  it('shows the checklist, artifacts and agent log of the session', async () => {
    const getSession = vi.spyOn(sessionApi, 'getSession').mockResolvedValue(record())
    render(<SessionDetail sessionId={SESSION_ID} onBack={() => {}} />)
    await waitFor(() => expect(screen.getByTestId('session-detail')).toBeInTheDocument())
    expect(getSession).toHaveBeenCalledWith(SESSION_ID)
    expect(screen.getByText('Hello World in C#')).toBeInTheDocument()
    expect(screen.getAllByTestId('requirement-row')).toHaveLength(2)
    expect(screen.getByTestId('requirements-summary')).toHaveTextContent('1 passed, 1 manual')
    expect(screen.getAllByTestId('artifact-item')).toHaveLength(2)
    expect(screen.getAllByTestId('log-entry')).toHaveLength(2)
  })

  it('shows no checklist for sessions saved before requirement tracking', async () => {
    vi.spyOn(sessionApi, 'getSession').mockResolvedValue(record({ requirements: undefined, agentLog: [] }))
    render(<SessionDetail sessionId={SESSION_ID} onBack={() => {}} />)
    await waitFor(() => expect(screen.getByTestId('session-detail')).toBeInTheDocument())
    expect(screen.queryByTestId('requirements-section')).not.toBeInTheDocument()
    expect(screen.queryByTestId('progress-log')).not.toBeInTheDocument()
  })

  it('shows the failure badge and error message of a failed session', async () => {
    vi.spyOn(sessionApi, 'getSession').mockResolvedValue(record({ success: false, errorMessage: 'Developer timed out' }))
    render(<SessionDetail sessionId={SESSION_ID} onBack={() => {}} />)
    await waitFor(() => expect(screen.getByText(/Failed/)).toBeInTheDocument())
    expect(screen.getByText('Developer timed out')).toBeInTheDocument()
  })

  it('shows not found when the session does not exist', async () => {
    vi.spyOn(sessionApi, 'getSession').mockResolvedValue(null)
    render(<SessionDetail sessionId={SESSION_ID} onBack={() => {}} />)
    await waitFor(() => expect(screen.getByTestId('session-error')).toHaveTextContent('was not found'))
  })

  it('shows the error and a back button when the API fails', async () => {
    vi.spyOn(sessionApi, 'getSession').mockRejectedValue(new Error('Failed to get session: 500'))
    const onBack = vi.fn()
    render(<SessionDetail sessionId={SESSION_ID} onBack={onBack} />)
    await waitFor(() => expect(screen.getByTestId('session-error')).toHaveTextContent('500'))
    fireEvent.click(screen.getByTestId('back-btn'))
    expect(onBack).toHaveBeenCalled()
  })

  it('ignores a late response for a session the user already left', async () => {
    let resolveFirst: (s: SessionRecord) => void = () => {}
    vi.spyOn(sessionApi, 'getSession')
      .mockReturnValueOnce(new Promise(r => { resolveFirst = r }))
      .mockResolvedValueOnce(record({ sessionId: 'second', requirement: 'Second session' }))
    const { rerender } = render(<SessionDetail sessionId="first" onBack={() => {}} />)
    rerender(<SessionDetail sessionId="second" onBack={() => {}} />)
    await waitFor(() => expect(screen.getByText('Second session')).toBeInTheDocument())

    resolveFirst(record({ sessionId: 'first', requirement: 'First session' }))
    await new Promise(r => setTimeout(r, 0))

    expect(screen.getByText('Second session')).toBeInTheDocument()
    expect(screen.queryByText('First session')).not.toBeInTheDocument()
  })
})
