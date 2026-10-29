import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from './App'
import * as pipelineApi from './services/pipelineApi'
import * as sessionApi from './services/sessionApi'

async function* fakeStream(...messages: string[]) {
  for (const m of messages) yield m
}

async function* failingStream(): AsyncGenerator<string> {
  throw new Error('Connection refused')
  yield ''
}

describe('App', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    window.history.pushState(null, '', '/')
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([])
  })

  it('renders pipeline form on load', () => {
    render(<App />)
    expect(screen.getByTestId('pipeline-form')).toBeInTheDocument()
  })

  it('shows progress log after submit', async () => {
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(fakeStream('🤖 PM started', '✅ done'))
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('progress-log')).toBeInTheDocument())
  })

  it('shows new pipeline button after completion', async () => {
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(fakeStream('done'))
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('new-pipeline-btn')).toBeInTheDocument())
  })

  it('loads the session after the stream and shows requirements and artifacts', async () => {
    const sessionId = '706c6714-cb17-45f6-abe1-3f87b4257220'
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(fakeStream(`🆔 Session ${sessionId}`, '✅ done'))
    const getSession = vi.spyOn(sessionApi, 'getSession').mockResolvedValue({
      sessionId,
      requirement: 'Hello World',
      startedAt: '2026-10-28T00:00:00Z',
      success: true,
      artifacts: { SourceCode: 'class Program {}' },
      agentLog: [],
      totalDuration: '00:03:00',
      requirements: [
        { id: 'FR-1', text: 'Print it', kind: 'Code', status: 'Passed', coveredBy: ['Developer'], source: 'Product Manager' }
      ]
    })
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('requirements-section')).toBeInTheDocument())
    expect(getSession).toHaveBeenCalledWith(sessionId)
    expect(screen.getAllByTestId('requirement-row')).toHaveLength(1)
    expect(screen.getAllByTestId('artifact-item')).toHaveLength(1)
  })

  it('still completes when loading the session fails', async () => {
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(
      fakeStream('🆔 Session 706c6714-cb17-45f6-abe1-3f87b4257220', '✅ done'))
    vi.spyOn(sessionApi, 'getSession').mockRejectedValue(new Error('500'))
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('new-pipeline-btn')).toBeInTheDocument())
    expect(screen.queryByTestId('requirements-section')).not.toBeInTheDocument()
  })

  it('shows error message when stream fails', async () => {
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(failingStream())
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('error-message')).toBeInTheDocument())
    expect(screen.getByTestId('error-message')).toHaveTextContent('Connection refused')
  })

  it('resets to form after try again', async () => {
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(failingStream())
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    await waitFor(() => expect(screen.getByTestId('try-again-btn')).toBeInTheDocument())
    fireEvent.click(screen.getByTestId('try-again-btn'))
    expect(screen.getByTestId('pipeline-form')).toBeInTheDocument()
  })

  it('navigates to sessions page', async () => {
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([])
    render(<App />)
    fireEvent.click(screen.getByText('Past Sessions'))
    await waitFor(() => expect(screen.getByTestId('no-sessions')).toBeInTheDocument())
  })

  it('resets to idle when stream is aborted', async () => {
    async function* abortStream(): AsyncGenerator<string> {
      const err = new Error('The user aborted a request.')
      err.name = 'AbortError'
      throw err
      yield ''
    }
    vi.spyOn(pipelineApi, 'streamPipeline').mockReturnValue(abortStream())
    render(<App />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    // AbortError → setState('idle') → form is shown, no error banner
    await waitFor(() => expect(screen.getByTestId('pipeline-form')).toBeInTheDocument())
    expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
  })

  it('opens a session from past sessions and goes back', async () => {
    const sessionId = '68b58a96-3422-4ec9-a870-6a392930e392'
    vi.spyOn(sessionApi, 'listSessions').mockResolvedValue([
      { sessionId, requirement: 'Hello World', success: true, artifactCount: 9, totalDuration: '00:03:48', startedAt: '2026-10-28T22:53:25Z' }
    ])
    vi.spyOn(sessionApi, 'getSession').mockResolvedValue({
      sessionId, requirement: 'Hello World', startedAt: '2026-10-28T22:53:25Z', success: true,
      artifacts: {}, agentLog: [], totalDuration: '00:03:48',
      requirements: [{ id: 'FR-1', text: 'Print it', kind: 'Code', status: 'Passed', coveredBy: [], source: 'Product Manager' }]
    })
    render(<App />)
    fireEvent.click(screen.getByText('Past Sessions'))
    await waitFor(() => expect(screen.getByTestId('session-link')).toBeInTheDocument())
    fireEvent.click(screen.getByTestId('session-link'))
    await waitFor(() => expect(screen.getByTestId('requirements-section')).toBeInTheDocument())
    expect(window.location.pathname).toBe(`/sessions/${sessionId}`)
    fireEvent.click(screen.getByTestId('back-btn'))
    await waitFor(() => expect(screen.getByTestId('sessions-table')).toBeInTheDocument())
    expect(window.location.pathname).toBe('/sessions')
  })

  it('opens the session named in the URL on load', async () => {
    const sessionId = '68b58a96-3422-4ec9-a870-6a392930e392'
    window.history.pushState(null, '', `/sessions/${sessionId}`)
    const getSession = vi.spyOn(sessionApi, 'getSession').mockResolvedValue(null)
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('session-error')).toBeInTheDocument())
    expect(getSession).toHaveBeenCalledWith(sessionId)
  })

  it('follows the browser back button', async () => {
    render(<App />)
    fireEvent.click(screen.getByText('Past Sessions'))
    await waitFor(() => expect(screen.getByTestId('no-sessions')).toBeInTheDocument())
    window.history.pushState(null, '', '/')
    window.dispatchEvent(new PopStateEvent('popstate'))
    await waitFor(() => expect(screen.getByTestId('pipeline-form')).toBeInTheDocument())
  })
})
